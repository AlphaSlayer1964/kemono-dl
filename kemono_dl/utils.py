import hashlib
import os
import re
from pathlib import Path

from requests import Session


def get_sha256_hash(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def format_bytes(size) -> str:
    for unit in ["B", "KiB", "MiB", "GiB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TiB"


def make_path_safe(value: str, replace: str = "_") -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', str(replace), str(value))


def get_sha256_url_content(session: Session, url: str, chunk_size: int = 8192):
    sha256 = hashlib.sha256()
    with session.get(url, stream=True) as response:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                sha256.update(chunk)
    return sha256.hexdigest()


def generate_file_path(base_path: str, output_template: str, template_variables: dict):
    try:
        expanded_path = output_template.format(**template_variables)
    except KeyError as e:
        raise ValueError(f"Missing template variable: {e}")

    if os.path.isabs(expanded_path):
        final_path = expanded_path
    else:
        final_path = os.path.join(base_path, expanded_path)

    final_path = str(Path(final_path))

    os.makedirs(os.path.dirname(final_path), exist_ok=True)

    return final_path
