import yt_dlp
from yt_dlp import DownloadError
import requests
import os
import time

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
    except DownloadError as e:
        print('[Error] yt-dlp could not download: {}'.format(link)) # errors always ignored
        if (str(e).find('Unsupported URL:') != -1):
            return 0
        elif (str(e).find('Video unavailable') != -1):
            return 0
        # elif (str(e).find('HTTP Error 404: Not Found') != -1): # noticed an imgur link 404ed when the link still works
        #     return 0
        else:
            return 1

def download_file(file_name, url, file_path, retry = 0):
    flag_404 = 0
    file_name = win_file_name(file_name)
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    print('[Downloading] {}'.format(file_name))
    try:
        headers = {
            'Connection': 'keep-alive',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
            }
        with requests.get(url,stream=True,cookies=args['cookies'],headers=headers) as r:
            if r.status_code != 200:
                if r.status_code == 404:
                    flag_404 = 1
                raise Exception('[Error] Responce status code: {}'.format(r.status_code))
            block_size = 1024
            downloaded = 0
            total = int(r.headers.get('content-length', 0)) # this seems to happen on pdfs a lot
            if not check_size(total):
                print('File size out of range: {} bytes'.format(total))
                return 0
            with open(os.path.join(file_path, file_name), 'wb') as f:
                start = time.time()
                for chunk in r.iter_content(block_size):
                    downloaded += len(chunk)
                    f.write(chunk)
                    time_diff = 1 if time.time() - start == 0 else time.time() - start
                    dl_rate = round((downloaded/(1024*1024))/time_diff, 1)
                    if total:
                        done = int(50*downloaded/total)
                        print('[{}{}] {}/{} MB, {} MB/s'.format('='*done, ' '*(50-done), round(downloaded/(1024*1024),1), round(total/(1024*1024),1), dl_rate) + ' '*20, end='\r')
                    else:
                        print('[{}] {}/??? MB, {} MB/s'.format('='*50, round(downloaded/(1024*1024),1), dl_rate) + ' '*20, end='\r')
            print()
            if total != 0 and downloaded < total:
                raise Exception(("[Error] I don't know what causes this!"))
        return 0
    except Exception as e:
        print('[Error] downloading: {}'.format(url))
        print(e)
        if retry:
            if flag_404 == 1:
                print('[Warning] Skipping retry because responce status 404')
                return 1
            current_try = 0
            while True:
                current_try += 1
                print('[info] Retrying download in 60 seconds. ({}/{})'.format(current_try, retry))
                time.sleep(30)
                if download_file(file_name, url, file_path) == 0:
                    return 0
                if current_try >= retry:
                    return 1
        if args['ignore_errors']:
            return 1
        quit()