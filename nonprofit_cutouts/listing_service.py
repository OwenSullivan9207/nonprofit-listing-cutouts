from __future__ import annotations

import hashlib
import os
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .infrai_client import InfraiError, InfraiImageClient, InfraiTransportError


class ListingUse(str, Enum):
    donor_receipt = "donor_receipt"
    volunteer_reminder = "volunteer_reminder"
    campaign_report = "campaign_report"


class CutoutRequest(BaseModel):
    listing_id: str = Field(min_length=1, max_length=100)
    image_path: Path
    use: ListingUse


class CutoutResult(BaseModel):
    listing_id: str
    use: ListingUse
    format: str
    asset: dict[str, Any]


def output_format_for(use: ListingUse) -> str:
    return "png" if use is ListingUse.donor_receipt else "webp"


def request_key_for(request: CutoutRequest) -> str:
    source = f"{request.listing_id}:{request.use.value}:{request.image_path.resolve()}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def build_service(client: InfraiImageClient | None = None) -> FastAPI:
    app = FastAPI(title="Nonprofit listing cutouts")

    @app.post("/listings/cutout", response_model=CutoutResult)
    def create_cutout(request: CutoutRequest) -> CutoutResult:
        if not request.image_path.is_file():
            raise HTTPException(status_code=400, detail="image_path must name a file")

        active_client = client
        if active_client is None:
            api_key = os.environ.get("INFRAI_API_KEY")
            if not api_key:
                raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")
            active_client = InfraiImageClient(api_key)

        output_format = output_format_for(request.use)
        try:
            asset = active_client.remove_background(
                request.image_path,
                output_format,
                request_key_for(request),
            )
        except InfraiError as exc:
            client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
            raise HTTPException(status_code=client_status, detail=exc.detail) from exc
        except InfraiTransportError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return CutoutResult(
            listing_id=request.listing_id,
            use=request.use,
            format=output_format,
            asset=asset,
        )

    return app


app = build_service()
