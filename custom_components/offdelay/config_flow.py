"""Adds config flow for Blueprint."""

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from slugify import slugify
import voluptuous as vol

from .api import (
    IntegrationBlueprintApiClient,
    IntegrationBlueprintApiClientAuthenticationError,
    IntegrationBlueprintApiClientCommunicationError,
    IntegrationBlueprintApiClientError,
)
from .const import DOMAIN, LOGGER

# Map exception types to error keys for user-facing messages
ERROR_MAP = {
    IntegrationBlueprintApiClientAuthenticationError: "auth",
    IntegrationBlueprintApiClientCommunicationError: "connection",
}


class OffdelayFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user.

        https://developers.home-assistant.io/docs/config_entries_config_flow_handler/#defining-steps

        Returns:
            config_entries.ConfigFlowResult: The result of the config flow.

        """
        errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
            except (
                IntegrationBlueprintApiClientAuthenticationError,
                IntegrationBlueprintApiClientCommunicationError,
                IntegrationBlueprintApiClientError,
            ) as exception:
                errors["base"] = self._handle_client_error(exception)
            else:
                await self.async_set_unique_id(
                    # Do NOT use this in production code
                    # The unique_id should never be something that can change
                    # https://developers.home-assistant.io/docs/config_entries_config_flow_handler#unique-ids
                    unique_id=slugify(user_input[CONF_USERNAME])
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            description_placeholders={
                "docs_url": "https://github.com/offdelay/offdelay_integration"
            },
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a reconfiguration of the integration.

        Returns:
            config_entries.ConfigFlowResult: The result of the config flow.

        """
        entry = self._get_reconfigure_entry()

        errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
            except (
                IntegrationBlueprintApiClientAuthenticationError,
                IntegrationBlueprintApiClientCommunicationError,
                IntegrationBlueprintApiClientError,
            ) as exception:
                errors["base"] = self._handle_client_error(exception)
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=entry.data.get(CONF_USERNAME),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_PASSWORD,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=errors,
        )

    async def _test_credentials(self, username: str, password: str) -> None:
        """Validate credentials."""
        client = IntegrationBlueprintApiClient(
            username=username,
            password=password,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_data()

    @staticmethod
    def _handle_client_error(exception: IntegrationBlueprintApiClientError) -> str:
        """Handle API client errors and return appropriate error key.

        Maps exception types to user-facing error messages defined in translations.

        Returns:
            str: The error key.

        """
        LOGGER.warning(exception)
        return ERROR_MAP.get(type(exception), "unknown")
