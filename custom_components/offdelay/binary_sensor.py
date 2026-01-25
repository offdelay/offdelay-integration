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

from .entity import OffdelayEntity

ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="is_home",
        translation_key="is_home",
        icon="mdi:home-account",
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
        return self.coordinator.data.get(self.entity_description.key, False)
