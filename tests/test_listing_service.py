from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from nonprofit_cutouts.listing_service import build_service


class RecordingImageClient:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, str, str]] = []

    def remove_background(
        self, image_path: Path, output_format: str, request_key: str
    ) -> dict[str, Any]:
        self.calls.append((image_path, output_format, request_key))
        return {"id": "asset_204", "format": output_format}


def test_donor_receipt_uses_lossless_cutout_and_stable_request_key(
    tmp_path: Path,
) -> None:
    receipt = tmp_path / "receipt.jpg"
    receipt.write_bytes(b"receipt-image")
    image_client = RecordingImageClient()
    service = TestClient(build_service(image_client))
    body = {
        "listing_id": "receipt-204",
        "image_path": str(receipt),
        "use": "donor_receipt",
    }

    first = service.post("/listings/cutout", json=body)
    second = service.post("/listings/cutout", json=body)

    assert first.status_code == 200
    assert first.json() == {
        "listing_id": "receipt-204",
        "use": "donor_receipt",
        "format": "png",
        "asset": {"id": "asset_204", "format": "png"},
    }
    assert image_client.calls[0][1] == "png"
    assert image_client.calls[0][2] == image_client.calls[1][2]


def test_campaign_report_uses_webp(tmp_path: Path) -> None:
    photo = tmp_path / "campaign.jpg"
    photo.write_bytes(b"campaign-image")
    image_client = RecordingImageClient()
    service = TestClient(build_service(image_client))

    response = service.post(
        "/listings/cutout",
        json={
            "listing_id": "campaign-q3",
            "image_path": str(photo),
            "use": "campaign_report",
        },
    )

    assert response.status_code == 200
    assert response.json()["format"] == "webp"
    assert image_client.calls[0][1] == "webp"
