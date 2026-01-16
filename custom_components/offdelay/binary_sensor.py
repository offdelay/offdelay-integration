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

    from .data import OffdelayIntegrationConfigEntry

from .entity import OffdelayIntegrationEntity

ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="is_home",
        translation_key="is_home",
        icon="mdi:home-account",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OffdelayIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors for this integration."""
    async_add_entities(
        OffdelayIntegrationBinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=description,
        )
        for description in ENTITY_DESCRIPTIONS
    )


class OffdelayIntegrationBinarySensor(OffdelayIntegrationEntity, BinarySensorEntity):
    """Binary sensor representing home status or other flag."""

    @property
    def is_on(self) -> bool:
        """Return True if the sensor is on, False otherwise."""
        return self.coordinator.data.get(self.entity_description.key, False)
