"""DataUpdateCoordinator for offdelay."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_state_change_event,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.loader import async_get_loaded_integration

from .api import (
    IntegrationBlueprintApiClient,
    IntegrationBlueprintApiClientAuthenticationError,
    IntegrationBlueprintApiClientError,
)
from .blueprint import async_setup_blueprints, async_unload_blueprints
from .const import DOMAIN, LOGGER, PLATFORMS
from .data import OffdelayConfigEntry, OffdelayData

if TYPE_CHECKING:
    from homeassistant.core import Event


class OffdelayDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching API data, weather, and home status."""

    config_entry: OffdelayConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: OffdelayConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass, LOGGER, name="Offdelay Coordinator", update_interval=None
        )

        self.config_entry = config_entry

        self.data: dict[str, Any] = {
            "home_status": "Home",
            "vacation_mode": False,
            "guest_mode": False,
        }

        self._prev_home = 0.0
        self._prev_near = 0.0

        async_track_state_change_event(
            self.hass,
            ["zone.home", "zone.near_home", "switch.vacation_mode"],
            self._async_zone_or_vacation_changed,
        )

    async def _async_zone_or_vacation_changed(
        self, _event: Event[EventStateChangedData]
    ) -> None:
        """React to zone/vacation state changes."""
        home = self._update_home_data()
        self.async_set_updated_data({**self.data, **home})

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all coordinator data."""
        data: dict[str, Any] = {}

        api = await self._update_api_data()
        weather = await self._update_weather_data()
        home = self._update_home_data()

        for source in (api, weather, home):
            if source:
                data.update(source)

        return data

    async def _update_api_data(self) -> dict[str, Any]:
        """Fetch fresh data from the backend API.

        Returns:
            dict[str, Any]: The data from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication fails.
            UpdateFailed: If the update fails.

        """
        try:
            return await self.config_entry.runtime_data.client.async_get_data()

        except IntegrationBlueprintApiClientAuthenticationError as exception:
            LOGGER.warning("Authentication error - %s", exception)
            raise ConfigEntryAuthFailed(
                translation_domain="offdelay",
                translation_key="authentication_failed",
            ) from exception

        except IntegrationBlueprintApiClientError as exception:
            LOGGER.exception("Error communicating with API")
            raise UpdateFailed(
                translation_domain="offdelay",
                translation_key="update_failed",
            ) from exception

    async def _update_weather_data(self) -> dict[str, Any]:
        """Get weather forecast data and compute values.

        Returns:
            dict[str, Any]: The weather data.

        Raises:
            UpdateFailed: If fetching weather data fails.

        """
        # Determine weather entity
        weather_entity: str | None = None
        if self.hass.states.get("weather.forecast_home"):
            weather_entity = "weather.forecast_home"
        elif self.hass.states.get("weather.home"):
            weather_entity = "weather.home"

        if weather_entity is None:
            raise UpdateFailed("No weather entity found")

        # Fetch hourly forecast
        hourly_response: dict[str, Any] | None = await self.hass.services.async_call(
            "weather",
            "get_forecasts",
            {"entity_id": weather_entity, "type": "hourly"},
            blocking=True,
            return_response=True,
        )

        hourly_data: dict[str, Any] = (
            hourly_response.get(weather_entity, {}) if hourly_response else {}
        )
        hourly_forecast: list[dict[str, Any]] = hourly_data.get("forecast", [])

        temperatures: list[float] = [
            t["temperature"]
            for t in hourly_forecast
            if isinstance(t.get("temperature"), (int, float))
        ]
        max_temp: float = max(temperatures) if temperatures else 17.0

        # Fetch daily forecast
        daily_response: dict[str, Any] | None = await self.hass.services.async_call(
            "weather",
            "get_forecasts",
            {"entity_id": weather_entity, "type": "daily"},
            blocking=True,
            return_response=True,
        )

        daily_data: dict[str, Any] = (
            daily_response.get(weather_entity, {}) if daily_response else {}
        )
        daily_forecast: list[dict[str, Any]] = daily_data.get("forecast", [])

        # Rank map for conditions
        rank_map: dict[str, int] = {
            "sunny": 4,
            "partlycloudy": 3,
            "cloudy": 2,
            "rainy": 1,
        }

        # Get today's and tomorrow's conditions
        today_condition: str | None = (
            daily_forecast[0].get("condition") if len(daily_forecast) > 0 else None
        )
        tomorrow_condition: str | None = (
            daily_forecast[1].get("condition") if len(daily_forecast) > 1 else None
        )

        today_rank: int = rank_map.get(today_condition or "", 0)
        tomorrow_rank: int = rank_map.get(tomorrow_condition or "", 0)

        return {
            "max_temp": max_temp,
            "today_condition": today_condition,
            "tomorrow_condition": tomorrow_condition,
            "today_rank": today_rank,
            "tomorrow_rank": tomorrow_rank,
        }

    def _update_home_data(self) -> dict[str, Any]:
        """Compute home status and flags.

        Returns:
            dict[str, Any]: Home-related state data.

        """

        def num(entity_id: str) -> float:
            state = self.hass.states.get(entity_id)
            try:
                return float(state.state) if state else 0.0
            except (ValueError, TypeError):
                return 0.0

        home = num("zone.home")
        near = num("zone.near_home")

        vacation_entity = self.hass.states.get("switch.offdelay_vacation_mode")
        vacation = self.data.get("vacation_mode", False)

        is_vacation_on = vacation_entity and vacation_entity.state == STATE_ON
        is_coming_back = (
            self._prev_home == 0.0 and self._prev_near == 0.0 and (home > 0 or near > 0)
        )

        if is_vacation_on and is_coming_back:
            LOGGER.info("People returned from vacation — clearing vacation mode")
            vacation = False

        if vacation:
            status = "Vacation"
        elif home > 0:
            status = "Home"
        elif near > 0:
            status = "NearHome"
        else:
            status = "Away"

        self._prev_home = home
        self._prev_near = near

        return {
            "home_status": status,
            "vacation_mode": vacation,
            "guest_mode": self.data.get("guest_mode", False),
        }

    async def async_set_home_data(self, key: str, *, value: bool) -> None:
        """Set a key-value pair in the coordinator's data."""
        self.data[key] = value
        self.data.update(self._update_home_data())
        self.async_set_updated_data(self.data)


async def async_setup_entry(hass: HomeAssistant, entry: OffdelayConfigEntry) -> bool:
    """Set up this integration using UI.

    Returns:
        bool: True if setup was successful.

    """
    coordinator = OffdelayDataUpdateCoordinator(hass, entry)
    coordinator.update_interval = timedelta(hours=1)

    entry.runtime_data = OffdelayData(
        client=IntegrationBlueprintApiClient(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    await coordinator.async_config_entry_first_refresh()
    await async_setup_blueprints(hass, DOMAIN)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: OffdelayConfigEntry) -> bool:
    """Handle removal of an entry.

    Returns:
        bool: True if unload was successful.

    """
    await async_unload_blueprints(hass, DOMAIN)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: OffdelayConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
