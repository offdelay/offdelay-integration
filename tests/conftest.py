"""Fixtures for the Off-delay integration tests."""

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return


@pytest.fixture(name="config")
def config_fixture():
    """Provide a default configuration for the integration."""
    return {
        "platform": "offdelay",
        "delay": 10,
    }
