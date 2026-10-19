from io import BytesIO

from PIL import Image, UnidentifiedImageError


class ValidationError(Exception):
    status_code = 400


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_FORMATS = {"JPEG", "PNG"}


def validate_image_uploads(files, config):
    files = [file for file in files if file and file.filename]
    if not files:
        raise ValidationError("Please select at least one image.")
    if len(files) > config["MAX_BATCH_SIZE"]:
        raise ValidationError(f"You can upload at most {config['MAX_BATCH_SIZE']} images.")

    validated = []
    for file in files:
        extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationError("Only JPG, JPEG, and PNG images are supported.")
        content = file.read(config["MAX_UPLOAD_BYTES"] + 1)
        file.seek(0)
        if len(content) > config["MAX_UPLOAD_BYTES"]:
            raise ValidationError(f"Each image must be smaller than {config['MAX_UPLOAD_BYTES'] // 1024 // 1024} MB.")
        try:
            with Image.open(BytesIO(content)) as image:
                if image.format not in ALLOWED_FORMATS:
                    raise ValidationError("The uploaded file is not a supported image.")
                image.verify()
        except (UnidentifiedImageError, OSError):
            raise ValidationError("The uploaded file is corrupted or is not a valid image.")
        validated.append(file)
    return validated

