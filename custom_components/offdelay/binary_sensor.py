"""Binary sensor platform for offdelay."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.event import async_track_state_change_event

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OffdelayConfigEntry

from .const import ATTRIBUTION, DATA_CLIMATE_MODE, DOMAIN
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

ZONE_HOME_ENTITY = "zone.home"


async def async_setup_entry(  # noqa: RUF029
    hass: HomeAssistant,  # noqa: ARG001
    entry: OffdelayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors for this integration."""
    entities: list[BinarySensorEntity] = [
        OffdelayBinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=description,
        )
        for description in ENTITY_DESCRIPTIONS
    ]

    entities.append(OffdelayHomeBinarySensor(entry))

    async_add_entities(entities)


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


class OffdelayHomeBinarySensor(BinarySensorEntity):
    """Binary sensor: ON when at least 1 person is in zone.home."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_translation_key = "is_home"
    _attr_device_class = BinarySensorDeviceClass.PRESENCE
    _attr_icon = "mdi:home-account"

    def __init__(self, config_entry: OffdelayConfigEntry) -> None:
        """Initialize the Home binary sensor."""
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_is_home"
        self._attr_device_info = DeviceInfo(
            name="Offdelay",
            identifiers={(DOMAIN, config_entry.entry_id)},
            manufacturer="Offdelay",
            model="Logic Engine",
            entry_type=DeviceEntryType.SERVICE,
        )
        self._is_on = False
        self._unsub: callback | None = None

    @property
    def is_on(self) -> bool:
        """Return True if at least 1 person is in zone.home."""
        return self._is_on

    async def async_added_to_hass(self) -> None:
        """Register zone.home state listener on add."""
        self._update_from_zone_state()

        self._unsub = async_track_state_change_event(
            self.hass, ZONE_HOME_ENTITY, self._async_zone_home_changed
        )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listener on remove."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

    @callback
    def _async_zone_home_changed(self, event: Event) -> None:  # noqa: ARG002
        """Handle zone.home state change."""
        self._update_from_zone_state()
        self.async_write_ha_state()

    def _update_from_zone_state(self) -> None:
        """Update _is_on from current zone.home state."""
        state = self.hass.states.get(ZONE_HOME_ENTITY)
        if state is None:
            self._is_on = False
            return
        try:
            self._is_on = int(state.state) > 0
        except (ValueError, TypeError):
            self._is_on = False
