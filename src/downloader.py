import requests
import os
import time

from .arguments import get_args
from .helper import win_file_name, check_size, get_hash, print_info, print_error, print_warning

args = get_args()

TIMEOUT = 120
RETRY_WAIT = 30

def download_yt_dlp(path, link):
    import yt_dlp
    from yt_dlp import DownloadError
    try:
        ydl_opts = {

            "outtmpl" : "./temp/%(title)s.%(ext)s",
            "noplaylist" : True, # Actually this does not stops from downloading an entire youtube channel :/
            "merge_output_format" : "mp4",
            "quiet" : True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        # This is so jank! Needed for when file path length is to long on windows
        if len(os.listdir('./temp')) > 1:
            print_error('THIS SHOULD NEVER HAPPEN!')
            raise Exception
        if not os.path.exists(path):
            os.makedirs(path)
        for x in os.listdir('./temp'):
            if x.find('.mp4'):
                if os.path.exists(os.path.join(path,x)):
                    os.remove(os.path.join(path,x))
                os.rename(os.path.join('./temp',x),os.path.join(path,x))
        os.rmdir('./temp')
        return 0
    except (Exception, DownloadError) as e:
        print_error('yt-dlp could not download: {}'.format(link))
        if type(e) is DownloadError:
            if (str(e).find('Unsupported URL:') != -1) or (str(e).find('Video unavailable') != -1) or (str(e).find('HTTP Error 404') != -1):
                return 0
        if os.path.isdir('./temp'):
            for x in os.listdir('./temp'):
                os.remove(x)
            os.rmdir('./temp')
        print(e)
        return 1

def download_file(url, file_name, file_path, retry = None, file_hash = None):
    # correct file name
    file_name = win_file_name(file_name)
    print('[Downloading]: {}'.format(file_name))
    # check file hash
    if os.path.exists(os.path.join(file_path, file_name)) and file_hash:
        if file_hash.lower() == get_hash(os.path.join(file_path, file_name)).lower():
            print_info('Skipping download: file with matching hash already exists.')
            return 0
    try:
        # begin download
        responce =  requests.get(url,stream=True,cookies=args['cookies'], timeout=TIMEOUT)
        responce.raise_for_status()

        total = int(responce.headers.get('content-length', 0))

        if not check_size(total):
            print_info('File size out of range: {} bytes'.format(total))
            return 0

        if not os.path.exists(file_path):
            os.makedirs(file_path)

        with open(os.path.join(file_path, file_name), 'wb') as f:
            start = time.time()
            block_size = 1024
            downloaded = 0
            for chunk in responce.iter_content(block_size):
                downloaded += len(chunk)
                f.write(chunk)
                print_download_bar(total, downloaded, start)
        print()
        if total != 0 and downloaded < total:
            print_error("I don't know what causes this!")
            raise Exception

        # # logging files with broken hashes
        # if file_hash:
        #     if file_hash.lower() != get_hash(os.path.join(file_path, file_name)).lower():
        #         print_warning('File hash does not match!')
        #         with open('broken_hashes.log','w+') as f:
        #             for line in f:
        #                 if (url + '\n') in line:
        #                     break
        #             else:
        #                 f.write((url + '\n'))

        return 0
    except Exception as e:
        print_error('downloading: {}'.format(url))
        print(e)
        # delete failed file
        if os.path.exists(os.path.join(file_path, file_name)):
            os.remove(os.path.join(file_path, file_name))
        # retry logic
        if retry:
            current_try = 0
            while True:
                current_try += 1
                print_info('Retrying download in {} seconds. ({}/{})'.format(RETRY_WAIT,current_try, retry))
                time.sleep(RETRY_WAIT)
                if download_file(url, file_name, file_path, file_hash=file_hash) == 0:
                    return 0
                if current_try >= retry:
                    break
        if args['ignore_errors']:
            return 1
        quit()

def print_download_bar(total, downloaded, start):
    time_diff = 1 if time.time() - start == 0 else time.time() - start
    done = 50
    total_MB = '???'
    if total:
        done = int(50*downloaded/total)
        total_MB = round(total/(1024*1024),1)
    downloaded_MB = round(downloaded/(1024*1024),1)
    rate_MBps = round((downloaded/(1024*1024))/time_diff, 1)
    bar_fill = '='*done
    bar_empty = ' '*(50-done)
    overlap_buffer = ' '*20
    print('[{}{}] {}/{} MB, {} MB/s{}'.format(bar_fill, bar_empty, downloaded_MB, total_MB, rate_MBps, overlap_buffer), end='\r')