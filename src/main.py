import re
import requests
import os
import hashlib
import time
from bs4 import BeautifulSoup
import datetime
import json
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import yt_dlp
import shutil
from yt_dlp import DownloadError
from PIL import Image
from io import BytesIO
import platform

from .arguments import get_args
from .logger import logger

args = get_args()
OS_NAME = platform.system()
TIMEOUT = 300

class downloader:

    def __init__(self):
        # I read using a session would make things faster.
        # Does it? I have no idea and didn't google
        retries = Retry(total=6, backoff_factor=15)
        adapter = HTTPAdapter(max_retries=retries)
        self.session = requests.Session()
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        self.all_creators = []
        self.download_list = []
        self.current_post = None
        self.current_post_path = None
        self.current_post_errors = 0
        self._add_all_creators('kemono')
        self._add_all_creators('coomer')

    def _add_all_creators(self, site:str):
        headers = {'accept': 'application/json'}
        creators_api_url = f'https://{site}.party/api/creators/'
        all_creators = self.session.get(url=creators_api_url, headers=headers, timeout=TIMEOUT)
        self.all_creators += all_creators.json()

    def _get_username(self, service:str, user_id:str):
        for creator in self.all_creators:
            if creator['id'] == user_id and creator['service'] == service:
                return creator['name']
        logger.critical(f'No username found: user_id: {user_id} service: {service}')
        return None

    def add_favorite_artists(self, site:str):
        logger.info('Gathering favorite users')
        headers = {'accept': 'application/json'}
        fav_art_api_url = f'https://{site}.party/api/favorites?type=artist'
        response = self.session.get(url=fav_art_api_url, cookies=args['cookies'], headers=headers, timeout=TIMEOUT)
        if not response.ok:
            logger.warning(f'{response.status_code} {response.reason}: Could not get favorite artists: Make sure you get your cookie file while logged in')
            return
        for favorite in response.json():
            last = (datetime.datetime.now().astimezone() - datetime.timedelta(days=args['favorite_users_updated_within'])) if args['favorite_users_updated_within'] else datetime.datetime.min
            last = last.strftime(r'%a, %d %b %Y %H:%M:%S %Z')
            if self._is_update_newer(favorite['updated'], last):
                self._add_user_posts(site,favorite['service'],favorite['id'])

    def add_favorite_posts(self, site:str):
        logger.info('Gathering favorite posts')
        headers = {'accept': 'application/json'}
        fav_art_api_url = f'https://{site}.party/api/favorites?type=post'
        response = self.session.get(url=fav_art_api_url, cookies=args['cookies'], headers=headers, timeout=TIMEOUT)
        if not response.ok:
            logger.warning(f'{response.status_code} {response.reason}Could not get favorite posts: Make sure you get your cookie file while logged in')
            return
        for favorite in response.json():
            self._add_single_post(site,favorite['service'],favorite['user'],favorite['id'])

    def add_links(self, urls:list):
        if urls:
            logger.info('Gathering posts')
        for url in urls:
            self._parse_links(url)

    def _parse_links(self, url:str):
        user = re.search(r'^https://(kemono|coomer)\.party/([^/]+)/user/([^/]+)$',url)
        if user:
            self._add_user_posts(user.group(1),user.group(2),user.group(3))
            return
        post = re.search(r'^https://(kemono|coomer)\.party/([^/]+)/user/([^/]+)/post/([^/]+)$',url)
        if post:
            self._add_single_post(post.group(1),post.group(2),post.group(3),post.group(4))
            return
        logger.warning(f'Invalid URL: {url}')

    def _add_user_posts(self, site:str, service:str, user_id:str):
        username = self._get_username(service, user_id)
        if not username:
            return
        headers = {'accept': 'application/json'}
        chunk = 0
        while True:
            user_api_url = f'https://{site}.party/api/{service}/user/{user_id}?o={chunk}'
            logger.debug(f'User API URL: {user_api_url}')
            response = self.session.get(url=user_api_url, headers=headers, timeout=TIMEOUT).json()
            if not response:
                return
            for post_dict in response:
                post_dict['username'], post_dict['site'] = username, site
                post_dict['date_object'], post_dict['date_object_string'] = get_post_date(post_dict)
                if post_dict not in self.download_list:
                    self.download_list.append(post_dict)
            chunk += 25

    def _add_single_post(self, site:str, service:str, user_id:str, post_id:str):
        username = self._get_username(service, user_id)
        if not username:
            return
        headers = {'accept': 'application/json'}
        post_api_url = f'https://{site}.party/api/{service}/user/{user_id}/post/{post_id}'
        logger.debug(f'Post API URL: {post_api_url}')
        post_dict = self.session.get(url=post_api_url, headers=headers, timeout=TIMEOUT).json()[0]
        post_dict['username'], post_dict['site'] = username, site
        post_dict['date_object'], post_dict['date_object_string'] = get_post_date(post_dict)
        if post_dict not in self.download_list:
            self.download_list.append(post_dict)

    # with how slow kemono.party can be sometimes I may want to make this asynchronous
    def download_posts(self):
        unique = []
        for index, post in enumerate(self.download_list):
            logger.debug(f"Post: {index+1}/{len(self.download_list)}")
            self.current_post = post
            self._set_current_post_path()
            logger.info(f"Post: {clean_folder_name(self.current_post['title'])}")
            logger.debug(f"user_id: {self.current_post['user']} service: {self.current_post['service']} post_id: {self.current_post['id']} url: https://{self.current_post['site']}.party/{self.current_post['service']}/user/{self.current_post['user']}/post/{self.current_post['id']}")
            if self._should_download():
                logger.debug(f"Sleeping for {args['post_timeout']} seconds")
                time.sleep(args['post_timeout'])
                if not args['simulate']:
                    # so we are not downloading the icon or banner over and over
                    if not (self.current_post['service'], self.current_post['user']) in unique:
                        if args['save_icon']:
                            self._download_profile_icon()
                        if args['save_banner']:
                            self._download_profile_banner()
                        unique.append((self.current_post['service'], self.current_post['user']))
                    if not args['skip_attachments']:
                        self._download_attachments()
                    if not args['skip_content']:
                        self._download_content()
                    if not args['skip_comments']:
                        self._download_comments()
                    if not args['skip_embeds']:
                        self._download_embeds()
                    if not args['skip_json']:
                        if not os.path.exists(self.current_post_path):
                            os.makedirs(self.current_post_path)
                        # json.dump can't handle the datetime object
                        self.current_post['date_object'] = None
                        with open(os.path.join(self.current_post_path,f"{self.current_post['id']}.json"),'w') as f:
                            json.dump(self.current_post, f, indent=4, sort_keys=True)

                    # no errors must have occurred to archive post
                    if not self.current_post_errors:
                        if args['archive']:
                            with open(args['archive'],'a') as f:
                                f.write('/{service}/user/{user}/post/{id}\n'.format(**self.current_post))
                            logger.debug('Post Archived: /{service}/user/{user}/post/{id}\n'.format(**self.current_post))
                    # reset error count
                    self.current_post_errors = 0

    def _set_current_post_path(self):
        # when using win_folder_name() on the post title it may return an empty string
        # for example if the title is "???" then that will return ""
        # this could cause conflicting folder names if you don't include any other unique identifier in the folder name
        # Note: the pfp and banners are downloaded to the second from last folder
        # so you might need to change that
        self.current_post_path = os.path.join(args['output'],
                                            self.current_post['service'],
                                            clean_folder_name(f"{self.current_post['username']} [{self.current_post['user']}]"),
                                            clean_folder_name(f"[{self.current_post['date_object_string']}] [{self.current_post['id']}] {self.current_post['title']}"))

    def _should_download(self):
        # check if post has been updated
        if args['update_posts']:
            json_path = os.path.join(self.current_post_path, f"{self.current_post['id']}.json")
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    data = json.loads(f.read())
                if not self._is_update_newer(self.current_post['edited'], data['edited']):
                    return False

        # check archive fle
        if args['archive']:
            if os.path.exists(args['archive']):
                with open(args['archive'],'r') as f:
                    archived = f.read().splitlines()
                if '/{service}/user/{user}/post/{id}'.format(**self.current_post) in archived:
                    logger.info("Skipping Post: Post Archived")
                    return False

        # check if post date is in range
        if args['date'] == datetime.datetime.min and args['datebefore'] == datetime.datetime.min and args['dateafter'] == datetime.datetime.max:
            return True
        elif self.current_post['date_object'] == datetime.datetime.min:
            return False
        elif not(self.current_post['date_object'] == args['date'] or self.current_post['date_object'] <= args['datebefore'] or self.current_post['date_object'] >= args['dateafter']):
            return False
        return True

    def _is_update_newer(self, current, last = 'Mon, 01 Jan 0001 00:00:00 GMT'):
        current_dt = datetime.datetime.strptime(current, r'%a, %d %b %Y %H:%M:%S %Z') if current else datetime.datetime.min
        last_dt = datetime.datetime.strptime(last, r'%a, %d %b %Y %H:%M:%S %Z')
        if current_dt > last_dt:
            return True

    def _download_profile_icon(self):
        if self.current_post['service'] in {'dlsite'}:
            logger.warning(f"Profile icons are not supported for {self.current_post['service']} users")
            return
        pfp_banner_url = f"https://{self.current_post['site']}.party/icons/{self.current_post['service']}/{self.current_post['user']}"
        logger.debug(f"Profile icon URL {pfp_banner_url}")
        response = self.session.get(url=pfp_banner_url, cookies=args['cookies'], timeout=TIMEOUT)
        try:
            image = Image.open(BytesIO(response.content))
            if not os.path.exists(os.path.dirname(self.current_post_path)):
                os.makedirs(os.path.dirname(self.current_post_path))
            image.save(os.path.join(os.path.dirname(self.current_post_path), f"Profile_icon.{image.format.lower()}"), format=image.format)
        except:
            logger.error(f"Unable to download profile icon for {self.current_post['username']}")

    def _download_profile_banner(self):
        if self.current_post['service'] in {'gumroad','dlsite'}:
            logger.warning(f"Profile banners are not supported for {self.current_post['service']} users")
            return
        pfp_banner_url = f"https://{self.current_post['site']}.party/banners/{self.current_post['service']}/{self.current_post['user']}"
        logger.debug(f"Profile banner URL {pfp_banner_url}")
        response = self.session.get(url=pfp_banner_url, cookies=args['cookies'], timeout=TIMEOUT)
        try:
            image = Image.open(BytesIO(response.content))
            if not os.path.exists(os.path.dirname(self.current_post_path)):
                os.makedirs(os.path.dirname(self.current_post_path))
            image.save(os.path.join(os.path.dirname(self.current_post_path), f"Profile_banner.{image.format.lower()}"), format=image.format)
        except:
            logger.error(f"Unable to download profile banner for {self.current_post['username']}")

    def _download_attachments(self):
        if self.current_post['file']:
            # kemono.party some times already has the file in attachments so stops duplicates
            if not self.current_post['file'] in self.current_post['attachments']:
                self.current_post['attachments'].insert(0, self.current_post['file'])
        if self.current_post['attachments']:
            if not os.path.exists(self.current_post_path):
                os.makedirs(self.current_post_path)
        for index, attachment in enumerate(self.current_post['attachments']):
            index_string = str(index+1).zfill(len(str(len(self.current_post['attachments']))))
            file_name = os.path.join(self.current_post_path, clean_file_name(f"[{index_string}]_{attachment['name']}"))
            if args['no_indexing']:
                file_name = os.path.join(self.current_post_path, clean_file_name(f"{attachment['name']}"))
            file_url = f"https://{self.current_post['site']}.party/data{attachment['path']}?f={attachment['name']}"
            file_hash = find_hash(attachment['path'])
            self._requests_download(file_url, file_name, file_hash)

    def _download_content(self):
        if self.current_post['content']:
            if not os.path.exists(self.current_post_path):
                os.makedirs(self.current_post_path)
            content_soup = self._save_inline(BeautifulSoup(self.current_post['content'], 'html.parser'))
            if args['extract_links']:
               self._save_links(content_soup)
            with open(os.path.join(self.current_post_path, 'content.html'),'wb') as f:
                f.write(content_soup.prettify().encode("utf-16"))

    def _save_inline(self, soup):
        # do these have hashes?
        inline_images = soup.find_all('img')
        for index, inline_image in enumerate(inline_images):
            party_hosted = re.search('^/[^*]+', inline_image['src'])
            if party_hosted:
                if not os.path.exists(os.path.join(self.current_post_path, 'inline')):
                    os.makedirs(os.path.join(self.current_post_path, 'inline'))
                index_string = str(index).zfill(len(str(len(inline_images))))
                file_name = os.path.join(self.current_post_path, 'inline', f"[{index_string}]_{inline_image['src'].split('/')[-1]}")
                file_url = f"https://{self.current_post['site']}.party/data{inline_image['src']}"
                self._requests_download(file_url, file_name)
                inline_image['src'] = os.path.join(self.current_post_path, 'inline', file_name)
        return soup

    def _save_links(self, soup):
        href_tags = soup.find_all(href=True)
        if href_tags:
            with open(os.path.join(self.current_post_path,'content_links.txt'),'w') as f:
                for href_tag in href_tags:
                    f.write(href_tag['href'] + '\n')

    def _download_comments(self):
        # no api method to get comments so using from html (not future proof)
        post_url = "https://{site}.party/{service}/user/{user}/post/{id}".format(**self.current_post)
        response = self.session.get(url=post_url, allow_redirects=True, cookies=args['cookies'], timeout=TIMEOUT)
        page_soup = BeautifulSoup(response.text, 'html.parser')
        comment_html = page_soup.find("div", {"class": "post__comments"})
        if comment_html:
            do_not_save = re.search('([^ ]+ does not support comment scraping yet\.|No comments found for this post\.)',comment_html.text)
            if do_not_save:
                logger.debug(do_not_save.group(1))
            else:
                if not os.path.exists(self.current_post_path):
                    os.makedirs(self.current_post_path)
                with open(os.path.join(self.current_post_path, 'comments.html'),'wb') as f:
                    f.write(comment_html.prettify().encode("utf-16"))

    def _download_embeds(self):
        if self.current_post['embed']:
            if not os.path.exists(self.current_post_path):
                os.makedirs(self.current_post_path)
            with open(os.path.join(self.current_post_path, 'embed.txt'),'wb') as f:
                f.write("{subject}\n{url}\n{description}".format(**self.current_post['embed']).encode('utf-16'))
            if args['yt_dlp']:
                self.download_yt_dlp(self.current_post['embed']['url'], os.path.join(self.current_post_path, 'embed'))

    def _requests_download(self, url:str, file_name:str, file_hash:str = None, retry:int = args['retry_download']):
        logger.debug(f"Preparing download: File Name: {os.path.split(file_name)[1]} URL: {url}")

        # check file extention
        if check_file_extention(os.path.split(file_name)[1]):
            logger.info(f"Skipping download: File extention not supported {os.path.split(file_name)[1].split('.')[-1]}")
            return

        logger.info(f"Downloading {os.path.split(file_name)[1]}")

        # check if file exists and if hashes match
        if os.path.exists(file_name) and file_hash:
            if file_hash.lower() == get_hash(file_name).lower():
                logger.info("Skipping download: File on disk has matching hash")
                return
            logger.warning(f"Resuming download: File on disk does not match hash")
            logger.debug(f"Local Hash: {get_hash(file_name).lower()} Server Hash: {file_hash.lower()}")

        resume_size = os.path.getsize(file_name) if os.path.exists(file_name) else 0

        headers = {'Accept-Encoding': None,
                   'Range': f'bytes={resume_size}-',
                   'User-Agent': args['user_agent']}

        response = self.session.get(url=url, stream=True, headers=headers, cookies=args['cookies'], timeout=TIMEOUT)

        # do not retry on a 404
        if response.status_code == 404:
            logger.error(f'{response.status_code} {response.reason}: URL {url}')
            self.current_post_errors += 1
            return

        # do not retry on a 403. Bad cookies
        if response.status_code == 403:
            logger.error(f"{response.status_code} {response.reason}: Update cookie file and re-run script")
            self.current_post_errors += 1
            return

        # do not retry on a 416 Range Not Satisfiable
        # means the requested range is >= the total content-length
        # when kemono.party finishes fixing their bd this will need to cause the file to redwonload
        if response.status_code == 416:
            logger.error(f'{response.status_code} {response.reason}: Will always happen if server hash is wrong! Please check file and report to site owner that file hash might be wrong')
            self.current_post_errors += 1
            return

        # retry download if status code is not ok
        if not response.ok:
            timeout = 30
            # 429 Too many requests
            # wait 5 minutes
            if response.status_code == 429:
                timeout = 300
            if retry > 0:
                logger.warning(f"{response.status_code} {response.reason}: Retrying in {timeout} seconds")
                time.sleep(timeout)
                self._requests_download(url=url, file_name=file_name, file_hash=file_hash, retry=retry-1)
                return
            logger.critical(f"All retries failed: {response.status_code} {response.reason}")
            self.current_post_errors += 1
            return

        # get content-length or get 0
        total = int(response.headers.get('content-length', 0))
        if total > 0:
            # if resuming download correct loading bar
            total += resume_size

        # check file content length
        if check_file_size(total):
            logger.info(f"Skipping download: Does not meat file size requirements: {total} bytes")
            return

        # writing response content to file
        with open(file_name, 'ab') as f:
            start = time.time()
            downloaded = resume_size
            for chunk in response.iter_content(chunk_size=1024*1024):
                downloaded += len(chunk)
                f.write(chunk)
                print_download_bar(total, downloaded, resume_size, start)
        print()

        # My futile attempts to check if the file downloaded correctly
        if os.path.exists(file_name) and file_hash:
            if file_hash.lower() == get_hash(file_name).lower():
                logger.debug("Download completed successfully")
                return
            # if hashes don't match retry download
            if retry > 0:
                timeout = 5
                logger.error(f"Download failed / was intertupted: File hash does not match: Retrying in {timeout} seconds")
                logger.debug(f"Local Hash: {get_hash(file_name).lower()} Server Hash: {file_hash.lower()}")
                time.sleep(timeout)
                self._requests_download(url=url, file_name=file_name, file_hash=file_hash, retry=retry-1)
                return
            logger.critical(f"All retries failed: Server hash is wrong or server keeps timing out: This is a problem on the sites end: Please report broken hashed files to them: URL {url}")
            self.current_post_errors += 1
            return

    def download_yt_dlp(self, url:str, file_path:str):
        logger.info(f"Downloading with yt-dlp: URL {url}")
        temp_folder = os.path.join(os.getcwd(),"yt_dlp_temp")
        try:
            # please reffer to yt-dlp's github for options
            ydl_opts = {
                "paths": {"temp" : temp_folder, "home": f"{file_path}"},
                # "output": '%(title)s.%(ext)s',
                "noplaylist" : True,
                # "merge_output_format" : "mp4",
                "quiet" : True,
                "verbose": False
            }
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

# Helper functions

# return hash from download url
def find_hash(url:str):
    find_hash = re.search(r'^([a-z0-9]{64})$',url.split('/')[-1].split('.')[0])
    if find_hash:
        return find_hash.group(1)
    return None

# return hash from file
def get_hash(file_name):
    sha256_hash = hashlib.sha256()
    with open(file_name,"rb") as f:
        for byte_block in iter(lambda: f.read(4096),b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()

# prints the stupid pointless download bar that took way to long to make
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

    if (not args['quiet']) or args['verbose']:
        print(f'[{bar_fill}{bar_empty}] {downloaded}/{total[0]} {total[1]} at {rate[0]} {rate[1]}/s ETA {eta}{overlap_buffer}', end='\r')

def clean_file_name(string:str):
    if args['restrict_names']:
        string = restrict_names(string)
    # if OS_NAME == 'Windows':
    return re.sub(r'[\\/:\"*?<>|\n\t]','_',string)[:255]

def clean_folder_name(string:str):
    if args['restrict_names']:
        string = restrict_names(string)
    # if OS_NAME == 'Windows':
    return re.sub(r'[\\/:\"*?<>|\n\t]','_',string)[:248].rstrip('. ')

# returns string replacing non ascii characters, spaces, and "&"
def restrict_names(string:str):
    return re.sub(r'[^\x00-\x7f]|[ &]','_',string)

# takes post date sting and converts it back to datetime object, and simple datetime string
def get_post_date(post:dict):
    if post['published']:
        date_object = datetime.datetime.strptime(post['published'], r'%a, %d %b %Y %H:%M:%S %Z')
        date_string = date_object.strftime(r'%Y%m%d')
    else:
        date_object = datetime.datetime.min
        date_string = '00000000'
    return (date_object, date_string)

# check if a number is between two values
def check_file_size(size):
    if args['min_filesize'] == '0' and args['max_filesize'] == 'inf':
        return False
    elif size == 0:
        return True
    elif int(size) <= float(args['max_filesize']) and int(size) >= int(args['min_filesize']):
        return False
    return True

# check file extention
def check_file_extention(file_name):
    file_extention = file_name.split('.')[-1]
    if args['only_filetypes']:
        if not file_extention.lower() in args['only_filetypes']:
            return True
    if args['skip_filetypes']:
        if file_extention.lower() in args['skip_filetypes']:
            return True
    return False

def main():
    start = time.time()
    D = downloader()
    urls = []
    for link in args['links']:
        urls.append(link)
    for link in args['fromfile']:
        urls.append(link)
    D.add_links(urls)
    if args['kemono_favorite_users']:
        D.add_favorite_artists('kemono')
    if args['kemono_favorite_posts']:
        D.add_favorite_posts('kemono')
    if args['coomer_favorite_users']:
        D.add_favorite_artists('coomer')
    if args['coomer_favorite_posts']:
        D.add_favorite_posts('coomer')
    D.download_posts()
    final_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - start))
    logger.debug(f"Completed in {final_time}")
    logger.info("Completed")