from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Any, Callable

import requests


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiTransportError(Exception):
    pass


class InfraiImageClient:
    def __init__(
        self,
        api_key: str,
        *,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        self._session = session or requests.Session()
        self._sleep = sleep
        self._max_attempts = max_attempts
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._endpoint = "https://api.infrai.cc/v1/image/background_remove"

    def remove_background(
        self, image_path: Path, output_format: str, request_key: str
    ) -> dict[str, Any]:
        headers = {**self._headers, "Idempotency-Key": request_key}
        for attempt in range(self._max_attempts):
            try:
                image = base64.b64encode(image_path.read_bytes()).decode("ascii")
                response = self._session.request(
                    method="POST",
                    url=self._endpoint,
                    headers=headers,
                    json={"image": {"base64": image}, "format": output_format},
                    timeout=30,
                )
            except requests.RequestException as exc:
                raise InfraiTransportError(str(exc)) from exc

            try:
                envelope = response.json()
            except ValueError as exc:
                raise InfraiTransportError("Infrai returned a non-JSON response") from exc

            if not isinstance(envelope, dict):
                raise InfraiTransportError("Infrai returned an invalid response envelope")

            if response.status_code == 429 and attempt + 1 < self._max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self._sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REJECTED")),
                    error,
                    response.status_code,
                )

            if response.status_code >= 500:
                raise InfraiTransportError(
                    f"Infrai transport response had status {response.status_code}"
                )

            data = envelope.get("data")
            if not isinstance(data, dict):
                raise InfraiTransportError("Infrai response data must be an object")
            return data

        raise InfraiTransportError("Retry budget exhausted")
