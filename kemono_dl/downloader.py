import sys
import time

from .session import CustomSession
from .utils import format_bytes


def download_file(session: CustomSession, url: str, filepath: str, chunk_size: int = 8192) -> None:
    print("[downloading] Source: " + url)
    print("[downloading] Destination:" + filepath)
    with session.get(url, stream=True, allow_redirects=True) as response:
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        start_time = time.time()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    elapsed = time.time() - start_time
                    speed = downloaded / elapsed if elapsed > 0 else 0
                    remaining = total_size - downloaded
                    eta = remaining / speed if speed > 0 else 0

                    percent = (downloaded / total_size) * 100
                    progress = f"[downloading] {percent:6.2f}% of {format_bytes(total_size)} eta {time.strftime('%H:%M:%S', time.gmtime(eta))} at {format_bytes(speed)}/s"
                    if sys.stdout.isatty():
                        print(progress.ljust(100), end="\r")
        print(progress.ljust(100))
