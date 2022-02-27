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
import sys

from .arguments import get_args
from .logger import logger
from .version import __version__

args = get_args()
OS_NAME = platform.system()
TIMEOUT = 300

class downloader:

    def __init__(self, urls:list = None):
        # I read using a session would make things faster.
        # Does it? I have no idea and didn't google
        retries = Retry(total=6, backoff_factor=15)
        adapter = HTTPAdapter(max_retries=retries)
        self.session = requests.Session()
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        self.all_creators = self.get_all_creators()

        # self.current_user = None
        # self.current_user_path = None
        self.current_post = None
        # self.current_post_path = None
        self.current_post_errors = 0
        self.downloaded_posts = []

        self.current_server = None
        self.current_server_path = None
        self.current_channel = None
        self.current_channel_path = None
        self.current_channel_errors = 0
        self.current_message = None
        self.current_message_path = None
        self.current_message_errors = 0
        self.downloaded_messages = []

        if args['kemono_favorite_users']:
            self.add_favorite('kemono','artist')
        if args['kemono_favorite_posts']:
            self.add_favorite('kemono','post')
        if args['coomer_favorite_users']:
            self.add_favorite('coomer','artist')
        if args['coomer_favorite_posts']:
            self.add_favorite('coomer','post')

        if urls:
            self.urls = urls
            self.add_links()

    def get_all_creators(self):
        all_creators = []
        headers = {'accept': 'application/json'}
        for site in {'kemono','coomer'}:
            creators_api_url = f'https://{site}.party/api/creators/'
            try:
                all_creators += self.session.get(url=creators_api_url, headers=headers, timeout=TIMEOUT).json()
            except:
                logger.error(f"Failed to get creator info from {site}.party")
        return all_creators

    def get_user_info(self, service:str, user_id:str):
        for creator in self.all_creators:
            if creator['id'] == user_id and creator['service'] == service:
                return creator
        logger.error(f"Failed to find user for service:{service} user_id:{user_id}")
        return None

    def add_favorite(self, site:str, type:str):
        logger.info(f'Adding favorite {type} from {site}.party')
        headers = {'accept': 'application/json'}
        fav_api_url = f'https://{site}.party/api/favorites?type={type}'
        logger.debug(f"{site}.party favorite {type}s api url: {fav_api_url}")
        try:
            logger.debug(f"Requests getting url: {fav_api_url}")
            response = self.session.get(url=fav_api_url, cookies=args['cookies'], headers=headers, timeout=TIMEOUT)
            if not response.ok:
                logger.error(f'{response.status_code} {response.reason}Could not get favorite posts: Make sure you get your cookie file while logged in')
                return
            for favorite in response.json():
                if type == 'post':
                    self.get_posts(site=site,service=favorite['service'],user_id=favorite['user'],post_id=favorite['id'])
                if type == 'artist':
                    self.get_posts(site=site,service=favorite['service'],user_id=favorite['id'])
        except:
            logger.error(f"Failed to get favorite {type}s from {site}.party")

    def add_links(self):
        for url in self.urls:
            self.parse_links(url)

    def parse_links(self, url:str):
        user = re.search(r'^https://(kemono|coomer)\.party/([^/]+)/user/([^/]+)$',url)
        post = re.search(r'^https://(kemono|coomer)\.party/([^/]+)/user/([^/]+)/post/([^/]+)$',url)
        discord = re.search(r'^https://(kemono)\.party/([^/]+)/server/([^/]+)$',url)
        if user:
            self.get_posts(site=user.group(1),service=user.group(2),user_id=user.group(3))
            return
        if post:
            self.get_posts(site=post.group(1),service=post.group(2),user_id=post.group(3),post_id=post.group(4))
            return
        if discord:
            logger.warning("Saving Discord servers is experimental!.")
            # self._find_channels(discord.group(1),discord.group(2),discord.group(3))
            return
        logger.warning(f'Invalid URL: {url}')

    def get_posts(self, site:str, service:str, user_id:str, post_id:str = None):
        user = self.get_user_info(service, user_id)
        if not user:
            return
        user['site'] = site
        # if not post_id:
        #     logger.info(f"Downloading User: {user['name']}")
        #     logger.debug(f"user_id: {user_id} service: {service} url: https://{site}.party/{service}/user/{user_id}")
            # self.download_profile_icon_banner()
        headers = {'accept': 'application/json'}
        chunk = 0
        while True:
            if post_id:
                api_url = f'https://{site}.party/api/{service}/user/{user_id}/post/{post_id}'
                logger.debug(f'Post API URL: {api_url}')
            else:
                api_url = f'https://{site}.party/api/{service}/user/{user_id}?o={chunk}'
                logger.debug(f'User API URL: {api_url}')
            try:
                response = self.session.get(url=api_url, headers=headers, timeout=TIMEOUT).json()
            except:
                logger.error(f"Failed to get api json: URL {api_url}")
                return
            if not response and chunk == 0 and not post_id:
                logger.error(f"Skipping User: No api json found: URL {api_url}")
                return
            elif not response and post_id:
                logger.error(f"Skipping Post: No api json found: URL {api_url}")
                return
            elif not response:
                logger.debug("End of json reached")
                return
            for post in response:
                post['date_object'], post['date_object_string'] = get_post_date(post['published']) # probably shouldn't mix this in the post json
                self.set_current_post(post, user)
                self.download_post()
                self.downloaded_posts.append(post['id'])
            if len(response) < 25:
                logger.debug("End of json reached")
                return
            chunk += 25

    def set_current_post(self, post:dict, user:dict):

        self.current_post = {}
        self.current_post['title'] = post['title']
        self.current_post['added_object'], self.current_post['added'] = get_post_date(post['added'])
        self.current_post['edited_object'], self.current_post['edited'] = get_post_date(post['edited'])
        self.current_post['published_object'], self.current_post['published'] = get_post_date(post['published'])
        self.current_post['id'] = post['id']
        self.current_post['attachments'] = post['attachments']
        self.current_post['file'] = post['file']
        self.current_post['content'] = post['content']
        self.current_post['shared_file'] = post['shared_file']
        self.current_post['embed'] = post['embed']
        self.current_post['user_id'] = user['id']
        self.current_post['username'] = user['name']
        self.current_post['service'] = user['service']
        self.current_post['user_updated_object'], self.current_post['user_updated'] = get_post_date(user['updated'])
        self.current_post['site'] = user['site']
        self.current_post['attachments'] = post['attachments']
        # merge post file into attachments at the front
        if post['file']:
            if not post['file'] in self.current_post['attachments']:
                self.current_post['attachments'].insert(0, post['file'])

        drive, tail = os.path.splitdrive(args['output'])
        tail_split = re.split(r'\\|/', tail)
        if drive:
            final_output = drive + os.path.sep
        else:
            final_output = ''
        for folder in tail_split[:-1]:
            final_output = os.path.join(final_output, clean_folder_name(folder.format(**self.current_post)))

        self.current_post['file_template'] = tail_split[-1]
        self.current_post['path'] = final_output

    # TODO UPDATE
    def download_profile_icon_banner(self):
        to_download = []
        if args['save_banner']:
            to_download += ['banner']
        if args['save_icon']:
            to_download += ['icon']
        for _item in to_download:
            if self.current_user['service'] in {'dlsite'}:
                logger.warning(f"Profile {_item}s are not supported for {self.current_user['service']} users")
                return
            elif self.current_user['service'] in {'gumroad'} and _item == 'banner':
                logger.warning(f"Profile {_item}s are not supported for {self.current_user['service']} users")
                return
            pfp_banner_url = f"https://{self.current_user['site']}.party/{_item}s/{self.current_user['service']}/{self.current_user['user_id']}"
            logger.debug(f"Profile {_item} URL {pfp_banner_url}")
            response = self.session.get(url=pfp_banner_url, cookies=args['cookies'], timeout=TIMEOUT)
            try:
                image = Image.open(BytesIO(response.content))
                if not os.path.exists(self.current_user_path):
                    os.makedirs(self.current_user_path)
                image.save(os.path.join(self.current_user_path, f"Profile_{_item}.{image.format.lower()}"), format=image.format)
            except:
                logger.error(f"Unable to download profile {_item} for {self.current_user['username']}")

    def download_post(self):
        if self.should_download_post():
            logger.info(f"Downloading Post: {clean_folder_name(self.current_post['title'])}")
            logger.debug("user_id: {user_id} service: {service} post_id: {id} url: https://{site}.party/{service}/user/{user_id}/post/{id}".format(**self.current_post))
            logger.debug(f"Sleeping for {args['post_timeout']} seconds")
            time.sleep(args['post_timeout'])
            self.current_post_errors = 0
            self.download_attachments()
            self.download_content()
            self.download_embeds()
            self.save_json()
            self.write_archive()

    def should_download_post(self):
        if self.check_duplicate_post():
            if self.check_user_date_in_range():
                if self.check_date_in_range():
                    if args['update_posts']:
                        return self.check_updated()
                    elif args['archive']:
                        return self.check_archived()
                    return True
        return False

    def check_duplicate_post(self):
        if self.current_post['id'] in self.downloaded_posts:
            logger.info("Skipping Post: Post was already downloaded this session")
            return False
        return True

    # TODO handle old files
    def check_updated(self):
        json_path = os.path.join(self.current_post_path, f"[{self.current_post['id']}].json")
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.loads(f.read())
            current_post_date = datetime.datetime.strptime(self.current_post['edited'], r'%a, %d %b %Y %H:%M:%S %Z') if self.current_post['edited'] else datetime.datetime.min
            old_post_date = datetime.datetime.strptime(data['edited'], r'%a, %d %b %Y %H:%M:%S %Z') if data['edited'] else datetime.datetime.min
            if old_post_date >= current_post_date:
                logger.info("Skipping Post: Post is up to date")
                return False
            return True
        logger.info(f"Skipping Post: {self.current_post['id']}.json not found")
        return False

    def check_archived(self):
        if os.path.exists(args['archive']):
            with open(args['archive'],'r') as f:
                archived = f.read().splitlines()
            if '/{service}/user/{user}/post/{id}'.format(**self.current_post) in archived:
                logger.info("Skipping Post: Post Archived")
                return False
        logger.debug("Archive file does not exist: File will be created when writing post data")
        return True

    def check_date_in_range(self):
        if args['date'] == datetime.datetime.min and args['datebefore'] == datetime.datetime.min and args['dateafter'] == datetime.datetime.max:
            return True
        elif self.current_post['published_object'] == datetime.datetime.min:
            logger.info(f"Skipping Post: Date out of range {self.current_post['published']}")
            return False
        elif not(self.current_post['published_object'] == args['date'] or self.current_post['published_object'] <= args['datebefore'] or self.current_post['published_object'] >= args['dateafter']):
            logger.info(f"Skipping Post: Date out of range {self.current_post['published']}")
            return False
        return True

    def check_user_date_in_range(self):
        if args['user_updated_datebefore'] == datetime.datetime.min and args['user_updated_dateafter'] == datetime.datetime.max:
            return True
        elif not(self.current_post['user_updated_object'] <= args['user_updated_datebefore'] or self.current_post['user_updated_object'] >= args['user_updated_dateafter']):
            logger.info(f"Skipping Post: Date out of range {self.current_post['user_updated']}")
            return False
        return True

    def set_file_name(self, name:str, ext:str, index:str = "0"):
        temp = {'name':name,'ext':ext,'index':index}
        return self.current_post['file_template'].format(**self.current_post, **temp)

    def fix_patreon_link_file_name(self, att_name:str, att_path):
        # tis should add the correct file extention to the file name
        broken_file_name = re.search(r'https://www\.patreon\.com/media-u/([^/]+)',att_name)
        if broken_file_name:
            return f"{att_name}.{att_path.rsplit('.', 1)[-1]}"
        return att_name

    def download_attachments(self):
        if args['skip_attachments']:
            logger.debug("Skipping attachments")
            return
        logger.debug("Downlaoding attachments")
        for index, attachment in enumerate(self.current_post['attachments']):
            index_string = str(index+1).zfill(len(str(len(self.current_post['attachments']))))
            file_url = f"https://{self.current_post['site']}.party/data{attachment['path']}?f={attachment['name']}"
            file_name = self.fix_patreon_link_file_name(attachment['name'], attachment['path'])
            file_name = self.set_file_name(file_name.rsplit('.', 1)[0], file_name.rsplit('.', 1)[-1], index_string)
            file_hash = find_hash(attachment['path'])
            self.requests_download(file_url, self.current_post['path'], file_name, file_hash)

    def download_content(self):
        if not args['skip_comments']:
            comments_soup = self.get_comments()
        else:
            comments_soup = None
        if self.current_post['content']:
            content_soup = BeautifulSoup(self.current_post['content'], 'html.parser')
            if not args['skip_inline']:
                content_soup = self.save_inline(content_soup)
            if args['extract_links']:
                self.save_links(content_soup)
            if not args['skip_content']:
                if not os.path.exists(self.current_post['path']):
                    os.makedirs(self.current_post['path'])
                with open(os.path.join(self.current_post['path'], self.set_file_name('content','html')),'wb') as f:
                    f.write(content_soup.prettify().encode("utf-16"))
                    if comments_soup:
                        f.write(comments_soup.prettify().encode("utf-16"))
        elif not args['skip_content'] and comments_soup:
                with open(os.path.join(self.current_post['path'], self.set_file_name('content','html')),'wb') as f:
                    f.write(comments_soup.prettify().encode("utf-16"))

    def save_inline(self, soup):
        # do these have hashes?
        inline_folder = os.path.join(self.current_post['path'], "inline")
        inline_images = soup.find_all('img')
        for index, inline_image in enumerate(inline_images):
            party_hosted = re.search('^/[^*]+', inline_image['src'])
            if party_hosted:
                if not os.path.exists(inline_folder):
                    os.makedirs(inline_folder)
                # indexing might be wonky if non party hosted images are in between party hosted images
                # indexing always enabled to stop file name collitions
                index_string = str(index).zfill(len(str(len(inline_images))))
                file_name = f"{inline_image['src'].split('/')[-1]}"
                file_name = self.set_file_name(file_name.rsplit('.', 1)[0], file_name.rsplit('.', 1)[-1], index_string)
                file_url = f"https://{self.current_post['site']}.party/data{inline_image['src']}"
                self.requests_download(file_url, inline_folder, file_name)
                inline_image['src'] = os.path.join("inline", file_name)
        return soup

    def save_links(self, soup):
        href_tags = soup.find_all(href=True)
        if href_tags:
            if not os.path.exists(self.current_post['path']):
                os.makedirs(self.current_post['path'])
            with open(os.path.join(self.current_post['path'], self.set_file_name('links','txt')),'w') as f:
                for href_tag in href_tags:
                    f.write(href_tag['href'] + '\n')

    def get_comments(self):
        try:
            # no api method to get comments so using from html (not future proof)
            post_url = "https://{site}.party/{service}/user/{user_id}/post/{id}".format(**self.current_post)
            response = self.session.get(url=post_url, allow_redirects=True, cookies=args['cookies'], timeout=TIMEOUT)
            page_soup = BeautifulSoup(response.text, 'html.parser')
            comment_soup = page_soup.find("div", {"class": "post__comments"})
            if comment_soup:
                no_comments = re.search('([^ ]+ does not support comment scraping yet\.|No comments found for this post\.)',comment_soup.text)
                if no_comments:
                    logger.debug(no_comments.group(1).strip())
                    return None
                return comment_soup
        except:
            return None

    def download_embeds(self):
        if self.current_post['embed']:
            if not args['skip_embed']:
                if not os.path.exists(self.current_post['path']):
                    os.makedirs(self.current_post['path'])
                with open(os.path.join(self.current_post['path'], self.set_file_name('embed','txt')),'wb') as f:
                    f.write("{subject}\n{url}\n{description}".format(**self.current_post['embed']).encode('utf-16'))
            if args['yt_dlp']:
                if not os.path.exists(self.current_post['path']):
                    os.makedirs(self.current_post['path'])
                self.download_yt_dlp(self.current_post['embed']['url'], os.path.join(self.current_post['path'], "embeds"))

    def save_json(self):
        if not args['skip_json']:
            if not os.path.exists(self.current_post['path']):
                os.makedirs(self.current_post['path'])
            # remove datetime objects from json
            del self.current_post['added_object']
            del self.current_post['edited_object']
            del self.current_post['published_object']
            del self.current_post['user_updated_object']
            with open(os.path.join(self.current_post['path'],self.set_file_name('post','json')),'w') as f:
                json.dump(self.current_post, f, indent=4, sort_keys=True)

    def write_archive(self):
        if not self.current_post_errors:
            if args['archive'] and not args['simulate']:
                with open(args['archive'],'a') as f:
                    f.write('/{service}/user/{user}/post/{id}\n'.format(**self.current_post))
                logger.debug('Post Archived: /{service}/user/{user}/post/{id}\n'.format(**self.current_post))

######################### DISCORD STUFF #########################
# TODO UPDATE

    # def _find_channels(self, site:str, service:str, server_id:str):
    #     username = self._get_username(service, server_id)
    #     if not username:
    #         logger.critical(f'No servername found: server_id: {server_id} service: {service}')
    #         return
    #     server = {'site':site,'service':service,'server_id':server_id,'username':username}
    #     self._set_current_server(server)
    #     headers = {'accept': 'application/json'}
    #     server_api_url = f"https://{site}.party/api/{service}/channels/lookup?q={server_id}"
    #     sever_response = self.session.get(url=server_api_url, headers=headers, timeout=TIMEOUT).json()
    #     if not sever_response:
    #         logger.error(f"Server has no api information: URL {server_api_url}")
    #         return
    #     for channel in sever_response:
    #         self._set_current_channel(channel)
    #         skip = 0
    #         while True:
    #             channel_api_url = f"https://{site}.party/api/{service}/channel/{channel['id']}?skip={skip}"
    #             channel_response = self.session.get(url=channel_api_url, headers=headers, timeout=TIMEOUT).json()
    #             if not channel_response and skip == 0:
    #                 logger.error(f"Channel has no api information: URL {channel_api_url}")
    #                 return
    #             if not channel_response:
    #                 break
    #             for message in channel_response:
    #                 self._set_current_message(message)
    #                 if self._should_download_message():
    #                     self._download_message()
    #                 self.downloaded_messages.append(message['id'])
    #                 pass
    #             if len(channel_response) < 10:
    #                 break
    #             skip += 10

    # def _set_current_server(self, server:dict):
    #     self.current_server = server
    #     self.current_server_path = os.path.join(
    #         args['output'],
    #         server['service'],
    #         clean_folder_name(f"{server['username']} [{server['server_id']}]")
    #     )

    # def _set_current_channel(self, channel:dict):
    #     self.current_channel = channel
    #     self.current_channel_path = os.path.join(
    #         self.current_server_path,
    #         clean_folder_name(f"{channel['name']} [{channel['id']}]")
    #     )

    # def _set_current_message(self, message:dict):
    #     self.current_message = message
    #     self.current_message_path = os.path.join(
    #         self.current_channel_path,
    #         clean_folder_name(f"{message['author']['username']} [{message['author']['id']}]")
    #     )

    # def _should_download_message(self):
    #     if self._check_duplicate_message():
    #         return True
    #     return False

    # def _check_duplicate_message(self):
    #     if self.current_message['id'] in self.downloaded_messages:
    #         logger.info("Skipping Message: Message was already downloaded this session")
    #         return False
    #     return True

    # def _download_message(self):
    #     # download message attachments to message folder
    #     self._download_message_attachments()
    #     # write data to html in channel folder in discord format
    #     pass

    # def _download_message_attachments(self):
    #     if not args['skip_attachments']:
    #         if self.current_message['attachments']:
    #             if not os.path.exists(self.current_message_path):
    #                 os.makedirs(self.current_message_path)
    #         for index, attachment in enumerate(self.current_message['attachments']):
    #             index_string = str(index+1).zfill(len(str(len(self.current_message['attachments']))))
    #             file_name = os.path.join(self.current_message_path, clean_file_name(f"[{index_string}]_[{self.current_message['id']}]_{attachment['name']}"))
    #             if args['no_indexing']:
    #                 file_name = os.path.join(self.current_message_path, clean_file_name(f"[{self.current_message['id']}]_{attachment['name']}"))
    #             file_url = f"https://{self.current_server['site']}.party/data{attachment['path']}?f={attachment['name']}"
    #             file_hash = find_hash(attachment['path'])
    #             self.requests_download(file_url, file_name, file_hash)

######################### END OF DISCORD STUFF #########################

    # TODO save file as .part until completed
    def requests_download(self, url:str, file_path:str, file_name:str, file_hash:str = None, retry:int = args['retry_download']):
        resume_size = 0
        timeout = 30

        file_name = clean_file_name(file_name)

        logger.info(f"Downloading: {file_name}")
        logger.debug(f"Download path: {file_path}")
        logger.debug(f"Download url: {url}")

        if check_file_extention(file_name):
            logger.info(f"Skipping download because of file extention: {file_name.split('.')[-1]}")
            return

        # check if file exists and if hashes match
        if os.path.exists(os.path.join(file_path, file_name)) and file_hash:
            local_hash = get_hash(os.path.join(file_path, file_name)).lower()
            logger.debug(f"Local Hash: {local_hash} Server Hash: {file_hash.lower()}")
            if file_hash.lower() == local_hash:
                logger.info("Skipping download because file on disk has matching hash")
                return
            logger.warning(f"File on disk does not have matching hash. Attempting to resume download")

        if os.path.exists(os.path.join(file_path, file_name)):
            resume_size = os.path.getsize(os.path.join(file_path, file_name))

        headers = {
            'Accept-Encoding': None,
            'Range': f'bytes={resume_size}-',
            'User-Agent': args['user_agent']
        }
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
        if response.status_code == 416:
            logger.warning(f'{response.status_code} {response.reason}: Will always happen if server hash is wrong! Please check file and report to site owner that file hash might be wrong')
            return

        # 429 Too many requests
        if response.status_code == 429:
            timeout = 300

        # retry download if status code is not ok
        if not response.ok:
            if retry > 0:
                logger.warning(f"{response.status_code} {response.reason}: Retrying in {timeout} seconds")
                time.sleep(timeout)
                self.requests_download(url=url, file_path=file_path, file_name=file_name, file_hash=file_hash, retry=retry-1)
                return
            logger.critical(f"{response.status_code} {response.reason}: All retries failed!")
            self.current_post_errors += 1
            return

        # get content-length or get 0
        total = int(response.headers.get('content-length', 0))

        # adjust total with resuming size
        if total:
            total += resume_size

        # check file content length
        if check_file_size(total):
            logger.info(f"Skipping download: Does not meat file size requirements: {total} bytes")
            return

        # create file path if it doesn't exist
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        # writing response content to file
        with open(os.path.join(file_path, file_name), 'ab') as f:
            start = time.time()
            downloaded = resume_size
            for chunk in response.iter_content(chunk_size=1024*1024):
                downloaded += len(chunk)
                f.write(chunk)
                print_download_bar(total, downloaded, resume_size, start)
        print()

        # My futile attempts to check if the file downloaded correctly
        if file_hash:
            logger.debug("Checking downloaded file")
            local_hash = get_hash(os.path.join(file_path, file_name)).lower()
            logger.debug(f"Local Hash: {local_hash} Server Hash: {file_hash.lower()}")
            if file_hash.lower() == local_hash:
                logger.debug("Download completed successfully")
                return
            if retry > 0:
                logger.error(f"Download failed / intertupted: Retrying in {timeout} seconds")
                time.sleep(timeout)
                self.requests_download(url=url, file_path=file_path, file_name=file_name, file_hash=file_hash, retry=retry-1)
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

######################### HELPER FUNCTIONS #########################

# return hash from download url
def find_hash(url:str):
    find_hash = re.search(r'^([a-z0-9]{64})$',url.split('/')[-1].split('.')[0])
    if find_hash:
        return find_hash.group(1)
    return None

# return hash from file
def get_hash(file):
    sha256_hash = hashlib.sha256()
    with open(file,"rb") as f:
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
    file_split = string.rsplit('.', 1)
    if len(file_split) == 1:
        file_name = file_split[0]
        file_extention = ''
    else:
        file_name = file_split[0]
        file_extention = f".{file_split[1]}"
    if args['restrict_names']:
        file_name = restrict_names(file_name)
    file_extention = re.sub(r'[\\/:\"*?<>|\n\t\b\r]','_',file_extention)
    file_name = re.sub(r'[\\/:\"*?<>|\n\t\b\r]','_',file_name)[:255-len(file_extention)]
    return f"{file_name}{file_extention}"

def clean_folder_name(string:str):
    if args['restrict_names']:
        string = restrict_names(string)
    return re.sub(r'[\\/:\"*?<>|\n\t\b\r]','_',string)[:248].rstrip('. ')

# returns string replacing non ascii characters, spaces, and "&"
def restrict_names(string:str):
    return re.sub(r'[^\x00-\x7f]|[ &]','_',string)

# takes post date sting and converts it back to datetime object, and simple datetime string
def get_post_date(date:str):
    if date:
        date_object = datetime.datetime.strptime(date, r'%a, %d %b %Y %H:%M:%S %Z')
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

def check_version():
    try:
        current_version = datetime.datetime.strptime(__version__, r'%Y.%m.%d')
    except:
        current_version = datetime.datetime.strptime(__version__, r'%Y.%m.%d.%H')
    github_api_url = 'https://api.github.com/repos/AplhaSlayer1964/kemono-dl/releases/latest'
    try:
        responce = requests.get(url=github_api_url, timeout=TIMEOUT)
    except:
        logger.error("Failed to get github latest release")
        return
    if not responce.ok:
        logger.error("Failed to get github latest release")
        return
    latest_tag = responce.json()['tag_name']
    try:
        latest_version = datetime.datetime.strptime(latest_tag, r'%Y.%m.%d')
    except:
        latest_version = datetime.datetime.strptime(latest_tag, r'%Y.%m.%d.%H')
    if current_version < latest_version:
        logger.debug(f"Using kemono-dl {__version__} while latest release is kemono-dl {latest_tag}")
        logger.warning(f"A newer version of kemono-dl is available. Please update to the latest release at https://github.com/AplhaSlayer1964/kemono-dl/releases/latest")

######################### END OF HELPER FUNCTIONS #########################

def main():
    logger.debug(f"Given command: python {' '.join(sys.argv)}")
    try:
        check_version()
    except:
        logger.error("Failed to check latest version of kemono-dl")
    start_time = time.time()
    urls = []
    for link in args['links']:
        urls.append(link)
    for link in args['from_file']:
        urls.append(link)
    downloader(urls)
    final_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time))
    logger.debug(f"Completed in {final_time}")
    logger.info("Completed")