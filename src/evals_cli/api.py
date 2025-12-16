"""API client for auto-monitor-setup routes."""

import requests
from typing import Optional
from .config import get_headers


class APIError(Exception):
    """Custom exception for API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class AutoMonitorSetupClient:
    """Client for auto-monitor-setup API routes."""

    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.endpoint = f"{self.base_url}/v2/auto-monitor-setups"

    @property
    def headers(self) -> dict:
        return get_headers(self.auth_token)

    def _handle_response(self, response: requests.Response) -> dict | list | None:
        """Handle API response and raise errors if needed."""
        if response.status_code >= 400:
            try:
                error_msg = response.json()
            except Exception:
                error_msg = response.text or "Unknown error"
            raise APIError(response.status_code, str(error_msg))

        if response.text:
            return response.json()
        return None

    def create(
        self,
        entity_type: str,
        entity_value: str,
        evaluator_ids: Optional[list[str]] = None,
        evaluator_types: Optional[list[str]] = None,
    ) -> dict:
        """
        Create a new auto-monitor-setup.

        Args:
            entity_type: Type of entity (e.g., 'agent')
            entity_value: Value/name of the entity
            evaluator_ids: List of existing evaluator IDs to use
            evaluator_types: List of evaluator types to create (e.g., 'hallucination', 'toxicity')

        Returns:
            Created setup object
        """
        evaluators = []

        if evaluator_ids:
            for eid in evaluator_ids:
                evaluators.append({"evaluator_id": eid})

        if evaluator_types:
            for etype in evaluator_types:
                evaluators.append({"evaluator_type": etype})

        payload = {
            "entity_type": entity_type,
            "entity_value": entity_value,
            "evaluators": evaluators,
        }

        response = requests.post(self.endpoint, headers=self.headers, json=payload)
        return self._handle_response(response)

    def list(
        self,
        entity_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list:
        """
        List auto-monitor-setups with optional filters.

        Args:
            entity_type: Filter by entity type
            status: Filter by status (e.g., 'pending', 'active')

        Returns:
            List of setup objects
        """
        params = {}
        if entity_type:
            params["entity_type"] = entity_type
        if status:
            params["status"] = status

        response = requests.get(self.endpoint, headers=self.headers, params=params)
        return self._handle_response(response)

    def get(self, setup_id: str) -> dict:
        """
        Get a specific auto-monitor-setup by ID.

        Args:
            setup_id: The ID of the setup to retrieve

        Returns:
            Setup object
        """
        url = f"{self.endpoint}/{setup_id}"
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)

    def delete(self, setup_id: str) -> None:
        """
        Delete an auto-monitor-setup by ID.

        Args:
            setup_id: The ID of the setup to delete
        """
        url = f"{self.endpoint}/{setup_id}"
        response = requests.delete(url, headers=self.headers)
        self._handle_response(response)
