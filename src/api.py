import requests
import re
import json
import os
import datetime
import time
from PIL import Image
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .arguments import get_args
from .downloader import download_yt_dlp, download_file
from .helper import check_post_archived, check_date, check_extention, win_folder_name, add_indexing, check_post_edited

args = get_args()

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

def save_inline(html, file_path, external = False):
    errors = 0
    print('Downloading inline images.')
    content_soup = BeautifulSoup(html, 'html.parser')
    inline_images = content_soup.find_all('img')
    for index, inline_image in enumerate(inline_images):
        kemono_hosted = re.search('^/[^*]+', inline_image['src'])
        if kemono_hosted:
            file_name = inline_image['src'].split('/')[-1] # might want to check content-disposition
            link = "https://kemono.party/data{}".format(inline_image['src'])
        else:
            if external: # can't think of a better way of doing this!
                Content_Disposition = requests.head(inline_image['src'],allow_redirects=True).headers.get('Content-Disposition', '')
                file_name_CD = re.findall('filename="(.+)"', Content_Disposition)
                file_name = inline_image['src'].split('?')[0].split('/')[-1]
                if file_name_CD:
                    file_name = file_name_CD[0]
                link = inline_image['src']
            else:
                break
        if args['force_indexing']:
            file_name = add_indexing(index, file_name, inline_images)
        if download_file(file_name, link, os.path.join(file_path, 'inline'), args['retry_download']) == 0:
            inline_image['src'] = os.path.join(file_path, 'inline', file_name)
        else:
            errors += 1
    return  (content_soup, errors)

def save_attachments(post, post_path):
    errors = 0
    print('Downloading attachments.')
    for index, item in enumerate(post['attachments']):
        if args['force_indexing']:
            file_name = add_indexing(index, item['name'], post['attachments'])
        else:
            file_name = '{}'.format(item['name'])
        url = 'https://kemono.party/data{path}'.format(**item)
        file_path = os.path.join(post_path, 'attachments')
        if check_extention(file_name):
            errors += download_file(file_name, url, file_path, args['retry_download'])
    return errors

def save_postfile(post, post_path):
    errors = 0
    print('Downloading post file.')
    if post['file']:
        file_name = post['file']['name']
        url = 'https://kemono.party/data{path}'.format(**post['file'])
        file_path = post_path
        if check_extention(file_name):
            errors += download_file(file_name, url, file_path, args['retry_download'])
    return errors

def get_content_links(html, post_path, save = False, download = False):
    errors = 0
    content_soup = BeautifulSoup(html, 'html.parser')
    links = content_soup.find_all('a', href=True)
    for link in links:
        if save:
            print('Saving external links in content to links.txt')
            with open(os.path.join(post_path, 'links.txt'),'a') as f:
                f.write(link['href'] + '\n')
        if download:
            print('Trying to download content links with yt_dlp')
            errors += download_yt_dlp(os.path.join(post_path, 'external files'), link['href'])
    return errors

def save_content(post, post_path):
    errors = 0
    if post['content']:
        print('Saving content to content.html')
        result = save_inline(post['content'], post_path, args['force_inline'])
        errors += result[1]
        with open(os.path.join(post_path, 'content.html'),'wb') as File:
            File.write(result[0].prettify().encode("utf-16"))
        errors += get_content_links(post['content'], post_path, args['force_external'], args['force_yt_dlp'])
    return errors

def save_embeds(post, post_path):
    errrors = 0
    if post['embed']:
        print('Saving embeds to embeds.txt')
        with open(os.path.join(post_path, 'embed.txt'),'w') as f:
            f.write('{url}'.format(**post['embed']))
        if args['yt_dlp']:
            print('Trying to download embed with yt_dlp')
            errrors += download_yt_dlp(os.path.join(post_path, 'embed'), post['embed']['url'])
    return errrors

def save_comments(post, post_path):
    # no api method to get comments so using from html (not future proof)
    try:
        page_html = s.get('https://kemono.party/{service}/user/{user}/post/{id}'.format(**post), allow_redirects=True, cookies=args['cookies'])
        page_html.raise_for_status()
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        comment_html = page_soup.find("div", {"class": "post__comments"})
        if comment_html:
            not_supported = re.search('[^ ]+ does not support comment scraping yet\.',comment_html.text)
            if not not_supported:
                print('Saving comments to comments.html')
                with open(os.path.join(post_path, 'comments.html'),'wb') as f:
                    f.write(comment_html.prettify().encode("utf-16"))
        return 0
    except Exception as e:
        print('Error getting comments')
        print(e)
        if args['ignore_errors']:
            return 1
        quit()

def save_post(post, info):

    print('Downloading post: {title}'.format(**post))
    print('service: [{service}] user_id: [{user}] post_id: [{id}]'.format(**post))

    if post['published']:
        date = datetime.datetime.strptime(post['published'], r'%a, %d %b %Y %H:%M:%S %Z')
        date_string = date.strftime(r'%Y%m%d')
    else:
        date = datetime.datetime.min
        date_string = '00000000'

    post_path = os.path.join(info['path'], win_folder_name('[{}] [{id}] {}'.format(date_string, post['title'], **post)))

    if check_post_archived(post):

        if check_post_edited(post, post_path):

            if not check_date(date):
                print('Date out of range {}\n{}'.format(date_string, '-'*100))
                return

            time.sleep(args['post_timeout'])

            if not os.path.exists(post_path):
                os.makedirs(post_path)

            errors = 0
            if not args['skip_attachments']:
                errors += save_attachments(post, post_path)
            if not args['skip_postfile']:
                errors += save_postfile(post, post_path)
            if not args['skip_content']:
                errors += save_content(post, post_path)
            if not args['skip_comments']:
                errors += save_comments(post, post_path)
            if not args['skip_embeds']:
                errors += save_embeds(post, post_path)
            if not args['skip_json']:
                with open(os.path.join(post_path,'{id}.json'.format(**post)),'w') as f:
                    json.dump(post, f)

            if errors == 0:
                if args['archive']:
                    with open(args['archive'],'a') as f:
                        f.write('/{service}/user/{user}/post/{id}\n'.format(**post))

                print('Completed downloading post: {title}'.format(**post))
                return

            print('[{} Errors] encountered downloading post: {title}'.format(errors, **post))
            return

        print('Post already up to date: {title}'.format(**post))
        return

    print('Already archived post: {title}'.format(**post))
    return

def save_channel(post, info, channel):
    pass

def get_post(info):
    api_call = 'https://kemono.party/api/{service}/user/{user_id}/post/{post_id}'.format(**info)
    api_response = s.get(api_call)
    api_response.raise_for_status()
    data = json.loads(api_response.text)
    for post in data:
        save_post(dict(post), dict(info))
        print('-'*100)
    return

def get_user(info):
    print('Downloading posts for user: {username}'.format(**info))
    print('service: [{service}] user_id: [{user_id}]'.format(**info))

    if not args['skip_pfp_banner']:
        save_icon_banner(info)

    chunk = 0
    while True:
        api_call = 'https://kemono.party/api/{service}/user/{user_id}?o={}'.format(chunk, **info)
        api_response = s.get(api_call)
        api_response.raise_for_status()
        data = json.loads(api_response.text)
        if not data:
            return
        for post in data:
            save_post(dict(post), dict(info))
            print('-'*100)
        chunk += 25

def get_channels(info):
    # for channel in info['channels']:
    #     skip = 0
    #     while True:
    #         api_call = 'https://kemono.party/api/discord/channel/{id}?skip={}'.format(skip, **channel)
    #         api_response = s.get(api_call)
    #         api_response.raise_for_status()
    #         data = json.loads(api_response.text)
    #         for post in data:
    #             save_channel(dict(post), dict(info), dict(channel))
    #         if not data:
    #             break
    #         skip += 10
    return

def save_icon_banner(info):
    for item in ['icon','banner']:
        file_name = '{username} [{user_id}] {}'.format(item, **info)
        url = 'https://kemono.party/{}s/{service}/{user_id}'.format(item, **info)
        file_path = info['path']
        if download_file(file_name, url, file_path, args['retry_download']) == 0:
            try:
                with Image.open(os.path.join(info['path'], file_name)) as image:
                    image.save(os.path.join(info['path'], '{}.{}'.format(file_name, image.format.lower())), format=image.format)
            except:
                pass
            if os.path.exists(os.path.join(info['path'], file_name)):
                os.remove(os.path.join(info['path'], file_name))
        else:
            print('[Error] unable to get user {}'.format(item))
    return

def get_channel_ids(info):
    api_call = 'https://kemono.party/api/discord/channels/lookup?q={}'.format(info['server_id'])
    api_response = s.get(api_call)
    api_response.raise_for_status()
    return json.loads(api_response.text)

def get_username(info):
    api_call = 'https://kemono.party/api/creators/'
    api_response = s.get(api_call)
    api_response.raise_for_status()
    for creator in json.loads(api_response.text):
        if creator['id'] == info['user_id'] and creator['service'] == info['service']:
            return creator['name']

def extract_link_info(link):
    found = re.search('https://kemono\.party/([^/]+)/(server|user)/([^/]+)($|/post/([^/]+)$)',link)
    info = {'service':None,'user_id':None,'post_id':None,'username':None,'path':None,'server_id':None,'Channels':None}
    if found:
        info['service'] =found.group(1)
        if info['service'] == 'discord':
            info['server_id'] = found.group(3)
            info['channels'] = get_channel_ids(info)
            info['path'] = ''
        else:
            info['user_id'] = found.group(3)
            info['post_id'] = found.group(5) # None for users
            info['username'] = get_username(info)
            info['path'] = os.path.join(args['output'], info['service'], win_folder_name('{username} [{user_id}]'.format(**info)))

        if info['service'] == 'discord':
            return False

        if info['post_id'] == None:
            get_user(info)
            return True

        get_post(info)
        return True

    return False

def get_favorites(type):
    api_call = 'https://kemono.party/api/favorites?type={}'.format(type)
    api_response = s.get(api_call, cookies=args['cookies'])
    if not api_response.ok:
        print('Error getting favorite {}s. Session might have expired, re-log in to kemono.party and get a new cookies.txt'.format(type))
        return
    data = json.loads(api_response.text)
    for favorite in data:
        if type == 'post':
            extract_link_info('https://kemono.party/{service}/user/{user}/post/{id}'.format(**favorite))
        elif type == 'artist':
            extract_link_info('https://kemono.party/{service}/user/{id}'.format(**favorite))
    if not data:
        print('You have no favorite {}s.'.format(type))
    return