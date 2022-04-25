import requests
from requests.adapters import HTTPAdapter, Retry
import re
import os
from bs4 import BeautifulSoup
import time
import datetime
from PIL import Image
from io import BytesIO
import json

from .args import get_args
from .logger import logger
from .version import __version__
from .helper import get_file_hash, print_download_bar, check_date, parse_url, compile_post_path, compile_file_path
from .my_yt_dlp import my_yt_dlp

class downloader:

    def __init__(self, args):
        self.input_urls = args['links'] + args['from_file']
        # list of completed posts from current session
        self.comp_posts = []
        # list of creators info
        self.creators = []

        # requests variables
        self.headers = {'User-Agent': args['user_agent']}
        self.cookies = args['cookies']
        self.timeout = 300

        # file/folder naming
        self.download_path_template = args['dirname_pattern']
        self.filename_template = args['filename_pattern']
        self.inline_filename_template = args['inline_filename_pattern']
        self.other_filename_template = args['other_filename_pattern']
        self.user_filename_template = args['user_filename_pattern']
        self.date_strf_pattern = args['date_strf_pattern']
        self.yt_dlp_args = args['yt_dlp_args']
        self.restrict_ascii = args['restrict_names']

        self.archive_file = args['archive']
        self.archive_list = []
        self.post_errors = 0

        # controls what to download/save
        self.attachments = not args['skip_attachments']
        self.inline = args['inline']
        self.content = args['content']
        self.extract_links = args['extract_links']
        self.comments = args['comments']
        self.json = args['json']
        self.yt_dlp = args['yt_dlp']
        self.files = (not args['skip_attachments']) or args['inline']
        self.k_fav_posts = args['kemono_fav_posts']
        self.c_fav_posts = args['coomer_fav_posts']
        self.k_fav_users = args['kemono_fav_users']
        self.c_fav_users = args['coomer_fav_users']
        self.icon_banner = []
        if args['icon']:
            self.icon_banner.append('icon')
        if args['banner']:
            self.icon_banner.append('banner')
        self.dms = args['dms']

        # controls files to ignore
        self.overwrite = args['overwrite']
        self.only_ext = args['only_filetypes']
        self.not_ext = args['skip_filetypes']
        self.max_size = args['max_filesize']
        self.min_size = args['min_filesize']

        # controlls posts to ignore
        self.date = args['date']
        self.datebefore = args['datebefore']
        self.dateafter = args['dateafter']
        self.user_up_datebefore = args['user_updated_datebefore']
        self.user_up_dateafter = args['user_updated_dateafter']

        # other
        self.retry = args['retry']
        self.no_part = args['no_part_files']
        self.ratelimit_sleep = args['ratelimit_sleep']
        self.post_timeout = args['post_timeout']
        self.simulate = args['simulate']

        self.session = requests.Session()
        retries = Retry(
            total=self.retry,
            backoff_factor=0.1,
            status_forcelist=[ 429, 500, 502, 503, 504 ]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.mount('http://', HTTPAdapter(max_retries=retries))

        self.start_download()

    def get_creators(self, domain:str):
        # get site creators
        creators_api = f"https://{domain}/api/creators/"
        logger.debug(f"Getting creator json from {creators_api}")
        return self.session.get(url=creators_api, cookies=self.cookies, headers=self.headers, timeout=self.timeout).json()

    def get_user(self, user_id:str, service:str):
        for creator in self.creators:
            if creator['id'] == user_id and creator['service'] == service:
                return creator
        return None

    def get_favorites(self, domain:str, fav_type:str, services:list = None, retry:int = 3):
        fav_api = f'https://{domain}/api/favorites?type={fav_type}'
        logger.debug(f"Getting favorite json from {fav_api}")
        response = self.session.get(url=fav_api, headers=self.headers, cookies=self.cookies, timeout=self.timeout)
        if response.status_code == 401:
            logger.error(f"{response.status_code} {response.reason} | Bad cookie file")
            return
        if not response.ok:
            logger.error(f"{response.status_code} {response.reason}")
            return
        for favorite in response.json():
            if fav_type == 'post':
                self.get_post(f"https://{domain}/{favorite['service']}/user/{favorite['user']}/post/{favorite['id']}")
            if fav_type == 'artist':
                if not (favorite['service'] in services or 'all' in services):
                    logger.info(f"Skipping user {favorite['name']} | Service {favorite['service']} was not requested")
                    continue
                self.get_post(f"https://{domain}/{favorite['service']}/user/{favorite['id']}")

    def get_post(self, url:str):
        found = re.search(r'(https://(kemono\.party|coomer\.party)/)(([^/]+)/user/([^/]+)($|/post/[^/]+))', url)
        if not found:
            logger.error(f"Unable to find url parameters for {url}")
            return
        api = f"{found.group(1)}api/{found.group(3)}"
        site = found.group(2)
        service = found.group(4)
        user_id = found.group(5)
        is_post = found.group(6)
        user = self.get_user(user_id, service)
        if not user:
            logger.error(f"Unable to find user info in creators list | service:{service} user_id:{user_id}")
            return
        if not is_post:
            if self.skip_user(user):
                return
        chunk = 0
        first = True
        while True:
            if is_post:
                logger.debug(f"Requesting post json from: {api}")
                json = self.session.get(url=api, cookies=self.cookies, headers=self.headers, timeout=self.timeout).json()
            else:
                logger.debug(f"Requesting user json from: {api}?o={chunk}")
                json = self.session.get(url=f"{api}?o={chunk}", cookies=self.cookies, headers=self.headers, timeout=self.timeout).json()
            if not json:
                if is_post:
                    logger.error(f"Unable to find post json for {api}")
                elif chunk == 0:
                    logger.error(f"Unable to find user json for {api}?o={chunk}")
                return # completed
            for post in json:
                post = self.clean_post(post, user, site)
                # only download once
                if not is_post and first:
                    self.download_icon_banner(post, self.icon_banner)
                    self.write_dms(post)
                    first = False
                if self.skip_post(post):
                    continue
                try:
                    self.download_post(post)
                    if self.post_timeout:
                        logger.info(f"Sleeping for {self.post_timeout} seconds.")
                        time.sleep(self.post_timeout)
                except:
                    logger.exception("Unable to download post | service:{service} user_id:{user_id} post_id:{id}".format(**post['post_variables']))
                self.comp_posts.append("https://{site}/{service}/user/{user_id}/post/{id}".format(**post['post_variables']))
            if len(json) < 25:
                return # completed
            chunk += 25

    def skip_user(self, user:dict):
        # check last update date
        if check_date(datetime.datetime.strptime(user['updated'], r'%a, %d %b %Y %H:%M:%S %Z'), None, self.user_up_datebefore, self.user_up_dateafter):
            logger.info("Skipping user | user updated date not in range")
            return True
        return False

    def skip_post(self, post:dict):
        # check if the post should be downloaded
        if self.check_archive(post):
            logger.info("Skipping post | post already archived")
            return True

        if check_date(datetime.datetime.strptime(post['post_variables']['published'], self.date_strf_pattern), self.date, self.datebefore, self.dateafter):
            logger.info("Skipping post | post published date not in range")
            return True

        if "https://{site}/{service}/user/{user_id}/post/{id}".format(**post['post_variables']) in self.comp_posts:
            logger.info("Skipping post | post was already downloaded this session")
            return True

        return False

    def download_icon_banner(self, post:dict, img_types:list):
        for img_type in img_types:
            if post['post_variables']['service'] in {'dlsite'}:
                logger.warning(f"Profile {img_type}s are not supported for {post['post_variables']['service']} users")
                return
            if post['post_variables']['service'] in {'gumroad'} and img_type == 'banner':
                logger.warning(f"Profile {img_type}s are not supported for {post['post_variables']['service']} users")
                return
            image_url = "https://{site}/{img_type}s/{service}/{user_id}".format(img_type=img_type, **post['post_variables'])
            response = self.session.get(url=image_url,headers=self.headers, cookies=self.cookies, timeout=self.timeout)
            try:
                image = Image.open(BytesIO(response.content))
                file_variables = {
                    'filename':img_type,
                    'ext':image.format.lower()
                }
                file_path = compile_file_path(post['post_path'], post['post_variables'], file_variables, self.user_filename_template, self.restrict_ascii)
                logger.info(f"Downloading {img_type}: {file_path}")
                if os.path.exists(file_path):
                    logger.info("Skipping download | File already exists")
                    return
                if not self.simulate:
                    if not os.path.exists(os.path.split(file_path)[0]):
                        os.makedirs(os.path.split(file_path)[0])
                    image.save(file_path, format=image.format)
            except:
                logger.error(f"Unable to download profile {img_type} for {post['post_variables']['username']}")

    def write_dms(self, post:dict):
        if self.dms:
            # no api method to get comments so using from html (not future proof)
            post_url = "https://{site}/{service}/user/{user_id}/dms".format(**post['post_variables'])
            response = self.session.get(url=post_url, allow_redirects=True, headers=self.headers, cookies=self.cookies, timeout=self.timeout)
            page_soup = BeautifulSoup(response.text, 'html.parser')
            if page_soup.find("div", {"class": "no-results"}):
                logger.info("No DMs found for https://{site}/{service}/user/{user_id}".format(**post['post_variables']))
                return
            dms_soup = page_soup.find("div", {"class": "card-list__items"})
            file_variables = {
                'filename':'direct messages',
                'ext':'html'
            }
            file_path = compile_file_path(post['post_path'], post['post_variables'], file_variables, self.user_filename_template, self.restrict_ascii)
            self.write_to_file(file_path, dms_soup.prettify(), 'direct messages')

    def get_inline_images(self, new_post, content_html):
        content_soup = BeautifulSoup(content_html, 'html.parser')
        if self.inline:
            # only get images that are hosted by the .party site
            inline_images = [inline_image for inline_image in content_soup.find_all("img") if inline_image['src'][0] == '/']
            for index, inline_image in enumerate(inline_images):
                file = {}
                filename, file_extension = os.path.splitext(inline_image['src'].rsplit('/')[-1])
                m = re.search(r'[a-zA-Z0-9]{64}', inline_image['src'])
                file_hash = m.group(0) if m else None
                file['file_variables'] = {
                    'filename': filename,
                    'ext': file_extension[1:],
                    'url': f"https://{new_post['post_variables']['site']}/data{inline_image['src']}",
                    'hash': file_hash,
                    'index': f"{index + 1}".zfill(len(str(len(inline_images))))
                }
                file['file_path'] = compile_file_path(new_post['post_path'], new_post['post_variables'], file['file_variables'], self.inline_filename_template, self.restrict_ascii)
                # set local image location in html
                inline_image['src'] = file['file_path']
                new_post['inline_images'].append(file)
        return content_soup

    def compile_content_links(self, new_post, content_soup):
        if self.extract_links:
            href_links = content_soup.find_all(href=True)
            new_post['links']['text'] = ''
            for href_link in href_links:
                new_post['links']['text'] += f"{href_link['href']}\n"
            new_post['links']['file_variables'] = {
                'filename':'links',
                'ext':'txt'
            }
            new_post['links']['file_path'] = compile_file_path(new_post['post_path'], new_post['post_variables'], new_post['links']['file_variables'], self.other_filename_template, self.restrict_ascii)

    def get_comments(self, post_variables:dict):
        if self.comments:
            try:
                # no api method to get comments so using from html (not future proof)
                post_url = "https://{site}/{service}/user/{user_id}/post/{id}".format(**post_variables)
                response = self.session.get(url=post_url, allow_redirects=True, headers=self.headers, cookies=self.cookies, timeout=self.timeout)
                page_soup = BeautifulSoup(response.text, 'html.parser')
                comment_soup = page_soup.find("div", {"class": "post__comments"})
                no_comments = re.search('([^ ]+ does not support comment scraping yet\.|No comments found for this post\.)',comment_soup.text)
                if no_comments:
                    logger.debug(no_comments.group(1).strip())
                    return ''
                return comment_soup.prettify()
            except:
                self.post_errors += 1
                logger.exception("Failed to get post comments")
        return ''

    def compile_post_content(self, new_post, content_soup, comment_soup, embed):
        if (self.content or self.comments) and (content_soup or comment_soup or embed):
            new_post['content']['text'] = f"{content_soup}\n{embed}\n{comment_soup}"
            new_post['content']['file_variables'] = {
                'filename':'content',
                'ext':'html'
            }
            new_post['content']['file_path'] = compile_file_path(new_post['post_path'], new_post['post_variables'], new_post['content']['file_variables'], self.other_filename_template, self.restrict_ascii)

    def clean_post(self, post:dict, user:dict, domain:str):
        new_post = {}
        # set post variables
        new_post['post_variables'] = {}
        new_post['post_variables']['title'] = post['title']
        new_post['post_variables']['id'] = post['id']
        new_post['post_variables']['user_id'] = post['user']
        new_post['post_variables']['username'] = user['name']
        new_post['post_variables']['site'] = domain
        new_post['post_variables']['service'] = post['service']
        new_post['post_variables']['added'] = datetime.datetime.strptime(post['added'], r'%a, %d %b %Y %H:%M:%S %Z').strftime(self.date_strf_pattern) if post['added'] else None
        new_post['post_variables']['updated'] = datetime.datetime.strptime(post['edited'], r'%a, %d %b %Y %H:%M:%S %Z').strftime(self.date_strf_pattern) if post['edited'] else None
        new_post['post_variables']['user_updated'] = datetime.datetime.strptime(user['updated'], r'%a, %d %b %Y %H:%M:%S %Z').strftime(self.date_strf_pattern) if user['updated'] else None
        new_post['post_variables']['published'] = datetime.datetime.strptime(post['published'], r'%a, %d %b %Y %H:%M:%S %Z').strftime(self.date_strf_pattern) if post['published'] else None

        new_post['post_path'] = compile_post_path(new_post['post_variables'], self.download_path_template, self.restrict_ascii)

        new_post['attachments'] = []
        if self.attachments:
            # add post file to front of attachments list if it doesn't already exist
            if post['file'] and not post['file'] in post['attachments']:
                post['attachments'].insert(0, post['file'])
            # loop over attachments and set file variables
            for index, attachment in enumerate(post['attachments']):
                file = {}
                filename, file_extension = os.path.splitext(attachment['name'])
                m = re.search(r'[a-zA-Z0-9]{64}', attachment['path'])
                file_hash = m.group(0) if m else None
                file['file_variables'] = {
                    'filename': filename,
                    'ext': file_extension[1:],
                    'url': f"https://{domain}/data{attachment['path']}?f={attachment['name']}",
                    'hash': file_hash,
                    'index': f"{index + 1}".zfill(len(str(len(post['attachments']))))
                }
                file['file_path'] = compile_file_path(new_post['post_path'], new_post['post_variables'], file['file_variables'], self.filename_template, self.restrict_ascii)
                new_post['attachments'].append(file)

        new_post['inline_images'] = []
        content_soup = self.get_inline_images(new_post, post['content'])

        new_post['links'] = {'text':None,'file_variables':None, 'file_path':None}
        self.compile_content_links(new_post, content_soup)

        comment_soup = self.get_comments(new_post['post_variables'])

        new_post['content'] = {'text':None,'file_variables':None, 'file_path':None}
        embed = "{subject}\n{url}\n{description}".format(**post['embed']) if post['embed'] else ''
        self.compile_post_content(new_post, content_soup.prettify(), comment_soup, embed)

        return new_post

    def download_post(self, post:dict):
        logger.info("Starting Post | {title}".format(**post['post_variables']))
        logger.debug("Post URL: https://{site}/{service}/user/{user_id}/post/{id}".format(**post['post_variables']))
        self.download_attachments(post)
        self.download_inline(post)
        self.write_content(post)
        self.write_links(post)
        self.write_json(post)
        self.download_yt_dlp(post)
        self.write_archive(post)
        self.post_errors = 0

    def download_attachments(self, post:dict):
        # download the post attachments
        for file in post['attachments']:
            try:
                self.download_file(file, retry=self.retry)
            except:
                self.post_errors += 1
                logger.exception(f"Failed to download {file['file_path']}")

    def download_inline(self, post:dict):
        # download the post inline files
        for file in post['inline_images']:
            try:
                self.download_file(file, retry=self.retry)
            except:
                self.post_errors += 1
                logger.exception(f"Failed to download {file['file_path']}")

    def write_content(self, post:dict):
        # write post content
        if post['content']['text']:
            try:
                self.write_to_file(post['content']['file_path'], post['content']['text'], 'content')
            except:
                self.post_errors += 1
                logger.exception(f"Failed to save content")

    def write_links(self, post:dict):
        # Write post content links
        if post['links']['text']:
            try:
                self.write_to_file(post['links']['file_path'], post['links']['text'], 'content links')
            except:
                self.post_errors += 1
                logger.exception(f"Failed to save content links")

    def write_json(self, post:dict):
        if self.json:
            try:
                file_variables = {
                    'filename':'json',
                    'ext':'json'
                }
                file_path = compile_file_path(post['post_path'], post['post_variables'], file_variables, self.other_filename_template, self.restrict_ascii)
                self.write_to_file(file_path, post, 'json')
            except:
                self.post_errors += 1
                logger.exception(f"Failed to save json")

    def write_to_file(self, file_path, file_content, file_type):
            # check if file exists and if should overwrite
            if os.path.exists(file_path) and not self.overwrite:
                logger.info(f"Skipping writing {file_type} | File already exists")
                return
            logger.info(f"Writing {file_type} to file")
            logger.debug(f"Writing {file_type} to: {file_path}")
            if not self.simulate:
                # create folder path if it doesn't exist
                if not os.path.exists(os.path.split(file_path)[0]):
                    os.makedirs(os.path.split(file_path)[0])
                # write to file
                if file_type == 'json':
                    with open(file_path,'w') as f:
                        json.dump(file_content, f, indent=4, sort_keys=True)
                else:
                    with open(file_path,'wb') as f:
                        f.write(file_content.encode("utf-16"))

    def skip_file(self, file:dict):
        # check if file exists
        if not self.overwrite:
            if os.path.exists(file['file_path']):
                logger.info(f"Skipping download | File already exists")
                return True

        # check file name extention
        if self.only_ext:
            if not file['file_variables']['ext'].lower() in self.only_ext:
                logger.info(f"Skipping download | File extention {file['file_variables']['ext']} not found in include list {self.only_ext}")
                return True
        if self.not_ext:
            if file['file_variables']['ext'].lower() in self.not_ext:
                logger.info(f"Skipping download | File extention {file['file_variables']['ext']} found in exclude list {self.not_ext}")
                return True

        # check file size
        if self.min_size or self.max_size:
            file_size = requests.get(file['file_variables']['url'], cookies=self.cookies, stream=True).headers.get('content-length', 0)
            if int(file_size) == 0:
                    logger.info(f"Skipping download | File size not included in file header")
                    return True
            if self.min_size and self.max_size:
                if not (self.min_size <= int(file_size) <= self.max_size):
                    logger.info(f"Skipping download | File size in bytes {file_size} was not between {self.min_size} and {self.max_size}")
                    return True
            elif self.min_size:
                if not (self.min_size <= int(file_size)):
                    logger.info(f"Skipping download | File size in bytes {file_size} was not >= {self.min_size}")
                    return True
            elif self.max_size:
                if not (int(file_size) <= self.max_size):
                    logger.info(f"Skipping download | File size in bytes {file_size} was not <= {self.max_size}")
                    return True
        return False

    def download_file(self, file:dict, retry:int):
        # download a file
        if self.files:
            if self.skip_file(file):
                return
            logger.info(f"Downloading: {os.path.split(file['file_path'])[1]}")
            logger.debug(f"Downloading from: {file['file_variables']['url']}")
            part_file = f"{file['file_path']}.part" if not self.no_part else file['file_path']
            logger.debug(f"Downloading to: {part_file}")

            # try to resume part files
            resume_size = 0
            if os.path.exists(part_file) and not self.overwrite:
                resume_size = os.path.getsize(part_file)
                logger.info("Trying to resuming partial download | Resume size: {resume_size} bytes")

            self.headers['Range'] = f"bytes={resume_size}-"

            try:
                response = self.session.get(url=file['file_variables']['url'], stream=True, headers=self.headers, cookies=self.cookies, timeout=self.timeout)
            except:
                logger.exception(f"Failed to download {os.path.split(file['file_path'])[1]} | Retrying download")
                if retry > 0:
                    self.download_file(file, retry=retry-1)
                    return
                raise Exception(f"All retries failed!")

            if response.status_code == 404:
                # doesn't exist
                raise Exception(f"{response.status_code} {response.reason}")
            if response.status_code == 403:
                # ddos guard
                raise Exception(f"{response.status_code} {response.reason} | Bad cookies")
            if response.status_code == 416:
                # bad request range
                raise Exception(f"{response.status_code} {response.reason} | Bad server file hash!")
            if response.status_code == 429:
                # ratelimit
                logger.warning(f"{response.status_code} {response.reason} | Retrying download in {self.ratelimit_sleep} seconds")
                time.sleep(self.ratelimit_sleep)
                if retry > 0:
                    self.download_file(file, retry=retry-1)
                    return
                raise Exception(f"All retries failed!")
            if not response.ok:
                # other
                raise Exception(f"{response.status_code} {response.reason}")

            total = int(response.headers.get('content-length', 0))
            if total:
                total += resume_size

            if not self.simulate:
                if not os.path.exists(os.path.split(file['file_path'])[0]):
                    os.makedirs(os.path.split(file['file_path'])[0])
                with open(part_file, 'ab') as f:
                    start = time.time()
                    downloaded = resume_size
                    for chunk in response.iter_content(chunk_size=1024*1024):
                        downloaded += len(chunk)
                        f.write(chunk)
                        print_download_bar(total, downloaded, resume_size, start)
                print()

                # verify download
                local_hash = get_file_hash(part_file)
                logger.debug(f"Local File hash: {local_hash}")
                logger.debug(f"Sever File hash: {file['file_variables']['hash']}")
                if not local_hash == file['file_variables']['hash']:
                    logger.warning(f"File hash did not match server! | Retrying download")
                    if retry > 0:
                        self.download_file(file, retry=retry-1)
                        return
                    raise Exception(f"All retries failed!")

                if self.overwrite:
                    os.replace(part_file, file['file_path'])
                else:
                    os.rename(part_file, file['file_path'])

    def download_yt_dlp(self, post:dict):
        # download from video streaming site
        # if self.yt_dlp and post['embed']:
            pass
            # my_yt_dlp(post['embed']['url'], post['post_path'], self.yt_dlp_args)

    def load_archive(self):
        # load archived post
        if self.archive_file and os.path.exists(self.archive_file):
            with open(self.archive_file,'r') as f:
                self.archive_list = f.read().splitlines()

    def check_archive(self, post:dict):
        if self.archive_file:
            if "https://{site}/{service}/user/{user_id}/post/{id}".format(**post['post_variables']) in self.archive_list:
                return True
            return False
        return False

    def write_archive(self, post:dict):
        if self.archive_file and self.post_errors == 0 and not self.simulate:
            with open(self.archive_file,'a') as f:
                f.write("https://{site}/{service}/user/{user_id}/post/{id}".format(**post['post_variables']) + '\n')

    def start_download(self):
        # start the download process
        self.load_archive()

        urls = []
        domains = []

        for url in self.input_urls:
            domain = parse_url(url)
            if not domain:
                logger.warning(f"URL is not downloadable | {url}")
                continue
            urls.append(url)
            if not domain in domains: domains.append(domain)

        if self.k_fav_posts or self.k_fav_users:
            if not 'kemono.party' in domains:
                domains.append('kemono.party')
        if self.c_fav_posts or self.c_fav_users:
            if not 'coomer.party' in domains:
                domains.append('coomer.party')

        for domain in domains:
            try:
                self.creators += self.get_creators(domain)
            except:
                logger.exception(f"Unable to get list of creators from {domain}")
        if not self.creators:
            logger.error("No creator information was retrieved. | exiting")
            exit()

        if self.k_fav_posts:
            try:
                self.get_favorites('kemono.party', 'post', retry=self.retry)
            except:
                logger.exception("Unable to get favorite posts from kemono.party")
        if self.c_fav_posts:
            try:
                self.get_favorites('coomer.party', 'post')
            except:
                logger.exception("Unable to get favorite posts from coomer.party")
        if self.k_fav_users:
            try:
                self.get_favorites('kemono.party', 'artist', self.k_fav_users)
            except:
                logger.exception("Unable to get favorite users from kemono.party")
        if self.c_fav_users:
            try:
                self.get_favorites('coomer.party', 'artist', self.c_fav_users)
            except:
                logger.exception("Unable to get favorite users from coomer.party")

        for url in urls:
            try:
                self.get_post(url)
            except:
                logger.exception(f"Unable to get posts for {url}")

def main():
    downloader(get_args())
