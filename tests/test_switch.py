"""Test the Off-delay switch platform."""

from unittest.mock import AsyncMock, patch

from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.offdelay.const import DOMAIN

from .const import MOCK_CONFIG


@pytest.fixture(autouse=True)
def bypass_api_and_weather():
    """Bypass API and weather calls."""
    with (
        patch(
            "custom_components.offdelay.api.IntegrationBlueprintApiClient.async_get_data",
            new_callable=AsyncMock,
            return_value={"title": "test"},
        ),
        patch(
            "custom_components.offdelay.coordinator.OffdelayDataUpdateCoordinator._update_weather_data",
            new_callable=AsyncMock,
            return_value={
                "weather_max_temp_today": 20,
                "weather_condition_rank_today": 4,
                "weather_condition_rank_tomorrow": 4,
                "weather_condition_today": "sunny",
                "weather_condition_tomorrow": "sunny",
            },
        ),
    ):
        yield


async def test_vacation_mode_switch(hass: HomeAssistant) -> None:
    """Test the vacation mode switch."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("switch.offdelay_vacation_mode")
    assert state
    assert state.state == STATE_OFF

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.offdelay_vacation_mode"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("switch.offdelay_vacation_mode")
    assert state
    assert state.state == STATE_ON

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.offdelay_vacation_mode"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("switch.offdelay_vacation_mode")
    assert state
    assert state.state == STATE_OFF


async def test_guest_mode_switch(hass: HomeAssistant) -> None:
    """Test the guest mode switch."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("switch.offdelay_guest_mode")
    assert state
    assert state.state == STATE_OFF

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.offdelay_guest_mode"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("switch.offdelay_guest_mode")
    assert state
    assert state.state == STATE_ON

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.offdelay_guest_mode"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("switch.offdelay_guest_mode")
    assert state
    assert state.state == STATE_OFF


async def test_switches_created(hass: HomeAssistant) -> None:
    """Test that both switches are created."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("switch.offdelay_vacation_mode")
    assert hass.states.get("switch.offdelay_guest_mode")
