"""Adds config flow for Blueprint."""

from homeassistant import config_entries
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers import selector
import voluptuous as vol

from .const import (
    CONF_CLIMATE_DAY_START_HOUR,
    CONF_CLIMATE_DELTA_TOLERANCE,
    CONF_CLIMATE_NIGHT_START_HOUR,
    CONF_CLIMATES,
    CONF_CLIMATES_BOOST,
    CONF_SUMMER_MIN_TEMP,
    CONF_WINTER_MAX_TEMP,
    DOMAIN,
)


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
            winter_temp = user_input[CONF_WINTER_MAX_TEMP]
            summer_temp = user_input[CONF_SUMMER_MIN_TEMP]
            if winter_temp >= summer_temp:
                errors["base"] = "winter_summer_temp_conflict"
            elif (summer_temp - winter_temp) <= 0.1:
                errors["base"] = "winter_summer_temp_too_close"

            if not errors:
                day_hour = int(user_input[CONF_CLIMATE_DAY_START_HOUR])
                night_hour = int(user_input[CONF_CLIMATE_NIGHT_START_HOUR])
                if day_hour >= night_hour:
                    errors["base"] = "day_night_hour_conflict"

            if not errors:
                return self.async_create_entry(
                    title="Offdelay",
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
                        CONF_WINTER_MAX_TEMP,
                        default=(user_input or {}).get(CONF_WINTER_MAX_TEMP, 20.0),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode="box",
                            unit_of_measurement=UnitOfTemperature.CELSIUS,
                            step=0.1,
                        ),
                    ),
                    vol.Required(
                        CONF_SUMMER_MIN_TEMP,
                        default=(user_input or {}).get(CONF_SUMMER_MIN_TEMP, 21.0),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode="box",
                            unit_of_measurement=UnitOfTemperature.CELSIUS,
                            step=0.1,
                        ),
                    ),
                    vol.Optional(
                        CONF_CLIMATES,
                        default=(user_input or {}).get(CONF_CLIMATES, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="climate",
                            multiple=True,
                        ),
                    ),
                    vol.Optional(
                        CONF_CLIMATES_BOOST,
                        default=(user_input or {}).get(CONF_CLIMATES_BOOST, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="climate",
                            multiple=True,
                        ),
                    ),
                    vol.Required(
                        CONF_CLIMATE_DELTA_TOLERANCE,
                        default=(user_input or {}).get(
                            CONF_CLIMATE_DELTA_TOLERANCE, 0.5
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode="box",
                            unit_of_measurement=UnitOfTemperature.CELSIUS,
                            step=0.1,
                        ),
                    ),
                    vol.Required(
                        CONF_CLIMATE_DAY_START_HOUR,
                        default=(user_input or {}).get(CONF_CLIMATE_DAY_START_HOUR, 8),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode="box",
                            min=0,
                            max=23,
                            step=1,
                        ),
                    ),
                    vol.Required(
                        CONF_CLIMATE_NIGHT_START_HOUR,
                        default=(user_input or {}).get(
                            CONF_CLIMATE_NIGHT_START_HOUR, 17
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode="box",
                            min=0,
                            max=23,
                            step=1,
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
            winter_temp = user_input[CONF_WINTER_MAX_TEMP]
            summer_temp = user_input[CONF_SUMMER_MIN_TEMP]
            if winter_temp >= summer_temp:
                errors["base"] = "winter_summer_temp_conflict"
            elif (summer_temp - winter_temp) <= 0.1:
                errors["base"] = "winter_summer_temp_too_close"

            if not errors:
                day_hour = int(user_input[CONF_CLIMATE_DAY_START_HOUR])
                night_hour = int(user_input[CONF_CLIMATE_NIGHT_START_HOUR])
                if day_hour >= night_hour:
                    errors["base"] = "day_night_hour_conflict"

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_WINTER_MAX_TEMP,
                        default=entry.data.get(CONF_WINTER_MAX_TEMP, 20.0),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode="box",
                            unit_of_measurement=UnitOfTemperature.CELSIUS,
                            step=0.1,
                        ),
                    ),
                    vol.Required(
                        CONF_SUMMER_MIN_TEMP,
                        default=entry.data.get(CONF_SUMMER_MIN_TEMP, 21.0),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode="box",
                            unit_of_measurement=UnitOfTemperature.CELSIUS,
                            step=0.1,
                        ),
                    ),
                    vol.Optional(
                        CONF_CLIMATES,
                        default=entry.data.get(CONF_CLIMATES, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="climate",
                            multiple=True,
                        ),
                    ),
                    vol.Optional(
                        CONF_CLIMATES_BOOST,
                        default=entry.data.get(CONF_CLIMATES_BOOST, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="climate",
                            multiple=True,
                        ),
                    ),
                    vol.Required(
                        CONF_CLIMATE_DELTA_TOLERANCE,
                        default=entry.data.get(CONF_CLIMATE_DELTA_TOLERANCE, 0.5),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode="box",
                            unit_of_measurement=UnitOfTemperature.CELSIUS,
                            step=0.1,
                        ),
                    ),
                    vol.Required(
                        CONF_CLIMATE_DAY_START_HOUR,
                        default=entry.data.get(CONF_CLIMATE_DAY_START_HOUR, 8),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode="box",
                            min=0,
                            max=23,
                            step=1,
                        ),
                    ),
                    vol.Required(
                        CONF_CLIMATE_NIGHT_START_HOUR,
                        default=entry.data.get(CONF_CLIMATE_NIGHT_START_HOUR, 17),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode="box",
                            min=0,
                            max=23,
                            step=1,
                        ),
                    ),
                },
            ),
            errors=errors,
        )
