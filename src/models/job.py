"""Inbound job payload from the probe-scheduler."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class JobPayload(BaseModel):
    """A single probe job dispatched by the scheduler.

    ``script`` is raw Lace source code.  ``variables`` are the fully
    resolved service variables (org -> workspace -> project -> service
    scope chain already merged by the scheduler).

    The agent is fully stateless — it doesn't need to know the job ID,
    service, org, or its own identity.  The scheduler correlates the
    response because it made the request.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    script: str
    variables: dict[str, Any] = {}
    prev: dict[str, Any] | None = None
    #: False when the scheduler forbids body persistence (unverified-domain
    #: anti-scraping limit). Bodies are then neither saved nor uploaded.
    allow_body_save: bool = True
    #: Resolved plaintext values of this run's secret variables. Masked out of
    #: any saved response body before it is uploaded, so a monitored endpoint
    #: that reflects a credential never lands the org's secret in the body store.
    secret_values: list[str] = []
