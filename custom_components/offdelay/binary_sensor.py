"""Binary sensor platform for offdelay."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OffdelayConfigEntry

from .const import DATA_CLIMATE_MODE
from .entity import OffdelayEntity

ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="climate_mode_winter",
        translation_key="climate_mode_winter",
        icon="mdi:snowflake",
    ),
    BinarySensorEntityDescription(
        key="climate_mode_summer",
        translation_key="climate_mode_summer",
        icon="mdi:white-balance-sunny",
    ),
    BinarySensorEntityDescription(
        key="climate_mode_winter_summer",
        translation_key="climate_mode_winter_summer",
        icon="mdi:sun-snowflake-variant",
    ),
)


async def async_setup_entry(  # noqa: RUF029
    hass: HomeAssistant,  # noqa: ARG001
    entry: OffdelayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors for this integration."""
    async_add_entities(
        OffdelayBinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=description,
        )
        for description in ENTITY_DESCRIPTIONS
    )


class OffdelayBinarySensor(OffdelayEntity, BinarySensorEntity):
    """Binary sensor representing home status or other flag."""

    @property
    def is_on(self) -> bool:
        """Return True if the sensor is on, False otherwise."""
        key = self.entity_description.key
        if key == "climate_mode_winter":
            return self.coordinator.data.get(DATA_CLIMATE_MODE) == "winter"
        if key == "climate_mode_summer":
            return self.coordinator.data.get(DATA_CLIMATE_MODE) == "summer"
        if key == "climate_mode_winter_summer":
            return self.coordinator.data.get(DATA_CLIMATE_MODE) in {"winter", "summer"}
        return self.coordinator.data.get(key, False)
