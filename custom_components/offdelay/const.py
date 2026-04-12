"""Constants for offdelay."""

from logging import Logger, getLogger

from homeassistant.const import ATTR_ENTITY_ID, Platform

LOGGER: Logger = getLogger(__package__)

DOMAIN = "offdelay"  # TEST COMMENT: Agent workflow test - please run tests and review
# Attribution text shown in Home Assistant UI for this integration
ATTRIBUTION = "Data provided by http://offdelay.be/"

# Proximity configuration
CONF_PERSONS = "persons"
PROXIMITY_NAME = "home"
PROXIMITY_ZONE = "zone.home"
PROXIMITY_TOLERANCE = 20

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]

# Config entry options for proximity
ATTR_PERSONS = ATTR_ENTITY_ID
