"""API clients for evals routes."""

import requests
from typing import Optional
from .config import get_headers


class APIError(Exception):
    """Custom exception for API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class MonitoringClient:
    """Client for monitoring API routes."""

    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.endpoint = f"{self.base_url}/v2/monitoring"

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

    def get_status(self) -> dict:
        """
        Get monitoring status for the organization.

        Returns the evaluation pipeline status including lag and health status.

        Response fields:
            - organization_id: Organization identifier
            - environment: Environment name (optional)
            - project: Project name (optional)
            - evaluated_up_to: Timestamp of last evaluation (optional)
            - latest_span_received: Timestamp of most recent span (optional)
            - lag_in_seconds: Evaluation lag in seconds
            - lag_in_spans: Number of spans not yet evaluated
            - status: OK | DEGRADED | ERROR
            - reasons: List of reasons for non-OK status

        Returns:
            Monitoring status object
        """
        url = f"{self.endpoint}/status"
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)


class MetricsClient:
    """Client for metrics API routes."""

    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token

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

    def get_metrics(
        self,
        project_id: str,
        from_timestamp_sec: int,
        to_timestamp_sec: Optional[int] = None,
        environments: Optional[list[str]] = None,
        metric_name: Optional[str] = None,
        metric_source: Optional[str] = None,
        filters: Optional[list[dict]] = None,
        logical_operator: str = "AND",
        sort_by: str = "event_time",
        sort_order: str = "DESC",
        limit: int = 50,
        cursor: int = 0,
    ) -> dict:
        """
        Get metrics with filtering and pagination.

        Args:
            project_id: Project ID
            from_timestamp_sec: Start timestamp (epoch seconds)
            to_timestamp_sec: End timestamp (epoch seconds), defaults to now
            environments: Filter by environments
            metric_name: Filter by specific metric name
            metric_source: Filter by metric source (e.g., 'openllmetry', 'sdk')
            filters: List of filter conditions
            logical_operator: AND or OR for combining filters
            sort_by: Sort field (event_time, metric_name, numeric_value, etc.)
            sort_order: ASC or DESC
            limit: Max results per page (default 50)
            cursor: Pagination cursor

        Returns:
            Paginated metrics response with grouped data points
        """
        import time

        url = f"{self.base_url}/v2/metrics"

        payload = {
            "from_timestamp_sec": from_timestamp_sec,
            "to_timestamp_sec": to_timestamp_sec or int(time.time()),
            "environments": environments or [],
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "cursor": cursor,
            "logical_operator": logical_operator,
        }

        if metric_name:
            payload["metric_name"] = metric_name
        if metric_source:
            payload["metric_source"] = metric_source
        if filters:
            payload["filters"] = filters

        response = requests.post(url, headers=self.headers, json=payload)
        return self._handle_response(response)


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
