#!/usr/bin/env python3
"""Number platform for offdelay_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import UnitOfTemperature

from .entity import IntegrationBlueprintEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import IntegrationBlueprintConfigEntry

ENTITY_DESCRIPTIONS = (
    NumberEntityDescription(
        key="global_outside_temperature_today_max",
        translation_key="global_outside_temperature_today_max",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=-50,
        native_max_value=50,
        native_step=0.1,
    ),
    NumberEntityDescription(
        key="global_outside_weather_condition_today_rank",
        translation_key="global_outside_weather_condition_today_rank",
        icon="mdi:weather-sunny",
        native_min_value=0,
        native_max_value=4,
        native_step=1,
    ),
    NumberEntityDescription(
        key="global_outside_weather_condition_tomorrow_rank",
        translation_key="global_outside_weather_condition_tomorrow_rank",
        icon="mdi:weather-sunny",
        native_min_value=0,
        native_max_value=4,
        native_step=1,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: IntegrationBlueprintConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    async_add_entities(
        IntegrationBlueprintNumber(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class IntegrationBlueprintNumber(IntegrationBlueprintEntity, NumberEntity):
    """offdelay_integration Number class."""

    @property
    def native_value(self) -> float | None:
        """Return the native value of the number."""
        return self.coordinator.data.get(self.entity_description.key)

    def set_native_value(self, value: float) -> None:
        """Set the native value of the number."""
        # This is a read-only entity
        msg = "This number entity is read-only"
        raise NotImplementedError(msg)

    def set_value(self, value: float) -> None:
        """Set the value of the number."""
        # This is a read-only entity
        msg = "This number entity is read-only"
        raise NotImplementedError(msg)
