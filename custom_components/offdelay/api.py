"""Sample API Client."""

from __future__ import annotations

import asyncio
import socket

import aiohttp


class IntegrationBlueprintApiClientError(Exception):
    """Exception to indicate a general API error."""


class IntegrationBlueprintApiClientCommunicationError(
    IntegrationBlueprintApiClientError,
):
    """Exception to indicate a communication error."""


class IntegrationBlueprintApiClientAuthenticationError(
    IntegrationBlueprintApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid.

    Raises:
        IntegrationBlueprintApiClientAuthenticationError: If the response indicates an authentication error.

    """
    if response.status in {401, 403}:
        msg = "Invalid credentials"
        raise IntegrationBlueprintApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class IntegrationBlueprintApiClient:
    """Sample API Client."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Sample API Client."""
        self._username = username
        self._password = password
        self._session = session

    async def async_get_data(self) -> dict:
        """Get data from the API.

        Returns:
            dict: The data from the API.

        """
        return await self._api_wrapper(
            method="get",
            url="https://jsonplaceholder.typicode.com/posts/1",
        )

    async def async_set_title(self, value: str) -> dict:
        """Get data from the API.

        Returns:
            dict: The data from the API.

        """
        return await self._api_wrapper(
            method="patch",
            url="https://jsonplaceholder.typicode.com/posts/1",
            data={"title": value},
            headers={"Content-type": "application/json; charset=UTF-8"},
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        """Get information from the API.

        Returns:
            dict: The data from the API.

        Raises:
            IntegrationBlueprintApiClientCommunicationError: If a communication error occurs.
            IntegrationBlueprintApiClientError: If a general API error occurs.

        """
        try:
            async with asyncio.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise IntegrationBlueprintApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise IntegrationBlueprintApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:
            msg = f"Something really wrong happened! - {exception}"
            raise IntegrationBlueprintApiClientError(
                msg,
            ) from exception
