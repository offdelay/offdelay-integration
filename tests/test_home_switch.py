"""Test the Off-delay switch platform."""

from unittest.mock import AsyncMock, patch

from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.offdelay.const import DOMAIN

from .const import MOCK_CONFIG, MOCK_CONFIG_WITH_PERSONS


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


@pytest.fixture(autouse=True)
def mock_zone_home(hass: HomeAssistant):
    """Mock zone.home to exist for tests."""
    hass.states.async_set(
        "zone.home",
        "zoning",
        {
            "friendly_name": "Home",
            "latitude": 51.524,
            "longitude": -0.104,
            "radius": 100,
        },
    )


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


async def test_proximity_sensor_created(hass: HomeAssistant) -> None:
    """Test that proximity sensor is created when persons are configured."""
    hass.states.async_set(
        "device_tracker.john_phone",
        "not_home",
        {"device_id": "device_123", "friendly_name": "John's Phone"},
    )
    hass.states.async_set(
        "device_tracker.jane_phone",
        "not_home",
        {"device_id": "device_456", "friendly_name": "Jane's Phone"},
    )

    hass.states.async_set(
        "person.john",
        "not_home",
        {"friendly_name": "John", "device_ids": ["device_123"]},
    )
    hass.states.async_set(
        "person.jane",
        "not_home",
        {"friendly_name": "Jane", "device_ids": ["device_456"]},
    )

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_WITH_PERSONS)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Verify proximity sensor exists
    state = hass.states.get("sensor.home_nearest_distance")
    assert state is not None, (
        "Proximity sensor 'sensor.home_nearest_distance' was not created"
    )

    # Verify sensor has expected attributes
    assert state.attributes.get("unit_of_measurement") == "m"
    assert state.attributes.get("friendly_name") == "Home Nearest distance"

    # Verify proximity config entry was created (check by title/name)
    proximity_entries = hass.config_entries.async_entries("proximity")
    assert len(proximity_entries) >= 1, "No proximity config entries were created"

    # Find the "home" proximity entry
    home_proximity = next(
        (entry for entry in proximity_entries if entry.data.get("zone") == "zone.home"),
        None,
    )
    assert home_proximity is not None, (
        "Proximity config entry for 'zone.home' was not created"
    )
    assert home_proximity.data["tolerance"] == 20
