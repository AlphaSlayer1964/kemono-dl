import yt_dlp
import shutil
from yt_dlp import DownloadError
import os

from .logger import logger


def my_yt_dlp(url:str, file_path:str, args:dict):
    logger.info(f"Downloading with yt-dlp: URL {url}")
    temp_folder = os.path.join(os.getcwd(),"yt_dlp_temp")
    try:
        # please reffer to yt-dlp's github for options
        ydl_opts = {"paths": {"home": file_path}, "noplaylist" : True, "quiet" : True, "verbose": False}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        # clean up temp folder
        shutil.rmtree(temp_folder)
    except (Exception, DownloadError) as e:
        # clean up temp folder
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
        logger.error(f"yt-dlp: Could not download URL {url}")
        return