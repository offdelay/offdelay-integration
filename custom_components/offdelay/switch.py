"""Switch platform for offdelay boost feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import OffdelayDataUpdateCoordinator
    from .data import OffdelayConfigEntry

from .const import CONF_CLIMATES_BOOST
from .entity import OffdelayEntity


def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OffdelayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up boost switches for configured climates."""
    boost_climates = entry.data.get(CONF_CLIMATES_BOOST, [])

    entities = []
    for climate_id in boost_climates:
        climate_name = climate_id.split(".")[-1]
        description = SwitchEntityDescription(
            key=f"boost_{climate_name}",
            translation_key=f"boost_{climate_name}",
            icon="mdi:heat-wave",
        )
        entities.append(
            OffdelayBoostSwitch(
                coordinator=entry.runtime_data.coordinator,
                entity_description=description,
                climate_entity_id=climate_id,
            )
        )

    async_add_entities(entities)


class OffdelayBoostSwitch(OffdelayEntity, SwitchEntity):
    """Switch to control heatpump boost mode."""

    def __init__(
        self,
        coordinator: OffdelayDataUpdateCoordinator,
        entity_description: SwitchEntityDescription,
        climate_entity_id: str,
    ) -> None:
        """Initialize boost switch."""
        super().__init__(coordinator, entity_description)
        self._climate_entity_id = climate_entity_id

    @property
    def is_on(self) -> bool:
        """Return True if switch is on."""
        boost_state = self.coordinator.data.get("boost_state", {})
        return boost_state.get(self._climate_entity_id, False)

    async def async_turn_on(self, **kwargs) -> None:  # noqa: ARG002, ANN003
        """Turn on boost switch."""
        self.coordinator.set_boost_active(self._climate_entity_id, active=True)

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ARG002, ANN003
        """Turn off boost switch."""
        self.coordinator.set_boost_active(self._climate_entity_id, active=False)
