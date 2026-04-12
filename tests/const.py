"""Constants for the Off-delay integration tests."""

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from custom_components.offdelay.const import CONF_PERSONS

MOCK_CONFIG = {
    CONF_USERNAME: "test_username",
    CONF_PASSWORD: "test_password",
}

MOCK_CONFIG_WITH_PERSONS = {
    CONF_USERNAME: "test_username",
    CONF_PASSWORD: "test_password",
    CONF_PERSONS: ["person.john", "person.jane"],
}
