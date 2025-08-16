import hashlib
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


def get_sha256_url_content(session: Session, url: str, chunk_size: int = 8192):
    sha256 = hashlib.sha256()
    with session.get(url, stream=True) as response:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                sha256.update(chunk)
    return sha256.hexdigest()


def generate_file_path(
    base_path: str,
    output_template: str,
    template_variables: dict,
    restrict_names: bool = False,
    replacement: str = "_",
) -> str:
    def _sanitize(value: str, replace: str = "_") -> str:
        return re.sub(r'[<>:"/\\|?*\x00-\x1F]', replace, value).rstrip(" .")

    path_segments = []
    try:
        for path_segment in re.split(r"[\\/]", output_template):
            path_segment_formatted = path_segment.format_map(template_variables)
            path_segments.append(_sanitize(path_segment_formatted, replacement))
    except KeyError as e:
        missing_key = e.args[0]
        raise ValueError(f"[Error] Missing template key: '{missing_key}'.")

    path = Path(*path_segments)

    if not path.is_absolute():
        path = Path(base_path) / path

    if restrict_names:
        path = Path(re.sub(r"[^\x20-\x7E]", replacement, str(path)))

    return str(path)
