#!/usr/bin/env python3
"""DataUpdateCoordinator for offdelay."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_ON
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_state_change_event,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    IntegrationBlueprintApiClientAuthenticationError,
    IntegrationBlueprintApiClientError,
)
from .const import LOGGER

if TYPE_CHECKING:
    from homeassistant.core import Event, HomeAssistant

    from .data import OffdelayIntegrationConfigEntry


class OffdelayDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching API data, weather, and home status."""

    config_entry: OffdelayIntegrationConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: OffdelayIntegrationConfigEntry
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass, LOGGER, name="Offdelay Coordinator", update_interval=None
        )

        self.config_entry = config_entry

        # Stored state
        self.data = {
            "home_status": "Home",
            "vacation_mode": False,
            "guest_mode": False,
        }

        # For detecting "coming back from holiday"
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
        home = self._update_home_data()
        self.async_set_updated_data({**self.data, **home})

    async def _async_update_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {}

        api = await self._update_api_data()
        data.update(api)

        weather = await self._update_weather_data()
        data.update(weather)

        home = self._update_home_data()
        data.update(home)

        return data

    async def _update_api_data(self) -> dict[str, Any]:
        """Fetch fresh data from the backend API."""
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
        """Get weather forecast data and compute values."""
        # Determine which weather entity to use
        if self.hass.states.get("weather.forecast_home"):
            weather_entity = "weather.forecast_home"
        elif self.hass.states.get("weather.home"):
            weather_entity = "weather.home"
        else:
            msg = "No weather entity found (weather.home or weather.forecast_home)"
            raise UpdateFailed(msg)

        try:
            # --- Hourly forecast ---
            hourly_response = await self.hass.services.async_call(
                "weather",
                "get_forecasts",
                {"entity_id": weather_entity, "type": "hourly"},
                blocking=True,
                return_response=True,
            )

            hourly_data: dict[str, Any] = {}
            if isinstance(hourly_response, dict):
                entity_data = hourly_response.get(weather_entity)
                if isinstance(entity_data, dict):
                    hourly_data = entity_data

            hourly_forecast = []
            if "forecast" in hourly_data and isinstance(hourly_data["forecast"], list):
                hourly_forecast = [
                    f for f in hourly_data["forecast"] if isinstance(f, dict)
                ]

            # Extract temperatures safely
            temperatures: list[float] = [
                t["temperature"]
                for t in hourly_forecast
                if "temperature" in t and isinstance(t["temperature"], (int, float))
            ]
            max_temp = max(temperatures) if temperatures else 17.0

            # --- Daily forecast ---
            daily_response = await self.hass.services.async_call(
                "weather",
                "get_forecasts",
                {"entity_id": weather_entity, "type": "daily"},
                blocking=True,
                return_response=True,
            )

            daily_data: dict[str, Any] = {}
            if isinstance(daily_response, dict):
                entity_data = daily_response.get(weather_entity)
                if isinstance(entity_data, dict):
                    daily_data = entity_data

            daily_forecast: list[dict[str, Any]] = []
            if "forecast" in daily_data and isinstance(daily_data["forecast"], list):
                daily_forecast = [
                    f for f in daily_data["forecast"] if isinstance(f, dict)
                ]

            # Map weather conditions to rank
            rank_map = {"sunny": 4, "partlycloudy": 3, "cloudy": 2, "rainy": 1}

            today_condition = (
                daily_forecast[0].get("condition") if len(daily_forecast) > 0 else None
            )
            tomorrow_condition = (
                daily_forecast[1].get("condition") if len(daily_forecast) > 1 else None
            )

            today_rank = rank_map.get(today_condition, 0) if today_condition else 0
            tomorrow_rank = (
                rank_map.get(tomorrow_condition, 0) if tomorrow_condition else 0
            )

        except Exception as err:
            msg = f"Error fetching weather data: {err}"
            raise UpdateFailed(msg) from err

        return {
            "weather_max_temp_today": max_temp,
            "weather_condition_rank_today": today_rank,
            "weather_condition_rank_tomorrow": tomorrow_rank,
            "weather_condition_today": today_condition,
            "weather_condition_tomorrow": tomorrow_condition,
        }

    def _update_home_data(self) -> dict[str, Any]:
        """Compute home_status and vacation flag."""

        def num(entity_id: str) -> float:
            state = self.hass.states.get(entity_id)
            try:
                return float(state.state) if state else 0.0
            except (ValueError, TypeError):
                return 0.0

        home = num("zone.home")
        near = num("zone.near_home")

        vacation_entity = self.hass.states.get("switch.offdelay_vacation_mode")
        vacation = self.data.get("vacation_mode")

        # Auto-clear vacation if coming back from 0 → >0
        if (
            vacation_entity is not None
            and vacation_entity.state == STATE_ON
            and self._prev_home == 0.0
            and self._prev_near == 0.0
            and (home > 0 or near > 0)
        ):
            LOGGER.info("People returned from vacation — clearing vacation mode")
            vacation = False

        # Compute status
        if vacation:
            status = "Vacation"
        elif home > 0:
            status = "Home"
        elif near > 0:
            status = "NearHome"
        else:
            status = "Away"

        # Save previous values for next run
        self._prev_home = home
        self._prev_near = near

        return {
            "home_status": status,
            "vacation_mode": vacation,
            "guest_mode": self.data.get("guest_mode", False),
        }

    async def async_set_home_data(self, key: str, value: Any) -> None:
        """Set a key-value pair in the coordinator's data."""
        self.data[key] = value
        home = self._update_home_data()
        self.data.update(home)
        self.async_set_updated_data(self.data)
