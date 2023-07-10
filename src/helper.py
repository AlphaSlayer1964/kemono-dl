import re
import hashlib
import os
import time
import requests
from urllib.parse import urlparse

def parse_url(url):
    # parse urls
    downloadable = re.search(r'^https://((?:kemono|coomer)\.(?:party|su))/([^/]+)/user/([^/]+)($|/post/([^/]+)$)',url)
    if not downloadable:
        return None
    return downloadable.group(1)

# create path from template pattern
def compile_post_path(post_variables, template, ascii):
    drive, tail = os.path.splitdrive(template)
    tail = tail[1:] if tail[0] in {'/','\\'} else tail
    tail_split = re.split(r'\\|/', tail)
    cleaned_path = drive + os.path.sep if drive else ''
    for folder in tail_split:
        if ascii:
            cleaned_path = os.path.join(cleaned_path, restrict_ascii(clean_folder_name(folder.format(**post_variables))))
        else:
            cleaned_path = os.path.join(cleaned_path, clean_folder_name(folder.format(**post_variables)))
    return cleaned_path

# create file path from template pattern
def compile_file_path(post_path, post_variables, file_variables, template, ascii):
    file_split = re.split(r'\\|/', template)
    if len(file_split) > 1:
        for folder in file_split[:-1]:
            if ascii:
                post_path = os.path.join(post_path, restrict_ascii(clean_folder_name(folder.format(**file_variables, **post_variables))))
            else:
                post_path = os.path.join(post_path, clean_folder_name(folder.format(**file_variables, **post_variables)))
    if ascii:
        cleaned_file = restrict_ascii(clean_file_name(file_split[-1].format(**file_variables, **post_variables)))
    else:
        cleaned_file = clean_file_name(file_split[-1].format(**file_variables, **post_variables))
    return os.path.join(post_path, cleaned_file)

# get file hash
def get_file_hash(file:str):
    sha256_hash = hashlib.sha256()
    with open(file,"rb") as f:
        for byte_block in iter(lambda: f.read(4096),b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest().lower()

# clean folder name for windows
def clean_folder_name(folder_name:str):
    if not folder_name.rstrip():
        folder_name = '_'
    return re.sub(r'[\x00-\x1f\\/:\"*?<>\|]|\.$','_',folder_name.rstrip())[:248]

# clean file name for windows
def clean_file_name(file_name:str):
    if not file_name:
        file_name = '_'
    file_name = re.sub(r'[\x00-\x1f\\/:\"*?<>\|]','_', file_name)
    file_name, file_extension = os.path.splitext(file_name)
    return file_name[:255-len(file_extension)-5] + file_extension

def restrict_ascii(string:str):
    return re.sub(r'[^\x21-\x7f]','_',string)

def check_date(post_date, date, datebefore, dateafter):
    if date:
        if date == post_date:
            return False
    if datebefore and dateafter:
        if dateafter <= post_date <= datebefore:
            return False
    elif datebefore:
        if datebefore >= post_date:
            return False
    elif dateafter:
        if dateafter <= post_date:
            return False
    return True

# prints download bar
def print_download_bar(total:int, downloaded:int, resumed:int, start):
    time_diff = time.time() - start
    if time_diff == 0.0:
        time_diff = 0.000001
    done = 50

    rate = (downloaded-resumed)/time_diff

    eta = time.strftime("%H:%M:%S", time.gmtime((total-downloaded) / rate))

    if rate/2**10 < 100:
        rate = (round(rate/2**10, 1), 'KB')
    elif rate/2**20 < 100:
        rate = (round(rate/2**20, 1), 'MB')
    else:
        rate = (round(rate/2**30, 1), 'GB')

    if total:
        done = int(50*downloaded/total)
        if total/2**10 < 100:
            total = (round(total/2**10, 1), 'KB')
            downloaded = round(downloaded/2**10,1)
        elif total/2**20 < 100:
            total = (round(total/2**20, 1), 'MB')
            downloaded = round(downloaded/2**20,1)
        else:
            total = (round(total/2**30, 1), 'GB')
            downloaded = round(downloaded/2**30,1)
    else:
        if downloaded/2**10 < 100:
            total = ('???', 'KB')
            downloaded = round(downloaded/2**10,1)
        elif downloaded/2**20 < 100:
            total = ('???', 'MB')
            downloaded = round(downloaded/2**20,1)
        else:
            total = ('???', 'GB')
            downloaded = round(downloaded/2**30,1)

    bar_fill = '='*done
    bar_empty = ' '*(50-done)
    overlap_buffer = ' '*15
    print(f'[{bar_fill}{bar_empty}] {downloaded}/{total[0]} {total[1]} at {rate[0]} {rate[1]}/s ETA {eta}{overlap_buffer}', end='\r')

# redo this
# def check_version():
#     try:
#         current_version = datetime.datetime.strptime(__version__, r'%Y.%m.%d')
#     except:
#         current_version = datetime.datetime.strptime(__version__, r'%Y.%m.%d.%H')
#     github_api_url = 'https://api.github.com/repos/AplhaSlayer1964/kemono-dl/releases/latest'
#     try:
#         latest_tag = requests.get(url=github_api_url, timeout=300).json()['tag_name']
#     except:
#         logger.error("Failed to check latest version of kemono-dl")
#         return
#     try:
#         latest_version = datetime.datetime.strptime(latest_tag, r'%Y.%m.%d')
#     except:
#         latest_version = datetime.datetime.strptime(latest_tag, r'%Y.%m.%d.%H')
#     if current_version < latest_version:
#         logger.debug(f"Using kemono-dl {__version__} while latest release is kemono-dl {latest_tag}")
#         logger.warning(f"A newer version of kemono-dl is available. Please update to the latest release at https://github.com/AplhaSlayer1964/kemono-dl/releases/latest")

class RefererSession(requests.Session):
    def rebuild_auth(self, prepared_request, response):
        super().rebuild_auth(prepared_request, response)
        u = urlparse(response.url)
        prepared_request.headers["Referer"] = f'{u.scheme}://{u.netloc}/'