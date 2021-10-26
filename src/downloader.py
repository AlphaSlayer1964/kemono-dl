import sys
import yt_dlp
import requests
import os
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .arguments import get_args
from .helper import win_file_name, check_size

args = get_args()

def download_yt_dlp(path, link):
    try:
        ydl_opts = {
            "outtmpl" : "{}/%(title)s.%(ext)s".format(path),
            "noplaylist" : True, # stops from downloading an entire youtube channel
            "merge_output_format" : "mp4"
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return 0
    except:
        print('Error with yt-dlp and link: {}'.format(link)) # errors always ignored
        return 1

retry_strategy = Retry(
    total=2,
    backoff_factor=60,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=False
)
adapter = HTTPAdapter(max_retries=retry_strategy)
s = requests.Session()
s.mount("https://", adapter)
s.mount("http://", adapter)

def download_file(file_name, url, file_path):
    file_name = win_file_name(file_name)
    print('Downloading: {}'.format(file_name))
    try:
        headers = {"Connection": "keep-alive"}
        with s.get(url,stream=True,cookies=args['cookies'],headers=headers) as r:
            r.raise_for_status()
            downloaded = 0
            total = int(r.headers.get('content-length', '0'))
            if not check_size(total):
                print('File size out of range: {} bytes'.format(total))
                return 0
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            with open(os.path.join(file_path, file_name), 'wb') as f:
                start = time.time()
                for chunk in r.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                    downloaded += len(chunk)
                    f.write(chunk)
                    if total:
                        done = int(50*downloaded/total)
                        sys.stdout.write('\r[{}{}] {}/{} MB, {} Mbps'.format('='*done, ' '*(50-done), round(downloaded/1000000,1), round(total/1000000,1), round(downloaded//(time.time() - start) / 100000,1)))
                        sys.stdout.flush()
                    else:
                        sys.stdout.write('\r[{}] 0.0/??? MB, 0.0 Mbps'.format('='*50))
                        sys.stdout.flush()
            sys.stdout.write('\n')
        return 0
    except Exception as e:
        print('Error downloading: {}'.format(url))
        print(e)
        if args['ignore_errors']:
            return 1
        quit()
