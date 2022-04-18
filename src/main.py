import requests
import re
import os
from bs4 import BeautifulSoup
import time
import datetime

from .args import get_args
from .logger import logger
from .version import __version__
from .helper import get_file_hash, clean_folder_name, clean_file_name, restrict_ascii, print_download_bar, check_date
from .my_yt_dlp import my_yt_dlp

class downloader:

    def __init__(self, args):
        self.input_urls = args['links'] + args['from_file']
        # list of parsed urls
        self.urls = []
        # list of sites to get creators from
        self.sites = []
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
        self.content_filename_template = args['content_filename_pattern']
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
        self.yt_dlp = args['yt_dlp']
        self.files = (not args['skip_attachments']) or args['inline']
        self.k_fav_posts = args['kemono_fav_posts']
        self.c_fav_posts = args['coomer_fav_posts']
        self.k_fav_users = args['kemono_fav_users']
        self.c_fav_users = args['coomer_fav_users']

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

        self.start_download()

    def parse_urls(self):
        # parse input urls
        for url in self.input_urls:
            downloadable = re.search(r'^https://(kemono|coomer)\.party/([^/]+)/user/([^/]+)($|/post/([^/]+)$)',url)
            if not downloadable:
                logger.warning(f"URL is not downloadable | {url}")
                continue
            self.urls.append(url)
            if not downloadable.group(1) in self.sites:
                self.sites.append(downloadable.group(1))

    def get_creators(self, site:str):
        # get site creators
        creators_api = f"https://{site}.party/api/creators/"
        creators_json = requests.get(url=creators_api, cookies=self.cookies, headers=self.headers, timeout=self.timeout).json()
        self.creators += creators_json

    def get_user(self, user_id:str, service:str):
        for creator in self.creators:
            if creator['id'] == user_id and creator['service'] == service:
                return creator
        return None

    def get_favorites(self, site:str, type:str, services:list = None):
        fav_api = f'https://{site}.party/api/favorites?type={type}'
        try:
            response = requests.get(url=fav_api, headers=self.headers, cookies=self.cookies, timeout=self.timeout)
        except:
            self.get_favorites(site, type, services)
            return
        if response.status_code == 401:
            logger.error(f"{response.status_code} {response.reason} | Bad cookie file")
            return
        if not response.ok:
            logger.error(f"{response.status_code} {response.reason}")
            self.get_favorites(site, type, services)
            return
        for favorite in response.json():
            if type == 'post':
                self.get_post(f"https://{site}.party/{favorite['service']}/user/{favorite['user']}/post/{favorite['id']}")
            if type == 'artist':
                if not (favorite['service'] in services or 'all' in services):
                    logger.info(f"Skipping user {favorite['name']} | Service {favorite['service']} was not requested")
                    continue
                self.get_post(f"https://{site}.party/{favorite['service']}/user/{favorite['id']}")

    def get_post(self, url:str):
        found = re.search(r'(https://(kemono|coomer)\.party/)(([^/]+)/user/([^/]+)($|/post/[^/]+))', url)
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
        if self.skip_user(user):
            return
        chunk = 0
        while True:
            if is_post:
                json = requests.get(url=api, cookies=self.cookies, headers=self.headers, timeout=self.timeout).json()
            else:
                json = requests.get(url=f"{api}?o={chunk}", cookies=self.cookies, headers=self.headers, timeout=self.timeout).json()
            if not json:
                if is_post:
                    logger.error(f"Unable to find post json for {api}")
                elif chunk == 0:
                    logger.error(f"Unable to find user json for {api}?o={chunk}")
                return # completed
            for post in json:
                post = self.clean_post(post, user, site)
                if self.skip_post(post):
                    continue
                if "https://{site}/{service}/user/{user_id}/post/{id}".format(**post) in self.comp_posts:
                    continue
                try:
                    self.download_post(post)
                    if self.post_timeout:
                        logger.info(f"Sleeping for {self.post_timeout} seconds.")
                        time.sleep(self.post_timeout)
                except:
                    logger.exception(f"Unable to download post | service:{post['service']} user_id:{post['user_id']} post_id:{post['id']}")
                self.comp_posts.append("https://{site}/{service}/user/{user_id}/post/{id}".format(**post))
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

        if check_date(datetime.datetime.strptime(post['published'], self.date_strf_pattern), self.date, self.datebefore, self.dateafter):
            logger.info("Skipping post | post published date not in range")
            return True
        return False

    def set_post_path(self, post):
        drive, tail = os.path.splitdrive(self.download_path_template)
        tail_split = re.split(r'\\|/', tail)
        cleaned_path = drive + os.path.sep if drive else ''
        for folder in tail_split:
            if self.restrict_ascii:
                cleaned_path = os.path.join(cleaned_path, restrict_ascii(clean_folder_name(folder.format(**post))))
            else:
                cleaned_path = os.path.join(cleaned_path, clean_folder_name(folder.format(**post)))
        post['post_path'] = cleaned_path

    def set_file_path(self, post, file, template):
        post_path = post['post_path']
        file_split = re.split(r'\\|/', template)
        if len(file_split) > 1:
            for folder in file_split[:-1]:
                if self.restrict_ascii:
                    post_path = os.path.join(post_path, restrict_ascii(clean_folder_name(folder.format(**file, **post))))
                else:
                    post_path = os.path.join(post_path, clean_folder_name(folder.format(**file, **post)))
        if self.restrict_ascii:
            cleaned_file = restrict_ascii(clean_file_name(file_split[-1].format(**file, **post)))
        else:
            cleaned_file = clean_file_name(file_split[-1].format(**file, **post))
        file['file_path'] = os.path.join(post_path, cleaned_file)

    def extract_inline_images(self, post, content_soup):
        '''
        CLEAN!
        '''
        inline_images = content_soup.find_all("img", {"data-media-id": True})
        post['inline'] = []
        for index, inline_image in enumerate(inline_images):
            filename, file_extension = os.path.splitext(inline_image['src'].rsplit('/')[-1])
            m = re.search(r'[a-zA-Z0-9]{64}', inline_image['src'])
            file_hash = m.group(0) if m else ''
            clean_file = {
                'filename': filename,
                'ext': file_extension[1:],
                'url': f"https://{post['site']}/data{inline_image['src']}",
                'hash': file_hash,
                'index': f"{index + 1}".zfill(len(str(len(inline_images))))
            }
            self.set_file_path(post, clean_file, self.inline_filename_template)
            # set local image location in html
            inline_image['src'] = os.path.join(clean_file['file_path'], clean_file['file_name'])
            post['inline'].append(clean_file)
        return content_soup.prettify()

    def get_comments(self, post:dict):
        # no api method to get comments so using from html (not future proof)
        post_url = "https://{site}/{service}/user/{user_id}/post/{id}".format(**post)
        response = requests.get(url=post_url, allow_redirects=True, headers=self.headers, cookies=self.cookies, timeout=self.timeout)
        page_soup = BeautifulSoup(response.text, 'html.parser')
        comment_soup = page_soup.find("div", {"class": "post__comments"})
        no_comments = re.search('([^ ]+ does not support comment scraping yet\.|No comments found for this post\.)',comment_soup.text)
        if no_comments:
            logger.debug(no_comments.group(1).strip())
            return ''
        return comment_soup.prettify()

    def process_post_content(self, post:dict, clean_post:dict):
        '''
        CLEAN!
        '''
        content_soup = BeautifulSoup(post['content'], 'html.parser')
        embed = "{subject}\n{url}\n{description}".format(**post['embed']) if post['embed'] else ''
        if self.inline:
            self.extract_inline_images(clean_post, content_soup)
        comments_html = ''
        if self.comments:
            try:
                comments_html = self.get_comments(clean_post)
            except:
                self.post_errors += 1
                logger.exception("Failed to get post comments")
        clean_post['content'] = None
        if (self.content or self.comments) and (post['content'] or embed or comments_html):
            clean_post['content'] = "{content}\n{embed}\n{comments}".format(content=content_soup, embed=embed, comments=comments_html)
            clean_post['content_file'] = {'filename':'content','ext':'html'}
            self.set_file_path(clean_post, clean_post['content_file'], self.content_filename_template)
        if self.extract_links:
            href_links = content_soup.find_all(href=True)
            clean_post['links'] = [href_link['href'] for href_link in href_links]

    def clean_post(self, post:dict, user:dict, site:str):
        '''
        CLEAN!
        Maybe set a variables dictionary so people can't accidentally use bad variables like post content
        '''
        # change post dictionary format
        clean_post = {}
        clean_post['title'] = post['title']
        clean_post['id'] = post['id']
        clean_post['user_id'] = post['user']
        clean_post['username'] = user['name']
        clean_post['service'] = post['service']
        clean_post['embed'] = post['embed']
        clean_post['site'] = f"{site}.party"

        # make these three datetime objects
        clean_post['added'] = (datetime.datetime.strptime(post['added'], r'%a, %d %b %Y %H:%M:%S %Z') if post['added'] else datetime.datetime.min).strftime(self.date_strf_pattern)
        clean_post['updated'] = (datetime.datetime.strptime(post['edited'], r'%a, %d %b %Y %H:%M:%S %Z') if post['edited'] else datetime.datetime.min).strftime(self.date_strf_pattern)
        clean_post['user_updated'] = (datetime.datetime.strptime(user['updated'], r'%a, %d %b %Y %H:%M:%S %Z') if user['updated'] else datetime.datetime.min).strftime(self.date_strf_pattern)
        clean_post['published'] = (datetime.datetime.strptime(post['published'], r'%a, %d %b %Y %H:%M:%S %Z') if post['published'] else datetime.datetime.min).strftime(self.date_strf_pattern)

        self.set_post_path(clean_post)

        # add post file to front of attachments list if it doesn't already exist
        if post['file'] and not post['file'] in post['attachments']:
            post['attachments'].insert(0, post['file'])

        clean_post['attachments'] = []
        for index, file in enumerate(post['attachments']):
            filename, file_extension = os.path.splitext(file['name'])
            m = re.search(r'[a-zA-Z0-9]{64}', file['path'])
            file_hash = m.group(0) if m else ''
            clean_file = {
                'filename': filename,
                'ext': file_extension[1:],
                'url': f"https://{clean_post['site']}/data{file['path']}?f={file['name']}",
                'hash': file_hash,
                'index': f"{index + 1}".zfill(len(str(len(post['attachments']))))
            }
            self.set_file_path(clean_post, clean_file, self.filename_template)
            clean_post['attachments'].append(clean_file)

        self.process_post_content(post, clean_post)
        return clean_post

    def download_post(self, post:dict):
        logger.info(f"Starting Post | {post['title']}")
        logger.debug(f"URL | https://{post['site']}/{post['service']}/user/{post['user_id']}/post/{post['id']}")
        self.download_icon(post)
        self.download_banner(post)
        self.download_attachments(post)
        self.download_inline(post)
        self.write_content(post)
        self.write_links(post)
        self.download_yt_dlp(post)
        self.write_archive(post)
        self.post_errors = 0

    def download_icon(self, post:dict):
        pass

    def download_banner(self, post:dict):
        pass

    def download_attachments(self, post:dict):
        # download the post attachments
        if self.attachments:
            for file in post['attachments']:
                try:
                    self.download_file(file, retry=self.retry)
                except:
                    self.post_errors += 1
                    logger.exception(f"Failed to download {os.path.split(file['file_path'])[1]}")

    def download_inline(self, post:dict):
        # download the post inline files
        if self.inline:
            for file in post['inline']:
                try:
                    self.download_file(file, retry=self.retry)
                except:
                    self.post_errors += 1
                    logger.exception(f"Failed to download {os.path.split(file['file_path'])[1]}")

    def write_content(self, post:dict):
        # write post content
        if (self.content or self.comments) and post['content']:
            try:
                # check if file exists and if should overwrite
                if os.path.exists(post['content_file']['file_path']) and not self.overwrite:
                    logger.info("Skipping content.html file already exists")
                    return
                # create folder path if it doesn't exist
                if not os.path.exists(os.path.split(post['content_file']['file_path'])[0]):
                    os.makedirs(os.path.split(post['content_file']['file_path'])[0])
                # write content to file
                with open(post['content_file']['file_path'],'wb') as f:
                    # write post content to file
                    if (self.content or self.comments) and post['content']:
                        f.write(post['content'].encode("utf-16"))
            except:
                self.post_errors += 1
                logger.exception("Failed to save content.html")

    def write_links(self, post:dict):
        # Write post content links
        if self.extract_links:
            try:
                # don't write duplicate links
                with open(os.path.join(post['post_path'],'links.txt'),'a') as f:
                    for links in post['links']:
                        f.write(links + '\n')
            except:
                self.post_errors += 1
                logger.exception("Failed to save links.txt")

    def write_json(self):
        # todo
        pass

    def skip_file(self, file:dict):
        # check if file exists
        if not self.overwrite:
            if os.path.exists(file['file_path']):
                logger.info(f"Skipping download | File already exists")
                return True

        # check file name extention
        if self.only_ext:
            if not file['ext'].lower() in self.only_ext:
                logger.info(f"Skipping download | File extention {file['ext']} not found in include list {self.only_ext}")
                return True
        if self.not_ext:
            if file['ext'].lower() in self.not_ext:
                logger.info(f"Skipping download | File extention {file['ext']} found in exclude list {self.not_ext}")
                return True

        # check file size
        if self.min_size or self.max_size:
            file_size = requests.get(file['url'], cookies=self.cookies, stream=True).headers.get('content-length', 0)
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
            logger.info(f"Downloading {os.path.split(file['file_path'])[1]}")
            logger.debug(f"Downloading from {file['url']}")
            logger.debug(f"Downloading to {os.path.split(file['file_path'])[0]}")

            part_file = f"{file['file_path']}.part" if not self.no_part else file['file_path']

            # try to resume part files
            resume_size = 0
            if os.path.exists(part_file) and not self.overwrite:
                resume_size = os.path.getsize(part_file)
                logger.info("Trying to resuming partial download")

            self.headers['Range'] = f"bytes={resume_size}-"

            try:
                response = requests.get(url=file['url'], stream=True, headers=self.headers, cookies=self.cookies, timeout=self.timeout)
            except:
                logger.exception(f"Failed to download {os.path.split(file['file_path'])[1]} | Retrying download")
                if retry > 0:
                    self.download_file(file, retry=retry-1)
                    return
                logger.error(f"All retries failed!")
                return Exception

            if response.status_code == 404:
                # doesn't exist
                logger.error(f"{response.status_code} {response.reason}")
                return Exception
            if response.status_code == 403:
                # ddos guard
                logger.error(f"{response.status_code} {response.reason} | Bad cookies")
                return Exception
            if response.status_code == 416:
                # bad request range
                logger.error(f"{response.status_code} {response.reason} | Bad server file hash!")
                return Exception
            if response.status_code == 429:
                # ratelimit
                logger.warning(f"{response.status_code} {response.reason} | Retrying download in {self.ratelimit_sleep} seconds")
                time.sleep(self.ratelimit_sleep)
                if retry > 0:
                    self.download_file(file, retry=retry-1)
                    return
                logger.error(f"All retries failed!")
                return Exception
            if not response.ok:
                # other
                logger.error(f"{response.status_code} {response.reason}")
                return Exception

            if not os.path.exists(os.path.split(file['file_path'])[0]):
                os.makedirs(os.path.split(file['file_path'])[0])

            total = int(response.headers.get('content-length', 0))
            if total:
                total += resume_size
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
            if not local_hash == file['hash']:
                logger.warning(f"File hash did not match server! | Retrying download")
                if retry > 0:
                    self.download_file(file, retry=retry-1)
                    return
                logger.error(f"All retries failed!")
                return Exception

            if self.overwrite:
                os.replace(part_file, file['file_path'])
            else:
                os.rename(part_file, file['file_path'])

    def download_yt_dlp(self, post:dict):
        # download from video streaming site
        if self.yt_dlp and post['embed']:
            pass
            # my_yt_dlp(post['embed']['url'], post['post_path'], self.yt_dlp_args)

    def check_archive(self, post:dict):
        if self.archive_file:
            if "https://{site}/{service}/user/{user_id}/post/{id}".format(**post) in self.archive_list:
                return True
            return False
        return False

    def load_archive(self):
        # load archived post
        if self.archive_file and os.path.exists(self.archive_file):
            with open(self.archive_file,'r') as f:
                self.archive_list = f.read().splitlines()

    def write_archive(self, post:dict):
        if self.archive_file and self.post_errors == 0:
            with open(self.archive_file,'a') as f:
                f.write("https://{site}/{service}/user/{user_id}/post/{id}".format(**post) + '\n')

    def start_download(self):
        # start the download process
        self.load_archive()

        self.parse_urls()

        for site in self.sites:
            try:
                self.get_creators(site)
            except:
                logger.exception(f"Unable to get list of creators for {site}.party")

        if self.k_fav_posts:
            try:
                self.get_favorites('kemono', 'posts')
            except:
                logger.exception("Unable to get favorite posts from kemono.party")
        if self.c_fav_posts:
            try:
                self.get_favorites('coomer', 'posts')
            except:
                logger.exception("Unable to get favorite posts from coomer.party")
        if self.k_fav_users:
            try:
                self.get_favorites('kemono', 'artists', self.k_fav_users)
            except:
                logger.exception("Unable to get favorite users from kemono.party")
        if self.c_fav_users:
            try:
                self.get_favorites('coomer', 'artists', self.c_fav_users)
            except:
                logger.exception("Unable to get favorite users from coomer.party")

        for url in self.urls:
            try:
                self.get_post(url)
            except:
                logger.exception(f"Unable to get posts for {url}")

def main():
    downloader(get_args())
