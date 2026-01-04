#!/usr/bin/env python3
"""
DataUpdateCoordinator for offdelay_integration.

Learn more about DataUpdateCoordinator:
https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    IntegrationBlueprintApiClientAuthenticationError,
    IntegrationBlueprintApiClientError,
)
from .const import LOGGER

if TYPE_CHECKING:
    from .data import IntegrationBlueprintConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class BlueprintDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: IntegrationBlueprintConfigEntry

    async def _async_update_data(self) -> Any:
        """
        Update data via library.

        This is the only method that needs to be implemented in a DataUpdateCoordinator.
        It should fetch data from the API and return it.
        """
        try:
            data = await self.config_entry.runtime_data.client.async_get_data()

            # Fetch weather forecasts
            weather_data = await self._get_weather_data()
            data.update(weather_data)

        except IntegrationBlueprintApiClientAuthenticationError as exception:
            LOGGER.warning("Authentication error - %s", exception)
            raise ConfigEntryAuthFailed(
                translation_domain="offdelay_integration",
                translation_key="authentication_failed",
            ) from exception
        except IntegrationBlueprintApiClientError as exception:
            LOGGER.exception("Error communicating with API")
            raise UpdateFailed(
                translation_domain="offdelay_integration",
                translation_key="update_failed",
            ) from exception
        else:
            return data

    async def _get_weather_data(self) -> dict[str, Any]:
        """Get weather forecast data and compute values."""
        # Check if the weather entity exists
        if self.hass.states.get("weather.home") is None:
            message = "Weather entity 'weather.home' is not available"
            raise UpdateFailed(message)
        try:
            # Get hourly forecast for temperature max
            hourly_response = await self.hass.services.async_call(
                "weather",
                "get_forecasts",
                {"entity_id": "weather.home", "type": "hourly"},
                blocking=True,
                return_response=True,
            )

            # Get daily forecast for conditions
            daily_response = await self.hass.services.async_call(
                "weather",
                "get_forecasts",
                {"entity_id": "weather.home", "type": "daily"},
                blocking=True,
                return_response=True,
            )

            # Process hourly data for max temperature
            hourly_forecast = hourly_response.get("weather.home", {}).get(
                "forecast", []
            )
            temperatures = [
                temp
                for item in hourly_forecast
                if (temp := item.get("temperature")) is not None
                and isinstance(temp, (int, float))
            ]
            max_temp = max(temperatures) if temperatures else 17.0

            # Process daily data for condition ranks
            daily_forecast = daily_response.get("weather.home", {}).get("forecast", [])
            rank_map = {
                "sunny": 4,
                "partlycloudy": 3,
                "cloudy": 2,
                "rainy": 1,
            }

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
            # This will show entities as unavailable by raising UpdateFailed exception
            message = f"Error fetching weather data: {err}"
            raise UpdateFailed(message) from err

        return {
            "global_outside_temperature_today_max": max_temp,
            "global_outside_weather_condition_today_rank": today_rank,
            "global_outside_weather_condition_tomorrow_rank": tomorrow_rank,
        }
