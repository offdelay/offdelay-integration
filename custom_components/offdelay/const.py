"""Constants for offdelay."""

from logging import Logger, getLogger

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

DOMAIN = "offdelay"  # TEST COMMENT: Agent workflow test - please run tests and review
# Attribution text shown in Home Assistant UI for this integration
ATTRIBUTION = "Data provided by http://offdelay.be/"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]
