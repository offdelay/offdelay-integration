"""Switch platform for offdelay_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.exceptions import HomeAssistantError

from .api import IntegrationBlueprintApiClientError
from .const import LOGGER
from .entity import OffdelayIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OffdelayIntegrationConfigEntry

ENTITY_DESCRIPTIONS = (
    SwitchEntityDescription(
        key="offdelay_integration",
        translation_key="offdelay_integration",
        icon="mdi:format-quote-close",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: OffdelayIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    async_add_entities(
        OffdelayIntegrationSwitch(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class OffdelayIntegrationSwitch(OffdelayIntegrationEntity, SwitchEntity):
    """offdelay_integration switch class."""

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data.get("title", "") == "foo"

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the switch."""
        try:
            await self.coordinator.config_entry.runtime_data.client.async_set_title(
                "bar"
            )
            await self.coordinator.async_request_refresh()
        except IntegrationBlueprintApiClientError as exception:
            LOGGER.exception(
                "Failed to turn on switch %s",
                self.entity_description.key,
            )
            raise HomeAssistantError(
                translation_domain="offdelay_integration",
                translation_key="switch_turn_on_failed",
            ) from exception

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the switch."""
        try:
            await self.coordinator.config_entry.runtime_data.client.async_set_title(
                "foo"
            )
            await self.coordinator.async_request_refresh()
        except IntegrationBlueprintApiClientError as exception:
            LOGGER.exception(
                "Failed to turn off switch %s",
                self.entity_description.key,
            )
            raise HomeAssistantError(
                translation_domain="offdelay_integration",
                translation_key="switch_turn_off_failed",
            ) from exception
