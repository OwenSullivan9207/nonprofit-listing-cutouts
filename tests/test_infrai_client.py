import base64
from pathlib import Path
from unittest.mock import Mock

from nonprofit_cutouts.infrai_client import InfraiImageClient


def test_background_remove_sends_json_image_and_format(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"image bytes")
    session = Mock()
    session.request.return_value.json.return_value = {"ok": True, "data": {"id": "asset"}}
    session.request.return_value.status_code = 200

    result = InfraiImageClient("test-key", session=session).remove_background(
        image_path, "png", "stable-key"
    )

    assert result == {"id": "asset"}
    kwargs = session.request.call_args.kwargs
    assert kwargs["json"] == {
        "image": {"base64": base64.b64encode(b"image bytes").decode("ascii")},
        "format": "png",
    }
    assert kwargs["headers"]["Idempotency-Key"] == "stable-key"
    assert "files" not in kwargs
    assert "data" not in kwargs
