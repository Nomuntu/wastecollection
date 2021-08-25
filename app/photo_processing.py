import os
import uuid

from PIL import Image
from flask import url_for
from sqlalchemy import event

from app import config as config
from app.model import CollectionRequest

STORAGE_PATH = 'app/static/waste_photos'


def save_photo(photo) -> uuid.UUID:
    if not os.path.exists(STORAGE_PATH):
        os.makedirs(STORAGE_PATH)

    photo_id = uuid.uuid4()
    photo_path = f'{STORAGE_PATH}/{str(photo_id)}'
    photo = compress_photo(photo)
    photo.save(photo_path, 'jpeg')
    print(f'Photo saved to {photo_path}')
    return photo_id


@event.listens_for(CollectionRequest, 'after_delete')
def delete_photo(mapper, connection, target):
    try:
        os.remove(f'{STORAGE_PATH}/{str(target.photo_id)}')
    except Exception as e:
        print(f"Failed to delete photo {str(target.photo_id)} due to {e}")


def compress_photo(photo):
    photo = Image.open(photo).convert("RGB")
    width_ratio = config.PHOTO_WIDTH / float(photo.size[0])
    photo_height = int(float(photo.size[1]) * float(width_ratio))
    return photo.resize((config.PHOTO_WIDTH, photo_height), Image.NEAREST)


def photo_url(photo_id) -> str:
    return url_for('static', filename=f'waste_photos/{photo_id}')
