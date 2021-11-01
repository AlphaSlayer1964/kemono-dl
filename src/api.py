import requests
import re
import json
import os
import datetime
import time
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .arguments import get_args
from .downloader import download_yt_dlp, download_file
from .helper import check_post_archived, check_date, check_extention, win_folder_name, add_indexing, check_post_edited, print_info, print_error, print_separator, print_warning

args = get_args()

TIMEOUT = 120

retry_strategy = Retry(
    total = 8,
    backoff_factor = 1,
    status_forcelist = [429, 500, 502, 503, 504],
    allowed_methods = False,
    raise_on_status = True
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)

def save_inline(html, file_path, external = False):
    errors = 0
    print_info('Downloading inline images:')
    content_soup = BeautifulSoup(html, 'html.parser')
    inline_images = content_soup.find_all('img')
    for index, inline_image in enumerate(inline_images):
        kemono_hosted = re.search('^/[^*]+', inline_image['src'])
        if kemono_hosted:
            file_name = inline_image['src'].split('/')[-1] # might want to check content-disposition
            url = "https://kemono.party/data{}".format(inline_image['src'])
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

def save_attachments(post, post_path):
    errors = 0
    print_info('Downloading attachments:')
    for index, item in enumerate(post['attachments']):
        if args['force_indexing']:
            file_name = add_indexing(index, item['name'], post['attachments'])
        else:
            file_name = '{}'.format(item['name'])
        url = 'https://kemono.party/data{path}'.format(**item)
        file_path = os.path.join(post_path, 'attachments')
        if check_extention(file_name):
            file_hash = url.split('/')[-1].split('.')[0]
            errors += download_file(url, file_name, file_path, args['retry_download'], file_hash=file_hash)
    return errors

def save_postfile(post, post_path):
    errors = 0
    print_info('Downloading post file:')
    if post['file']:
        file_name = post['file']['name']
        url = 'https://kemono.party/data{path}'.format(**post['file'])
        file_path = post_path
        if check_extention(file_name):
            file_hash = url.split('/')[-1].split('.')[0]
            errors += download_file(url, file_name, file_path, args['retry_download'], file_hash=file_hash)
    return errors

def get_content_links(html, post_path, save = False, download = False):
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

def save_content(post, post_path):
    errors = 0
    if post['content']:
        print_info('Saving content: content.html')
        result = save_inline(post['content'], post_path, args['force_inline'])
        errors += result[1]
        with open(os.path.join(post_path, 'content.html'),'wb') as File:
            File.write(result[0].prettify().encode("utf-16"))
        errors += get_content_links(post['content'], post_path, args['force_external'], args['force_yt_dlp'])
    return errors

def save_embeds(post, post_path):
    errors = 0
    if post['embed']:
        print_info('Saving embeds: embeds.txt')
        with open(os.path.join(post_path, 'embed.txt'),'wb') as f:
            f.write('{subject}\n{url}\n{description}'.format(**post['embed']).encode('utf-8'))
        if args['yt_dlp']:
            print_info('Downloading embed with yt_dlp')
            errors += download_yt_dlp(os.path.join(post_path, 'embed'), post['embed']['url'])
    return errors

def save_comments(post, post_path):
    # no api method to get comments so using from html (not future proof)
    url = 'https://kemono.party/{service}/user/{user}/post/{id}'.format(**post)
    try:
        responce = session.get(url=url, allow_redirects=True, cookies=args['cookies'], timeout=TIMEOUT)
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

def save_post(post, info):

    print_info('Downloading Post: {title}'.format(**post))
    print_info('service: [{service}] user_id: [{user}] post_id: [{id}]'.format(**post))

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
                print_info('Date out of range {}\n{}'.format(date_string, '-'*100))
                return

            if args['post_timeout']:
                print_info('Sleeping for {} seconds...'.format(args['post_timeout']))
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

def save_channel(post, info, channel):
    pass

def get_post(info):
    url = 'https://kemono.party/api/{service}/user/{id}/post/{post_id}'.format(**info)
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    for post in response.json():
        save_post(dict(post), dict(info))
        print_separator()

def get_user(info):
    print_info('Downloading User: {username}'.format(**info))
    print_info('service: [{service}] user_id: [{id}]'.format(**info))

    if not args['skip_pfp_banner']:
        save_icon_banner(info)

    chunk = 0
    while True:
        url = 'https://kemono.party/api/{service}/user/{id}?o={}'.format(chunk, **info)
        response = session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        if not response.json():
            return
        for post in response.json():
            save_post(dict(post), dict(info))
            print_separator()
        chunk += 25

def get_channels(info):
    for channel in info['channels']:
        skip = 0
        while True:
            url = 'https://kemono.party/api/discord/channel/{id}?skip={}'.format(skip, **channel)
            response = session.get(url, timeout=TIMEOUT)
            for post in response.json():
                save_channel(dict(post), dict(info), dict(channel))
            if not response.json():
                break
            skip += 10

def save_icon_banner(info):
    from PIL import Image
    from io import BytesIO

    if info['service'] in ('discord','dlsite'):
        print_error('icon and banner not supported by discord or dslite.')
        return
    for item in ['icon','banner']:
        if info['service'] == 'gumroad' and item == 'banner':
            return
        if not os.path.exists(info['path']):
            os.makedirs(info['path'])
        print('[Downloading] User {}.'.format(item))
        url = 'https://kemono.party/{}s/{service}/{id}'.format(item, **info)
        response = requests.get(url, cookies=args['cookies'], timeout=TIMEOUT)
        try:
            image = Image.open(BytesIO(response.content))
            image.save(os.path.join(info['path'], '{username} [{id}] {}.{}'.format(item, image.format.lower(), **info)), format=image.format)
        except:
            print_error('Unable to get user {}.'.format(item))

def get_channel_ids(info):
    url = 'https://kemono.party/api/discord/channels/lookup?q={}'.format(info['id'])
    response = session.get(url, timeout=TIMEOUT)
    return response.json()

def get_username(info):
    url = 'https://kemono.party/api/creators/'
    response = session.get(url, timeout=TIMEOUT)
    for creator in response.json():
        if creator['id'] == info['id'] and creator['service'] == info['service']:
            return creator['name']

def extract_link_info(link):
    found = re.search('https://kemono\.party/([^/]+)/(server|user)/([^/]+)($|/post/([^/]+)$)',link)
    info = {'username':None,'service':None,'id':None,'post_id':None,'channels':None,'path':None}
    if found:
        info['service'] = found.group(1)
        info['id'] = found.group(3)
        info['post_id'] = found.group(5) # None for users
        info['username'] = get_username(info)
        info['path'] = os.path.join(args['output'], info['service'], win_folder_name('{username} [{id}]'.format(**info)))
        if info['service'] == 'discord':
            return False
            info['channels'] = get_channel_ids(info)
            get_channels(info)
        elif info['post_id'] == None:
            get_user(info)
        else:
            get_post(info)
        return True
    return False

def get_favorites(type):
    url = 'https://kemono.party/api/favorites?type={}'.format(type)
    response = session.get(url, cookies=args['cookies'], timeout=TIMEOUT)
    if not response.ok:
        print_error('Can not get favorite {}s. Session might have expired, re-log in to kemono.party and get a new cookies.txt'.format(type))
        return
    for favorite in response.json():
        if type == 'post':
            extract_link_info('https://kemono.party/{service}/user/{user}/post/{id}'.format(**favorite))
        elif type == 'artist':
            extract_link_info('https://kemono.party/{service}/user/{id}'.format(**favorite))
    if not response.json():
        print_warning('You have no favorite {}s.'.format(type))