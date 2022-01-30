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
        self.kemono_creators = []
        self.coomer_creators = []

        self.current_user = None
        self.current_user_path = None
        self.current_post = None
        self.current_post_path = None
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
            self.add_favorite_artists('kemono')
        if args['kemono_favorite_posts']:
            self.add_favorite_posts('kemono')
        if args['coomer_favorite_users']:
            self.add_favorite_artists('coomer')
        if args['coomer_favorite_posts']:
            self.add_favorite_posts('coomer')

        if urls:
            self.urls = urls
            self.add_links()

    def _add_all_creators(self, site:str):
        if site == 'kemono':
            if self.kemono_creators:
                return
        if site == 'coomer':
            if self.coomer_creators:
                return
        headers = {'accept': 'application/json'}
        creators_api_url = f'https://{site}.party/api/creators/'
        all_creators = self.session.get(url=creators_api_url, headers=headers, timeout=TIMEOUT)
        if site == 'kemono':
            self.kemono_creators = all_creators.json()
        if site == 'coomer':
            self.coomer_creators = all_creators.json()

    def _get_username(self, service:str, user_id:str):
        all_creators = [self.kemono_creators, self.coomer_creators]
        for site in all_creators:
            for creator in site:
                if creator['id'] == user_id and creator['service'] == service:
                    return creator['name']
        return None

    def add_favorite_artists(self, site:str):
        self._add_all_creators(site)
        logger.info('Gathering favorite users')
        headers = {'accept': 'application/json'}
        fav_art_api_url = f'https://{site}.party/api/favorites?type=artist'
        response = self.session.get(url=fav_art_api_url, cookies=args['cookies'], headers=headers, timeout=TIMEOUT)
        if not response.ok:
            logger.warning(f'{response.status_code} {response.reason}: Could not get favorite artists: Make sure you get your cookie file while logged in')
            return
        for favorite in response.json():
            current_updated = datetime.datetime.strptime(favorite['updated'], r'%a, %d %b %Y %H:%M:%S %Z')
            if current_updated > args['favorite_users_updated_within']:
                self._find_posts(site,favorite['service'],favorite['id'])

    def add_favorite_posts(self, site:str):
        logger.info('Gathering favorite posts')
        headers = {'accept': 'application/json'}
        fav_art_api_url = f'https://{site}.party/api/favorites?type=post'
        response = self.session.get(url=fav_art_api_url, cookies=args['cookies'], headers=headers, timeout=TIMEOUT)
        if not response.ok:
            logger.warning(f'{response.status_code} {response.reason}Could not get favorite posts: Make sure you get your cookie file while logged in')
            return
        for favorite in response.json():
            self._find_posts(site,favorite['service'],favorite['user'],favorite['id'])

    def add_links(self):
        for url in self.urls:
            self._parse_links(url)

    def _parse_links(self, url:str):
        user = re.search(r'^https://(kemono|coomer)\.party/([^/]+)/user/([^/]+)$',url)
        post = re.search(r'^https://(kemono|coomer)\.party/([^/]+)/user/([^/]+)/post/([^/]+)$',url)
        discord = re.search(r'^https://(kemono)\.party/([^/]+)/server/([^/]+)$',url)
        if user:
            self._add_all_creators(user.group(1))
            self._find_posts(user.group(1),user.group(2),user.group(3))
            return
        if post:
            self._add_all_creators(post.group(1))
            self._find_posts(post.group(1),post.group(2),post.group(3),post.group(4))
            return
        if discord:
            logger.warning("Saving Discord servers is experimental!.")
            self._add_all_creators(discord.group(1))
            self._find_channels(discord.group(1),discord.group(2),discord.group(3))
            return
        logger.warning(f'Invalid URL: {url}')

    def _find_posts(self, site:str, service:str, user_id:str, post_id:str = None):
        username = self._get_username(service, user_id)
        if not username:
            logger.critical(f'No username found: user_id: {user_id} service: {service}')
            return
        user = {'site':site,'service':service,'user_id':user_id,'username':username}
        self._set_current_user(user)
        if not post_id:
            logger.info(f"Downloading User: {self.current_user['username']}")
            logger.debug(f"user_id: {self.current_user['user_id']} service: {self.current_user['service']} url: https://{self.current_user['site']}.party/{self.current_user['service']}/user/{self.current_user['user_id']}")
            self._download_profile_icon_banner()
        headers = {'accept': 'application/json'}
        chunk = 0
        while True:
            if post_id:
                api_url = f'https://{site}.party/api/{service}/user/{user_id}/post/{post_id}'
                logger.debug(f'Post API URL: {api_url}')
            else:
                api_url = f'https://{site}.party/api/{service}/user/{user_id}?o={chunk}'
                logger.debug(f'User API URL: {api_url}')

            response = self.session.get(url=api_url, headers=headers, timeout=TIMEOUT).json()
            if not response and chunk == 0 and not post_id:
                logger.error(f"Skipping User: No api information: URL {api_url}")
                return
            elif not response and post_id:
                logger.error(f"Skipping Post: No api information: URL {api_url}")
                return
            elif not response:
                break
            for post in response:
                # probably shouldn't mix this in the post json
                post['date_object'], post['date_object_string'] = get_post_date(post)
                self._set_current_post(post)
                if self._should_download_post():
                    self.download_post()
                self.downloaded_posts.append(post['id'])
            if len(response) < 25:
                break
            chunk += 25

    def download_post(self):
        logger.info(f"Downloading Post: {clean_folder_name(self.current_post['title'])}")
        logger.debug("user_id: {user} service: {service} post_id: {id} url: https://{site}.party/{service}/user/{user}/post/{id}".format(site=self.current_user['site'],**self.current_post))
        logger.debug(f"Sleeping for {args['post_timeout']} seconds")
        time.sleep(args['post_timeout'])
        self._download_content()
        self._download_attachments()
        self._download_comments()
        self._download_embeds()
        self._save_json()
        self._write_archive()
        self.current_post_errors = 0

    def _set_current_user(self, user:dict):
        self.current_user = user
        self.current_user_path = os.path.join(
            args['output'],
            user['service'],
            clean_folder_name(f"{user['username']} [{user['user_id']}]")
        )

    def _set_current_post(self, post:dict):
        self.current_post = post
        self.current_post_path = os.path.join(
            self.current_user_path,
            clean_folder_name(f"[{post['date_object_string']}] [{post['id']}] {post['title']}")
        )

    def _should_download_post(self):
        if self._check_duplicate_post():
            if self._check_date_in_range():
                if args['update_posts']:
                    return self._check_updated()
                elif args['archive']:
                    return self._check_archived()
                return True
        return False

    def _check_duplicate_post(self):
        if self.current_post['id'] in self.downloaded_posts:
            logger.info("Skipping Post: Post was already downloaded this session")
            return False
        return True

    def _check_updated(self):
        json_path = os.path.join(self.current_post_path, f"{self.current_post['id']}.json")
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

    def _check_archived(self):
        if os.path.exists(args['archive']):
            with open(args['archive'],'r') as f:
                archived = f.read().splitlines()
            if '/{service}/user/{user}/post/{id}'.format(**self.current_post) in archived:
                logger.info("Skipping Post: Post Archived")
                return False
        logger.debug("Archive file does not exist: File will be created when writing post data")
        return True

    def _check_date_in_range(self):
        if args['date'] == datetime.datetime.min and args['datebefore'] == datetime.datetime.min and args['dateafter'] == datetime.datetime.max:
            return True
        elif self.current_post['date_object'] == datetime.datetime.min:
            logger.info(f"Skipping Post: Date out of range {self.current_post['date_object_string']}")
            return False
        elif not(self.current_post['date_object'] == args['date'] or self.current_post['date_object'] <= args['datebefore'] or self.current_post['date_object'] >= args['dateafter']):
            logger.info(f"Skipping Post: Date out of range {self.current_post['date_object_string']}")
            return False
        return True

    def _save_json(self):
        if not args['skip_json']:
            if not os.path.exists(self.current_post_path):
                os.makedirs(self.current_post_path)
            # json.dump can't handle the datetime object
            self.current_post['date_object'] = None
            with open(os.path.join(self.current_post_path,f"{self.current_post['id']}.json"),'w') as f:
                json.dump(self.current_post, f, indent=4, sort_keys=True)

    def _write_archive(self):
        if not self.current_post_errors:
            if args['archive'] and not args['simulate']:
                with open(args['archive'],'a') as f:
                    f.write('/{service}/user/{user}/post/{id}\n'.format(**self.current_post))
                logger.debug('Post Archived: /{service}/user/{user}/post/{id}\n'.format(**self.current_post))

    def _download_profile_icon_banner(self):
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

    def _download_attachments(self):
        if not args['skip_attachments']:
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
                file_url = f"https://{self.current_user['site']}.party/data{attachment['path']}?f={attachment['name']}"
                file_hash = find_hash(attachment['path'])
                self._requests_download(file_url, file_name, file_hash)

    def _download_content(self):
        if self.current_post['content']:
            content_soup = BeautifulSoup(self.current_post['content'], 'html.parser')
            if not args['skip_inline']:
                content_soup = self._save_inline(content_soup)
            if args['extract_links']:
                if not os.path.exists(self.current_post_path):
                    os.makedirs(self.current_post_path)
                self._save_links(content_soup)
            if not args['skip_content']:
                if not os.path.exists(self.current_post_path):
                    os.makedirs(self.current_post_path)
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
                # indexing might be wonky if non party hosted images are in between party hosted images
                index_string = str(index).zfill(len(str(len(inline_images))))
                file_name = os.path.join(self.current_post_path, 'inline', f"[{index_string}]_{inline_image['src'].split('/')[-1]}")
                file_url = f"https://{self.current_user['site']}.party/data{inline_image['src']}"
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
        if not args['skip_comments']:
            # no api method to get comments so using from html (not future proof)
            post_url = f"https://{self.current_user['site']}.party/{self.current_user['service']}/user/{self.current_user['user_id']}/post/{self.current_post['id']}"
            response = self.session.get(url=post_url, allow_redirects=True, cookies=args['cookies'], timeout=TIMEOUT)
            page_soup = BeautifulSoup(response.text, 'html.parser')
            comment_html = page_soup.find("div", {"class": "post__comments"})
            if comment_html:
                do_not_save = re.search('([^ ]+ does not support comment scraping yet\.|No comments found for this post\.)',comment_html.text)
                if do_not_save:
                    logger.debug(do_not_save.group(1).strip())
                else:
                    if not os.path.exists(self.current_post_path):
                        os.makedirs(self.current_post_path)
                    with open(os.path.join(self.current_post_path, 'comments.html'),'wb') as f:
                        f.write(comment_html.prettify().encode("utf-16"))

    def _download_embeds(self):
        if self.current_post['embed']:
            if not args['skip_embed']:
                if not os.path.exists(self.current_post_path):
                    os.makedirs(self.current_post_path)
                with open(os.path.join(self.current_post_path, 'embed.txt'),'wb') as f:
                    f.write("{subject}\n{url}\n{description}".format(**self.current_post['embed']).encode('utf-16'))
            if args['yt_dlp']:
                if not os.path.exists(self.current_post_path):
                    os.makedirs(self.current_post_path)
                self.download_yt_dlp(self.current_post['embed']['url'], os.path.join(self.current_post_path, 'embed'))



    def _find_channels(self, site:str, service:str, server_id:str):
        username = self._get_username(service, server_id)
        if not username:
            logger.critical(f'No servername found: server_id: {server_id} service: {service}')
            return
        server = {'site':site,'service':service,'server_id':server_id,'username':username}
        self._set_current_server(server)
        headers = {'accept': 'application/json'}
        server_api_url = f"https://{site}.party/api/{service}/channels/lookup?q={server_id}"
        sever_response = self.session.get(url=server_api_url, headers=headers, timeout=TIMEOUT).json()
        if not sever_response:
            logger.error(f"Server has no api information: URL {server_api_url}")
            return
        for channel in sever_response:
            self._set_current_channel(channel)
            skip = 0
            while True:
                channel_api_url = f"https://{site}.party/api/{service}/channel/{channel['id']}?skip={skip}"
                channel_response = self.session.get(url=channel_api_url, headers=headers, timeout=TIMEOUT).json()
                if not channel_response and skip == 0:
                    logger.error(f"Channel has no api information: URL {channel_api_url}")
                    return
                if not channel_response:
                    break
                for message in channel_response:
                    self._set_current_message(message)
                    if self._should_download_message():
                        self._download_message()
                    self.downloaded_messages.append(message['id'])
                    pass
                if len(channel_response) < 10:
                    break
                skip += 10

    def _set_current_server(self, server:dict):
        self.current_server = server
        self.current_server_path = os.path.join(
            args['output'],
            server['service'],
            clean_folder_name(f"{server['username']} [{server['server_id']}]")
        )

    def _set_current_channel(self, channel:dict):
        self.current_channel = channel
        self.current_channel_path = os.path.join(
            self.current_server_path,
            clean_folder_name(f"{channel['name']} [{channel['id']}]")
        )

    def _set_current_message(self, message:dict):
        self.current_message = message
        self.current_message_path = os.path.join(
            self.current_channel_path,
            clean_folder_name(f"{message['author']['username']} [{message['author']['id']}]")
        )

    def _should_download_message(self):
        if self._check_duplicate_message():
            return True
        return False

    def _check_duplicate_message(self):
        if self.current_message['id'] in self.downloaded_messages:
            logger.info("Skipping Message: Message was already downloaded this session")
            return False
        return True

    def _download_message(self):
        # download message attachments to message folder
        self._download_message_attachments()
        # write data to html in channel folder in discord format
        pass

    def _download_message_attachments(self):
        if not args['skip_attachments']:
            if self.current_message['attachments']:
                if not os.path.exists(self.current_message_path):
                    os.makedirs(self.current_message_path)
            for index, attachment in enumerate(self.current_message['attachments']):
                index_string = str(index+1).zfill(len(str(len(self.current_message['attachments']))))
                file_name = os.path.join(self.current_message_path, clean_file_name(f"[{index_string}]_[{self.current_message['id']}]_{attachment['name']}"))
                if args['no_indexing']:
                    file_name = os.path.join(self.current_message_path, clean_file_name(f"[{self.current_message['id']}]_{attachment['name']}"))
                file_url = f"https://{self.current_server['site']}.party/data{attachment['path']}?f={attachment['name']}"
                file_hash = find_hash(attachment['path'])
                self._requests_download(file_url, file_name, file_hash)





    # TODO save file as .part until completed
    def _requests_download(self, url:str, file_name:str, file_hash:str = None, retry:int = args['retry_download']):
        logger.debug(f"Preparing download: File Name: {os.path.split(file_name)[1]} URL: {url}")

        # check file extention
        if check_file_extention(os.path.split(file_name)[1]):
            logger.info(f"Skipping download: File extention excluded: {os.path.split(file_name)[1].split('.')[-1]}")
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
            logger.warning(f'{response.status_code} {response.reason}: Will always happen if server hash is wrong! Please check file and report to site owner that file hash might be wrong')
            # self.current_post_errors += 1
            return

        # might want to add try except to be able to Ctrl C and skip download
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

def check_version():
    try:
        current_version = datetime.datetime.strptime(__version__, r'%Y.%m.%d')
    except:
        current_version = datetime.datetime.strptime(__version__, r'%Y.%m.%d.%H')
    github_api_url = 'https://api.github.com/repos/AplhaSlayer1964/kemono-dl/releases/latest'
    responce = requests.get(url=github_api_url, timeout=TIMEOUT)
    if not responce.ok:
        logger.warning(f"Could not check github for latest release.")
        return
    latest_tag = responce.json()['tag_name']
    try:
        latest_version = datetime.datetime.strptime(latest_tag, r'%Y.%m.%d')
    except:
        latest_version = datetime.datetime.strptime(latest_tag, r'%Y.%m.%d.%H')
    if current_version < latest_version:
        logger.debug(f"Using kemono-dl {__version__} while latest release is kemono-dl {latest_tag}")
        logger.warning(f"A newer version of kemono-dl is available. Please update to the latest release at https://github.com/AplhaSlayer1964/kemono-dl/releases/latest")

def main():
    logger.debug(f"Given command: python {' '.join(sys.argv)}")
    check_version()
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