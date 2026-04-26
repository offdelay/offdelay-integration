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

    from .coordinator import OffdelayDataUpdateCoordinator
    from .data import OffdelayConfigEntry

from .const import CONF_CLIMATES_BOOST, DATA_CLIMATE_MODE
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
    coordinator = entry.runtime_data.coordinator

    static_sensors = [
        OffdelayBinarySensor(
            coordinator=coordinator,
            entity_description=description,
        )
        for description in ENTITY_DESCRIPTIONS
    ]

    boost_climates = entry.data.get(CONF_CLIMATES_BOOST, [])
    boost_sensors: list[OffdelayBoostBinarySensor] = []
    for climate_id in boost_climates:
        climate_name = climate_id.split(".")[-1]
        for boost_type, temp_label in (("summer", "17"), ("winter", "24")):
            description = BinarySensorEntityDescription(
                key=f"boost_{climate_name}_{boost_type}",
                translation_key=f"boost_{climate_name}_{boost_type}",
                name=f"offdelay boost {temp_label}",
                icon="mdi:snowflake" if boost_type == "summer" else "mdi:fire",
            )
            boost_sensors.append(
                OffdelayBoostBinarySensor(
                    coordinator=coordinator,
                    entity_description=description,
                    climate_entity_id=climate_id,
                    boost_type=boost_type,
                )
            )

    async_add_entities(static_sensors + boost_sensors)


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


class OffdelayBoostBinarySensor(OffdelayEntity, BinarySensorEntity):
    """Binary sensor for heatpump boost activation (summer/winter specific)."""

    def __init__(
        self,
        coordinator: OffdelayDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
        climate_entity_id: str,
        boost_type: str,
    ) -> None:
        """Initialize boost binary sensor."""
        super().__init__(coordinator, entity_description)
        self._climate_entity_id = climate_entity_id
        self._boost_type = boost_type

    @property
    def is_on(self) -> bool:
        """Return True if boost should be active for this season."""
        boost_state = self.coordinator.data.get("boost_state", {})
        switch_on = boost_state.get(self._climate_entity_id, False)

        if not switch_on:
            return False

        winter_mode = self.coordinator.data.get(DATA_CLIMATE_MODE) == "winter"

        if self._boost_type == "winter":
            return winter_mode
        return not winter_mode
