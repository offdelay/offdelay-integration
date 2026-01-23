"""Custom integration to integrate offdelay with Home Assistant.

For more details about this integration, please refer to
https://github.com/offdelay/offdelay_integration
"""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import IntegrationBlueprintApiClient
from .blueprint import async_setup_blueprints, async_unload_blueprints
from .const import DOMAIN, PLATFORMS
from .coordinator import OffdelayDataUpdateCoordinator
from .data import OffdelayConfigEntry, OffdelayData


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: OffdelayConfigEntry,
) -> bool:
    """Set up this integration using the UI.

    Returns:
        bool: True if setup was successful, False otherwise.

    """
    coordinator = OffdelayDataUpdateCoordinator(hass, entry)

    # Optionally set periodic update interval
    coordinator.update_interval = timedelta(hours=1)

    # Initialize runtime data
    entry.runtime_data = OffdelayData(
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

    # Set up blueprints
    await async_setup_blueprints(hass, DOMAIN)

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: OffdelayConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    await async_unload_blueprints(hass, DOMAIN)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: OffdelayConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
