"""Switch platform for offdelay_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)

from .entity import OffdelayIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OffdelayIntegrationConfigEntry


ENTITY_DESCRIPTIONS = (
    SwitchEntityDescription(
        key="vacation_mode",
        translation_key="vacation_mode",
        icon="mdi:home-export-outline",
    ),
    SwitchEntityDescription(
        key="guest_mode",
        translation_key="guest_mode",
        icon="mdi:account-convert-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OffdelayIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    async_add_entities(
        OffdelayIntegrationModeSwitch(
            coordinator=entry.runtime_data.coordinator,
            entity_description=description,
        )
        for description in ENTITY_DESCRIPTIONS
    )


class OffdelayIntegrationModeSwitch(OffdelayIntegrationEntity, SwitchEntity):
    """Offdelay mode switch."""

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return bool(self.coordinator.data.get(self.entity_description.key))

    async def async_turn_on(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Turn the switch on."""
        await self.coordinator.async_set_home_data(
            self.entity_description.key, value=True
        )

    async def async_turn_off(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Turn the switch off."""
        await self.coordinator.async_set_home_data(
            self.entity_description.key, value=False
        )
