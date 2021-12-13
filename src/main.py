
import requests
import logging
import re
import os
import datetime
import time
from bs4 import BeautifulSoup
import json

from .arguments import get_args
from .downloader import download_yt_dlp, download_file
from .helper import check_post_archived, check_date, check_extention, win_folder_name, add_indexing, check_post_edited, print_info, print_error, print_separator, print_warning

args = get_args()

TIMEOUT = 180

class downloader:

    def __init__(self, urls:list = [], kfav_artists:bool = False, kfav_posts:bool = False, cfav_artists:bool = False, cfav_posts:bool = False):
        self.all_creators = self.get_all_creators()
        self.download_list = []
        for url in self.remove_duplicate_urls(urls):
            self.add_links(url)
        if kfav_artists:
            self.add_favorite_artists('kemono')
        if kfav_posts:
            self.add_favorite_posts('kemono')
        if cfav_artists:
            self.add_favorite_artists('coomer')
        if cfav_posts:
            self.add_favorite_posts('coomer')
        self.download()

    def add_links(self, url:str):
        found = re.search('^https://(kemono|coomer)\.party/([^/]+)/user/([^/]+)($|/post/([^/]+)$)', url)
        if found:
            username = self.find_username(user_id=found.group(3), service=found.group(2))
            U = user(domain=found.group(1), user_id=found.group(3), service=found.group(2) , username=username)
            # make check to see if user exists and if so just add needed posts
            if found.group(5):
                U.add_post_id(found.group(5))
            else:
                U.add_all_posts()
            if U in self.download_list:
                index = self.download_list.index(U)
                self.download_list[index].merge_posts(U)
            else:
                self.download_list.append(U)
        # print bad links?

    def add_favorite_artists(self, domain:str):
        headers = {'Accept': 'application/json'}
        fav_art_api_url = 'https://{}.party/api/favorites?type=artit'.format(domain)
        response = requests.get(url=fav_art_api_url, cookies=args['cookies'], headers=headers, timeout=TIMEOUT)
        if not response.ok:
            return
        for favorite in response.json():
            url = 'https://{domain}.party/{service}/user/{user}'.format(domain=domain,**favorite)
            self.add_links(url)

    def add_favorite_posts(self, domain:str):
        headers = {'Accept': 'application/json'}
        fav_art_api_url = 'https://{}.party/api/favorites?type=post'.format(domain)
        response = requests.get(url=fav_art_api_url, cookies=args['cookies'], headers=headers, timeout=TIMEOUT)
        if not response.ok:
            return
        for favorite in response.json():
            url = 'https://{domain}.party/{service}/user/{user}/post/{id}'.format(domain=domain,**favorite)
            self.add_links(url)

    def remove_duplicate_urls(self, urls:list):
        cleaned_urls = []
        for url in urls:
            if url.strip() not in cleaned_urls:
                cleaned_urls.append(url.strip())
        return cleaned_urls

    def merge_duplicate_users(self):
        # not really needed
        pass

    def find_username(self, user_id:str, service:str):
        for creator in self.all_creators:
            if creator['id'] == user_id and creator['service'] == service:
                return creator['name']

    def get_all_creators(self):
        headers = {'Accept': 'application/json'}
        creators_api_url = 'https://kemono.party/api/creators/'
        kemono_creator = requests.get(url=creators_api_url, headers=headers, timeout=TIMEOUT).json()
        creators_api_url = 'https://coomer.party/api/creators/'
        coomer_creators = requests.get(url=creators_api_url, headers=headers, timeout=TIMEOUT).json()
        return kemono_creator + coomer_creators

    def print_download_list_info(self):
        for user in self.download_list:
            user.print_user_info()
            print('*'*60)

    def download(self):
        for user in self.download_list:
            user_path = os.path.join(args['output'], user.service, '{} [{}]'.format(user.username, user.user_id))
            self.download_pfp_banner(user, user_path)
            for post in user.posts:
                post['domain'] = user.domain
                self.download_post(post, user_path)

    def download_pfp_banner(self, user, user_path:str):
        from PIL import Image
        from io import BytesIO

        for item in ['icon','banner']:
            url = 'https://{domain}.party/{}s/{service}/{user_id}'.format(item,
                                                                          domain=user.domain,
                                                                          service=user.service,
                                                                          user_id=user.user_id)
            response = requests.get(url, cookies=args['cookies'], timeout=TIMEOUT).content
            try:
                image = Image.open(BytesIO(response))
                if not os.path.exists(user_path):
                    os.makedirs(user_path)
                image.save(os.path.join(user_path, '{username} [{user_id}] {}.{ext}'.format(item,
                                                                                            ext=image.format.lower(),
                                                                                            username=user.username,
                                                                                            user_id=user.user_id)), format=image.format)
            except:
                pass


    # all class functions bellow here are old. might look at in future

    def save_inline(self, html, file_path, post, external = False):
        errors = 0
        print_info('Downloading inline images:')
        content_soup = BeautifulSoup(html, 'html.parser')
        inline_images = content_soup.find_all('img')
        for index, inline_image in enumerate(inline_images):
            kemono_hosted = re.search('^/[^*]+', inline_image['src'])
            if kemono_hosted:
                file_name = inline_image['src'].split('/')[-1] # might want to check content-disposition
                url = "https://{domain}.party/data{}".format(inline_image['src'], **post)
            else:
                if external: # can't think of a better way of doing this!
                    Content_Disposition = requests.head(inline_image['src']).headers.get('Content-Disposition', '')
                    file_name_CD = re.findall('filename="(.+)"', Content_Disposition)
                    file_name = inline_image['src'].split('?')[0].split('/')[-1]
                    if file_name_CD:
                        file_name = file_name_CD[0]
                    url = inline_image['src']
                else:
                    break
            if args['force_indexing']:
                file_name = add_indexing(index, file_name, inline_images)
            if download_file(url, file_name, os.path.join(file_path, 'inline'), args['retry_download']) == 0:
                inline_image['src'] = os.path.join(file_path, 'inline', file_name)
            else:
                errors += 1
        return (content_soup, errors)

    def save_attachments(self, post, post_path):
        errors = 0
        if post['attachments']:
            print_info('Downloading attachments:')
        for index, item in enumerate(post['attachments']):
            if args['force_indexing']:
                file_name = add_indexing(index, item['name'], post['attachments'])
            else:
                file_name = '{}'.format(item['name'])
            url = 'https://{domain}.party/data{path}'.format(**item, **post)
            file_path = os.path.join(post_path, 'attachments')
            if check_extention(file_name):
                file_hash = url.split('/')[-1].split('.')[0]
                errors += download_file(url, file_name, file_path, args['retry_download'], file_hash=file_hash, post=post)
        return errors

    def save_postfile(self, post, post_path):
        errors = 0
        if post['file']:
            print_info('Downloading post file:')
            file_name = post['file']['name']
            url = 'https://{domain}.party/data{path}'.format(domain=post['domain'], **post['file'])
            file_path = post_path
            if check_extention(file_name):
                file_hash = url.split('/')[-1].split('.')[0]
                errors += download_file(url, file_name, file_path, args['retry_download'], file_hash=file_hash, post=post)
        return errors

    def get_content_links(self, html, post_path, save = False, download = False):
        errors = 0
        content_soup = BeautifulSoup(html, 'html.parser')
        links = content_soup.find_all('a', href=True)
        for link in links:
            if save:
                print_info('Saving external content links: links.txt')
                with open(os.path.join(post_path, 'links.txt'),'a') as f:
                    f.write(link['href'] + '\n')
            if download:
                print_info('Downloading content links with yt_dlp')
                errors += download_yt_dlp(os.path.join(post_path, 'external files'), link['href'])
        return errors

    def save_content(self, post, post_path):
        errors = 0
        if post['content']:
            print_info('Saving content: content.html')
            result = self.save_inline(post['content'], post_path, post, args['force_inline'])
            errors += result[1]
            with open(os.path.join(post_path, 'content.html'),'wb') as File:
                File.write(result[0].prettify().encode("utf-16"))
            errors += self.get_content_links(post['content'], post_path, args['force_external'], args['force_yt_dlp'])
        return errors

    def save_embeds(self, post, post_path):
        errors = 0
        if post['embed']:
            print_info('Saving embeds: embeds.txt')
            with open(os.path.join(post_path, 'embed.txt'),'wb') as f:
                f.write('{subject}\n{url}\n{description}'.format(**post['embed']).encode('utf-8'))
            if args['yt_dlp']:
                print_info('Downloading embed with yt_dlp')
                errors += download_yt_dlp(os.path.join(post_path, 'embed'), post['embed']['url'])
        return errors

    def save_comments(self, post, post_path):
        # no api method to get comments so using from html (not future proof)
        url = 'https://{domain}.party/{service}/user/{user}/post/{id}'.format(**post)
        try:
            responce = requests.get(url=url, allow_redirects=True, cookies=args['cookies'], timeout=TIMEOUT)
            page_soup = BeautifulSoup(responce.text, 'html.parser')
            comment_html = page_soup.find("div", {"class": "post__comments"})
            if comment_html:
                not_supported = re.search('[^ ]+ does not support comment scraping yet\.',comment_html.text)
                if not not_supported:
                    print_info('Saving comments: comments.html')
                    with open(os.path.join(post_path, 'comments.html'),'wb') as f:
                        f.write(comment_html.prettify().encode("utf-16"))
            return 0
        except Exception as e:
            print_error('Could not get post comments: {}'.format(url))
            if args['ignore_errors']:
                return 1
            quit()


    def download_post(self, post:dict, user_path:str):

        print_info('Downloading Post: {title}'.format(**post))
        print_info('service: [{service}] user_id: [{user}] post_id: [{id}]'.format(**post))

        if post['published']:
            date = datetime.datetime.strptime(post['published'], r'%a, %d %b %Y %H:%M:%S %Z')
            date_string = date.strftime(r'%Y%m%d')
        else:
            date = datetime.datetime.min
            date_string = '00000000'

        post_path = os.path.join(user_path, win_folder_name('[{}] [{id}] {}'.format(date_string, post['title'], **post)))

        if check_post_archived(post):

            if check_post_edited(post, post_path):

                if not check_date(date):
                    print_info('Date out of range {}\n{}'.format(date_string, '-'*100))
                    return

                if args['post_timeout']:
                    print_info('Sleeping for {} seconds...'.format(args['post_timeout']))
                    time.sleep(args['post_timeout'])

                if not os.path.exists(post_path):
                    os.makedirs(post_path)

                errors = 0
                if not args['skip_attachments']:
                    errors += self.save_attachments(post, post_path)
                if not args['skip_postfile']:
                    errors += self.save_postfile(post, post_path)
                if not args['skip_content']:
                    errors += self.save_content(post, post_path)
                if not args['skip_comments']:
                    errors += self.save_comments(post, post_path)
                if not args['skip_embeds']:
                    errors += self.save_embeds(post, post_path)

                if errors == 0:
                    if not args['skip_json']:
                        print_info('Saving json: {id}.json'.format(**post))
                        with open(os.path.join(post_path,'{id}.json'.format(**post)),'w') as f:
                            json.dump(post, f)
                    if args['archive']:
                        with open(args['archive'],'a') as f:
                            f.write('/{service}/user/{user}/post/{id}\n'.format(**post))

                    print_info('Completed downloading post: {title}'.format(**post))
                    return
                print_warning('{} Errors encountered downloading post: {title}'.format(errors, **post))
                return
            print_info('Post already up to date: {title}'.format(**post))
            return
        print_info('Already archived post: {title}'.format(**post))
        return


class user():

    def __init__(self, domain:str, user_id:str, service:str, username:str):
        self.domain = domain
        self.user_id = user_id
        self.service = service
        self.username = username
        self.posts = []

    def __eq__(self, other:object):
        if self.domain == other.domain and self.user_id == other.user_id and self.service == other.service:
            return True
        return False

    def merge_posts(self, other:object):
        if self.domain == other.domain and self.user_id == other.user_id and self.service == other.service:
            for other_post in other.posts:
                if other_post not in self.posts:
                    self.posts.append(other_post)

    def print_user_info(self):
        print('Domain: {domain}.party\nUser ID: {user_id}\nService: {service}\nUsername: {username}\n# of Posts: {posts}'.format(domain=self.domain,
                                                                                                                           user_id=self.user_id,
                                                                                                                           service=self.service,
                                                                                                                           username=self.username,
                                                                                                                           posts=len(self.posts)))

    def add_post_id(self, post_id:str):
        headers = {'Accept': 'application/json'}
        post_api_url = 'https://{domain}.party/api/{service}/user/{user_id}/post/{post_id}'.format(domain=self.domain,
                                                                                          service=self.service,
                                                                                          user_id=self.user_id,
                                                                                          post_id=post_id)
        post_dict = requests.get(url=post_api_url, headers=headers, timeout=TIMEOUT).json()
        self.posts.append(post_dict[0])

    def add_all_posts(self):
        headers = {'Accept': 'application/json'}
        chunk = 0
        while True:
            user_api_url = 'https://{domain}.party/api/{service}/user/{user_id}?o={chunk}'.format(domain=self.domain,
                                                                                        service=self.service,
                                                                                        user_id=self.user_id,
                                                                                        chunk=chunk)
            response = requests.get(url=user_api_url, headers=headers, timeout=TIMEOUT).json()
            if not response:
                return
            for post_dict in response:
                self.posts.append(post_dict)
            chunk += 25

def main():
    input_list = []

    for link in args['links']:
        input_list.append(link)

    for link in args['fromfile']:
        input_list.append(link)

    d = downloader(input_list, kfav_artists=args['kemono_favorite_users'], kfav_posts=args['kemono_favorite_posts'])
