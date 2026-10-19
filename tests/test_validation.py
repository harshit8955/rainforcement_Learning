from io import BytesIO

from PIL import Image

from src.validators import ValidationError, validate_image_uploads


CONFIG = {"MAX_BATCH_SIZE": 2, "MAX_UPLOAD_BYTES": 100000}


def test_valid_png():
    stream = BytesIO()
    Image.new("RGB", (10, 10), "red").save(stream, format="PNG")
    stream.seek(0)
    file = type("Upload", (), {"filename": "image.png", "read": lambda self, size=-1: stream.read(size), "seek": lambda self, offset=0: stream.seek(offset)})()
    assert validate_image_uploads([file], CONFIG)[0] is file


def test_invalid_extension():
    file = type("Upload", (), {"filename": "image.exe", "read": lambda self, size=-1: b"", "seek": lambda self: None})()
    try:
        validate_image_uploads([file], CONFIG)
    except ValidationError:
        return
    raise AssertionError("Expected validation failure")
