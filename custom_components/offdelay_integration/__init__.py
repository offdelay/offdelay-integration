#!/usr/bin/env python3
"""
Custom integration to integrate offdelay_integration with Home Assistant.

For more details about this integration, please refer to
https://github.com/offdelay/offdelay_integration
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import IntegrationBlueprintApiClient
from .coordinator import OffdelayDataUpdateCoordinator
from .data import OffdelayIntegrationData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import OffdelayIntegrationConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: OffdelayIntegrationConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    # Create coordinator (logger and name are positional)
    coordinator = OffdelayDataUpdateCoordinator(hass, entry)

    # Optionally set periodic update interval
    coordinator.update_interval = timedelta(hours=1)

    # Initialize runtime data
    entry.runtime_data = OffdelayIntegrationData(
        client=IntegrationBlueprintApiClient(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # Perform first refresh
    await coordinator.async_config_entry_first_refresh()

    # Forward platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: OffdelayIntegrationConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: OffdelayIntegrationConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
