"""Custom types for offdelay_integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import IntegrationBlueprintApiClient
    from .coordinator import OffdelayDataUpdateCoordinator


type OffdelayIntegrationConfigEntry = ConfigEntry[OffdelayIntegrationData]


@dataclass
class OffdelayIntegrationData:
    """Data for the Offdelay integration."""

    client: IntegrationBlueprintApiClient
    coordinator: OffdelayDataUpdateCoordinator
    integration: Integration
