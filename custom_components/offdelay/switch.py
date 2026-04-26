"""Switch platform for Offdelay integration: Guest Mode and Vacation Mode."""

from __future__ import annotations

import datetime as dt
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_ON
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    ATTRIBUTION,
    CONF_GUEST_TURN_OFF_DELAY,
    CONF_GUEST_TURN_ON_DELAY,
    CONF_OCCUPANCY_SENSORS,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OffdelayConfigEntry

ZONE_HOME_ENTITY = "zone.home"
VACATION_MIN_HOURS = 4


async def async_setup_entry(  # noqa: RUF029
    hass: HomeAssistant,  # noqa: ARG001
    entry: OffdelayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Offdelay switches from a config entry."""
    config = dict(entry.data)
    async_add_entities(
        [
            GuestModeSwitch(entry, config),
            VacationModeSwitch(entry),
        ]
    )


def _device_info(entry_id: str) -> DeviceInfo:
    return DeviceInfo(
        name="Offdelay",
        identifiers={(DOMAIN, entry_id)},
        manufacturer="Offdelay",
        model="Logic Engine",
        entry_type=DeviceEntryType.SERVICE,
    )


def _zone_home_person_count(hass: HomeAssistant) -> int:
    state = hass.states.get(ZONE_HOME_ENTITY)
    if state is None:
        return 0
    try:
        return int(state.state)
    except (ValueError, TypeError):
        return 0


def _any_occupancy_on(hass: HomeAssistant, entity_ids: list[str]) -> bool:
    return any(
        (state := hass.states.get(eid)) is not None and state.state == STATE_ON
        for eid in entity_ids
    )


class GuestModeSwitch(SwitchEntity):
    """Guest mode: auto-ON when nobody home + occupancy detected, auto-OFF when occupancy clears."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_translation_key = "guest_mode"
    _attr_icon = "mdi:account-question"

    def __init__(
        self,
        config_entry: OffdelayConfigEntry,
        config: dict[str, Any],
    ) -> None:
        """Initialize guest mode switch from config entry data."""
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_guest_mode"
        self._attr_device_info = _device_info(config_entry.entry_id)

        self._occupancy_sensors: list[str] = list(
            config.get(CONF_OCCUPANCY_SENSORS, [])
        )
        self._on_delay_minutes: int = int(config.get(CONF_GUEST_TURN_ON_DELAY, 5))
        self._off_delay_minutes: int = int(config.get(CONF_GUEST_TURN_OFF_DELAY, 15))

        self._is_on = False
        self._manual_override = False
        self._on_timer: CALLBACK_TYPE | None = None
        self._off_timer: CALLBACK_TYPE | None = None
        self._listeners: list[CALLBACK_TYPE] = []

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **_kwargs: Any) -> None:  # noqa: ANN401
        self._cancel_all_timers()
        self._manual_override = True
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **_kwargs: Any) -> None:  # noqa: ANN401
        self._cancel_all_timers()
        self._manual_override = True
        self._is_on = False
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._listeners.append(
            async_track_state_change_event(
                self.hass, ZONE_HOME_ENTITY, self._async_zone_home_changed
            )
        )
        for eid in self._occupancy_sensors:
            self._listeners.append(
                async_track_state_change_event(
                    self.hass, eid, self._async_occupancy_changed
                )
            )

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_all_timers()
        for unsub in self._listeners:
            unsub()
        self._listeners.clear()

    @callback
    def _async_zone_home_changed(self, _event: Event) -> None:
        """Zone.home changed = major state change, clears manual override."""
        self._manual_override = False
        someone_home = _zone_home_person_count(self.hass) > 0

        if someone_home:
            self._cancel_all_timers()
            if self._is_on:
                self._is_on = False
                self.async_write_ha_state()
        else:
            self._evaluate_guest_mode()

    @callback
    def _async_occupancy_changed(self, _event: Event) -> None:
        if self._manual_override:
            return
        self._evaluate_guest_mode()

    @callback
    def _evaluate_guest_mode(self) -> None:
        someone_home = _zone_home_person_count(self.hass) > 0
        if someone_home:
            return

        occupancy_detected = _any_occupancy_on(self.hass, self._occupancy_sensors)

        if occupancy_detected and not self._is_on:
            self._cancel_off_timer()
            if self._on_timer is None:
                self._on_timer = async_call_later(
                    self.hass,
                    self._on_delay_minutes * 60,
                    self._async_activate_guest_mode,
                )
        elif not occupancy_detected and self._is_on:
            self._cancel_on_timer()
            if self._off_timer is None:
                self._off_timer = async_call_later(
                    self.hass,
                    self._off_delay_minutes * 60,
                    self._async_deactivate_guest_mode,
                )
        elif not occupancy_detected and not self._is_on:
            self._cancel_on_timer()

    @callback
    def _async_activate_guest_mode(self, _now: dt.datetime) -> None:
        self._on_timer = None
        if not self._manual_override and _zone_home_person_count(self.hass) == 0:
            self._is_on = True
            self.async_write_ha_state()

    @callback
    def _async_deactivate_guest_mode(self, _now: dt.datetime) -> None:
        self._off_timer = None
        if not self._manual_override:
            self._is_on = False
            self.async_write_ha_state()

    def _cancel_on_timer(self) -> None:
        if self._on_timer is not None:
            self._on_timer()
            self._on_timer = None

    def _cancel_off_timer(self) -> None:
        if self._off_timer is not None:
            self._off_timer()
            self._off_timer = None

    def _cancel_all_timers(self) -> None:
        self._cancel_on_timer()
        self._cancel_off_timer()


class VacationModeSwitch(SwitchEntity):
    """Vacation mode: only auto-turns OFF when someone arrives home and mode was active >= 4h."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_translation_key = "vacation_mode"
    _attr_icon = "mdi:beach"

    def __init__(self, config_entry: OffdelayConfigEntry) -> None:
        """Initialize vacation mode switch from config entry."""
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_vacation_mode"
        self._attr_device_info = _device_info(config_entry.entry_id)

        self._is_on = False
        self._on_since: dt.datetime | None = None
        self._manual_override = False
        self._deactivation_timer: CALLBACK_TYPE | None = None
        self._listeners: list[CALLBACK_TYPE] = []

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        if self._on_since is not None:
            attrs["on_since"] = self._on_since.isoformat()
        return attrs

    async def async_turn_on(self, **_kwargs: Any) -> None:  # noqa: ANN401
        self._cancel_timer()
        self._manual_override = True
        self._is_on = True
        self._on_since = dt_util.utcnow()
        self.async_write_ha_state()

    async def async_turn_off(self, **_kwargs: Any) -> None:  # noqa: ANN401
        self._cancel_timer()
        self._manual_override = True
        self._is_on = False
        self._on_since = None
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._listeners.append(
            async_track_state_change_event(
                self.hass, ZONE_HOME_ENTITY, self._async_zone_home_changed
            )
        )

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_timer()
        for unsub in self._listeners:
            unsub()
        self._listeners.clear()

    @callback
    def _async_zone_home_changed(self, _event: Event) -> None:
        """Zone.home changed = major state change, clears manual override."""
        self._manual_override = False
        someone_home = _zone_home_person_count(self.hass) > 0

        if not someone_home or not self._is_on:
            return

        if self._on_since is None:
            self._turn_off_vacation()
            return

        elapsed = dt_util.utcnow() - self._on_since
        min_duration = timedelta(hours=VACATION_MIN_HOURS)

        if elapsed >= min_duration:
            self._turn_off_vacation()
        elif self._deactivation_timer is None:
            remaining = (min_duration - elapsed).total_seconds()
            self._deactivation_timer = async_call_later(
                self.hass,
                remaining,
                self._async_deferred_turn_off,
            )

    @callback
    def _async_deferred_turn_off(self, _now: dt.datetime) -> None:
        self._deactivation_timer = None
        if self._is_on and not self._manual_override:
            self._turn_off_vacation()

    def _turn_off_vacation(self) -> None:
        self._is_on = False
        self._on_since = None
        self.async_write_ha_state()

    def _cancel_timer(self) -> None:
        if self._deactivation_timer is not None:
            self._deactivation_timer()
            self._deactivation_timer = None
