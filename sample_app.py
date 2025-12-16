#!/usr/bin/env python3

import os
from datetime import datetime, timedelta

from evals_cli.api import (
    AutoMonitorSetupClient,
    MetricsClient,
    MonitoringClient,
    OrganizationClient,
)

BASE_URL = "http://localhost:8080"
AUTH_TOKEN = "Bearer your-auth-token-here"


def step1_create_organization() -> dict:
    client = OrganizationClient(BASE_URL, AUTH_TOKEN)
    return client.create(org_name="Demo Organization", environments=["prd"])


def step2_create_monitor_setup(api_key: str) -> dict:
    client = AutoMonitorSetupClient(BASE_URL, api_key)
    return client.create(
        entity_type="workflow",
        entity_value="pirate_tech_joke_generator",
        evaluator_types=["char-count"],
    )


def step3_check_monitoring_status(api_key: str) -> dict:
    client = MonitoringClient(BASE_URL, api_key)
    return client.get_status()


def step4_get_metrics(api_key: str, project_id: str = None) -> dict:
    client = MetricsClient(BASE_URL, api_key)
    from_timestamp = int((datetime.now() - timedelta(days=7)).timestamp())
    to_timestamp = int(datetime.now().timestamp())
    project_id = project_id or os.environ.get("EVALS_PROJECT_ID", "demo-project")

    return client.get_metrics(
        project_id=project_id,
        from_timestamp_sec=from_timestamp,
        to_timestamp_sec=to_timestamp,
        limit=10,
    )


def main():
    org_result = step1_create_organization()
    print("Step 1 - Organization created:", org_result)

    new_api_key = org_result["environments"][0]["api_key"]

    setup_result = step2_create_monitor_setup(new_api_key)
    print("Step 2 - Monitor setup created:", setup_result)

    status_result = step3_check_monitoring_status(new_api_key)
    print("Step 3 - Monitoring status:", status_result)

    metrics_result = step4_get_metrics(new_api_key)
    print("Step 4 - Metrics:", metrics_result)


if __name__ == "__main__":
    main()
