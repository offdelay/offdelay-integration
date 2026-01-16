#!/usr/bin/env python3
"""Sensor platform for offdelay."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfTemperature

from .entity import OffdelayIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OffdelayIntegrationConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="weather_max_temp_today",
        translation_key="weather_max_temp_today",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key="weather_condition_rank_today",
        translation_key="weather_condition_rank_today",
        icon="mdi:weather-sunny",
    ),
    SensorEntityDescription(
        key="weather_condition_rank_tomorrow",
        translation_key="weather_condition_rank_tomorrow",
        icon="mdi:weather-sunny",
    ),
    SensorEntityDescription(
        key="weather_condition_today",
        translation_key="weather_condition_today",
        icon="mdi:weather-partly-cloudy",
    ),
    SensorEntityDescription(
        key="weather_condition_tomorrow",
        translation_key="weather_condition_tomorrow",
        icon="mdi:weather-partly-cloudy",
    ),
    SensorEntityDescription(
        key="home_status",
        translation_key="home_status",
        icon="mdi:home",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: OffdelayIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        OffdelayIntegrationSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class OffdelayIntegrationSensor(OffdelayIntegrationEntity, SensorEntity):
    """offdelay Sensor class."""

    @property
    def native_value(self) -> float | int | str | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.get(self.entity_description.key)
