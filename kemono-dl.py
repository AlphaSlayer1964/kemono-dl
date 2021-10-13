import requests
import os
import re
import argparse
import sys
import time
import datetime
import json
from PIL import Image
from bs4 import BeautifulSoup
from http.cookiejar import MozillaCookieJar

version = '2021.10.13'

ap = argparse.ArgumentParser()
ap.add_argument("--version", action='store_true', help="Displays the current version then exits")
ap.add_argument("--cookies", help="Set path to cookie.txt (REQUIRED TO DOWNLOAD FILES)")
ap.add_argument("-l", "--links", help="Downloads user or post links seperated by a comma (,)")
ap.add_argument("-f", "--fromfile", help="Download users and posts from a file seperated by a newline")
ap.add_argument("-o", "--output", help="Set path to download posts")
ap.add_argument("-a", "--archive", help="Downloads only posts that are not in provided archive file")
ap.add_argument("-i", "--ignore-errors", action='store_true', help="Continue to download post(s) when an error occurs")
ap.add_argument("-s", "--simulate", action='store_true', help="Print post(s) info and does not download")
ap.add_argument("--date", help="Only download posts from this date. (Format: YYYYMMDD)")
ap.add_argument("--datebefore", help="Only download posts from this date and before. (Format: YYYYMMDD)")
ap.add_argument("--dateafter", help="Only download posts from this date and after. (Format: YYYYMMDD)")
ap.add_argument("--force-inline", action='store_true', help="Force download all external inline images found in post content. (experimental)")
ap.add_argument("--min-filesize", help="Do not download files smaller than this. (Format: 1GB, 1MB, 1KB, 1B)")
ap.add_argument("--max-filesize", help="Do not download files larger than this. (Format: 1GB, 1MB, 1KB, 1B)")
ap.add_argument("--skip-content", action='store_true', help="Skips creating content.html")
ap.add_argument("--skip-embeds", action='store_true', help="Skips creating external_links.txt")
ap.add_argument("--favorite-users", action='store_true', help="Downloads all users saved in your favorites. (Requires --cookies)")
ap.add_argument("--favorite-posts", action='store_true', help="Downloads all posts saved in your favorites. (Requires --cookies)")
# ap.add_argument("-up", "--update", action='store_true', help="Redownloads any post that has been updated (ignores --archive)") # might need to create a log file of kemono.party last edit time
args = vars(ap.parse_args())

if args['version']: print(version), quit()

simulation_flag = False
if args['cookies']:
    if not os.path.exists(args['cookies']):
        print('Invalid cookie location: {}'.format(args['cookies'])), quit()
    cookie_jar = MozillaCookieJar(args['cookies'])
    cookie_jar.load()
else:
    simulation_flag = True
    
if args['simulate']: simulation_flag = True     

download_location = os.path.join(os.getcwd(), 'Downloads') # default download location 
if args['output']:
    if not os.path.exists(args['output']):
        print('Invalid download location: {}'.format(args['output'])), quit()
    download_location = args['output']  

archive_flag = False
if args['archive']:
    if not os.path.exists(os.path.dirname(os.path.abspath(args['archive']))):
        print('Invalid archive location: {}'.format(os.path.dirname(os.path.abspath(args['archive'])))), quit()
    archive_flag = True
    archive_file = args['archive']

def valid_date(date:str):
    try: datetime.datetime.strptime(date, r'%Y%m%d')  
    except: print("Error incorrect data format, should be YYYYMMDD"), quit()
    return True   
     
if args['date']: valid_date(args['date'])
if args['datebefore']: valid_date(args['datebefore'])
if args['dateafter']: valid_date(args['dateafter'])

def valid_size(size:str):
    giga = re.search('([0-9]+)GB', size)
    mega = re.search('([0-9]+)MB', size)
    kilo = re.search('([0-9]+)KB', size)
    byte = re.search('([0-9]+)B', size)
    if giga: return int(giga.group(1)) * 10**9
    elif mega: return int(mega.group(1)) * 10**6
    elif kilo: return int(kilo.group(1)) * 10**2
    elif byte: return int(byte.group(1))
    else: print("Error incorrect size format, should be 1GB, 1MB, 1KB, 1B"), quit()

if args['max_filesize']: args['max_filesize'] = valid_size(args['max_filesize'])
if args['min_filesize']: args['min_filesize'] = valid_size(args['min_filesize'])
    
def check_date(date:str):
    if not args['date'] and not args['datebefore'] and not args['dateafter']: return True
    if date == '00000000': return False
    if not args['datebefore']: args['datebefore'] = '0'
    if not args['dateafter']: args['dateafter'] = float('inf')
    if not args['date']: args['date'] = '0'
    return True if int(date) == int(args['date']) or int(date) <= int(args['datebefore']) or int(date) >= float(args['dateafter']) else False
    
def check_size(size:int):
    if not args['min_filesize'] and not args['max_filesize']: return True
    if size == 0: return False
    if not args['min_filesize']: args['min_filesize'] = '0'
    if not args['max_filesize']: args['max_filesize'] = float('inf')
    return True if size <= float(args['max_filesize']) and size >= int(args['min_filesize']) else False    
           
def download_file(file_name:str, url:str, file_path:str):
    try:
        file_name = re.sub('[\\/:\"*?<>|]+','',file_name) # remove illegal windows characters from file name
        print('Downloading: {}'.format(file_name))    
        with requests.get(url,stream=True,cookies=cookie_jar) as r:
            r.raise_for_status()
            downloaded = 0
            total = int(r.headers.get('content-length', '0'))
            if not check_size(total):
                print('File size out of range: {} bytes'.format(total))
                return True
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            with open(os.path.join(file_path, file_name), 'wb') as f:
                start = time.time()
                for chunk in r.iter_content(chunk_size=max(int(total/1000), 1024*1024)):                   
                    downloaded += len(chunk)
                    f.write(chunk)
                    if total:
                        done = int(50*downloaded/total)
                        sys.stdout.write('\r[{}{}] {}/{} MB, {} Mbps'.format('=' * done, ' ' * (50-done), round(downloaded/1000000,1), round(total/1000000,1), round(downloaded//(time.time() - start) / 100000,1)))
                        sys.stdout.flush() 
            if total:
                sys.stdout.write('\n')
        return True
    except Exception as e:
        print('Error downloading: {}'.format(url))
        print(e)
        if not args['ignore_errors']:
            quit()
        return False

def download_inline(html:str, file_path:str, external:bool):
    errors = 0
    content_soup = BeautifulSoup(html, 'html.parser')
    inline_images = content_soup.find_all('img')
    file_names = []
    for inline_image in inline_images:
        kemono_hosted = re.search('^/[^*]+', inline_image['src'])
        if kemono_hosted:
            file_name = inline_image['src'].split('/')[-1]
            link = "https://kemono.party/data{}".format(inline_image['src'])
        else:
            if external:
                # auto renamer for duplicate inline image names (for non kemono.party hosted images)
                try: Content_Disposition = re.findall('filename="(.+)"', requests.head(inline_image['src'],allow_redirects=True).headers.get('Content-Disposition', ''))
                except: Content_Disposition = ''
                file_name = link.split('?')[0].split('/')[-1]
                if Content_Disposition:
                    file_name = Content_Disposition[0]
                extention = re.search('([^.]+)\.([^*]+)', file_name)
                if not extention:
                    print('Error downloading inline image: {}'.format(inline_image['src'])) # these errors will always be skipped
                    errors += 1
                    break
                if file_name in file_names:
                    count = 1
                    while re.sub("\.","({}).".format(count), file_name) in file_names:
                        count += 1
                    file_name = re.sub("\.","({}).".format(count), file_name)
                file_names.append(file_name)
                link = inline_image['src']
            else:
                break
        if download_file(file_name, link, os.path.join(file_path, 'inline')):
            inline_image['src'] = os.path.join(file_path, 'inline', file_name)
        else:
            errors += 1
    return  (content_soup, errors)      
    
def print_post_data(post:dict):
    print('Post Link: https://kemono.party/{service}/user/{user}/{id}'.format(**post))
    print('Post Title: {title}\nPost ID: {id}\nUser ID: {user}\nService: {service}\nPublished Date: {published}\nAdded Date: {added}\nEdited Date: {edited}'.format(**post))
    if post['embed']:
        print('Embedded:\n\tSubject: {subject}\n\tURL: {url}\n\tDescription: {description}'.format(**post['embed']))
    if post['attachments']:
        print('Attachments: {}'.format(len(post['attachments'])))
        for attachment in post['attachments']:
            print('\tFile name: {name}\n\tFile path: https://kemono.party/data/{path}'.format(**attachment))
    if post['file']:
        print('Files:\n\tFile name: {name}\n\tFile Path: https://kemono.party/data/{path}'.format(**post['file']))
    print('Content:\n{}'.format(BeautifulSoup(post['content'], 'html.parser').getText(separator="\n")))
    print('-' * 50)     

def extract_post(post:dict, info:dict):
    """
    post                    # dict      
        ['title']           # str 
        ['added']           # str, datetime object
        ['edited']          # str, datetime object
        ['id']              # str
        ['user']            # str
        ['published']       # str, datetime object
        ['attachments']     # list of dict
            ['name']        # str
            ['path']        # str
        ['file']            # dict
            ['name']        # str
            ['path']        # str 
        ['content']         # str, html
        ['shared_file']     # bool 
        ['embed']:          # dict
            ['description'] # str
            ['subject']     # str
            ['url']         # str
    """
    errors = 0
    info['post_id'] = post['id']
    
    archived = []
    if archive_flag and os.path.exists(archive_file):
        with open(archive_file,'r') as f:
            archived = f.read().splitlines() 
               
    if not '{service} {user_id} {post_id}'.format(**info) in archived:
        
        try: date = datetime.datetime.strptime(post['published'], r'%a, %d %b %Y %H:%M:%S %Z').strftime(r'%Y%m%d')   
        except: date = '00000000'
        
        if not check_date(date):
            print('Date out of range: {} service: [{service}] user_id: [{user_id}] post_id: [{post_id}]'.format(date, **info))
            return        
    
        if simulation_flag:
            print_post_data(post)
            return
    
        post_title = re.sub('[\\n\\t]+',' ', re.sub('[\\/:\"*?<>|]+','', post['title'] )).strip('.').strip() # removing illegal windows characters
        post_path = os.path.join(download_location, info['service'], '{username} [{user_id}]'.format(**info), '[{}] [{post_id}] {}'.format(date, post_title, **info))
        
        if post['content'] and not args['skip_content']:
            if not os.path.exists(post_path):
                os.makedirs(post_path)
            result = download_inline(post['content'], post_path, args['force_inline'])
            errors += result[1]
            with open(os.path.join(post_path, 'content.html'),'wb') as File:
                File.write(result[0].prettify().encode("utf-16"))
                
        for item in post['attachments']:
            errors += 1 if not download_file(item['name'], 'https://kemono.party/data{path}'.format(**item), os.path.join(post_path, 'attachments')) else 0
                
        if post['file']:
            errors += 1 if not download_file(post['file']['name'], 'https://kemono.party/data{path}'.format(**post['file']), post_path) else 0
                 
        if post['embed'] and not args['skip_embeds']:
            if not os.path.exists(post_path):
                os.makedirs(post_path)
            with open(os.path.join(post_path, 'external_links.txt'),'wb') as f:
                f.write('{subject}\n{url}\n{description}'.format(**post['embed']).encode("utf-16"))
                           
        if not errors:
            if archive_flag:
                with open(archive_file,'a') as f:
                    f.write('{service} {user_id} {post_id}\n'.format(**info))
            print("Completed downloading post. service: [{service}] user_id: [{user_id}] post_id: [{post_id}]".format(**info))
            return    
        print('{} Error(s) encountered downloading post. service: [{service}] user_id: [{user_id}] post_id: [{post_id}]'.format(errors, **info))
        return
    print("Already archived post. service: [{service}] user_id: [{user_id}] post_id: [{post_id}]".format(**info))
    return    

def print_channel_post_data(post:dict):
    for key, value in post.items():
        print(key, ' : ', value)
    print('-' * 50)
    return  

def extract_channel_post(post:dict, info:dict, channel:dict):
    """
    channel                     # dict
        ['id']                  # str
        ['name']                # str
        
    post                        # dict
        ['added']               # str, datetime object
        ['attachments']         # list of dict
            ['isImage']         # str
            ['name']            # str
            ['path']            # str
        ['author']              # dict   
            ['avatar']          # str
            ['discriminator']   # str
            ['id']              # str
            ['public_flags']    # int
            ['username']        # str
        ['channel']             # str
        ['content']             # str, html
        ['edited']              # ???
        ['embeds']              # list of dict
            ['description']     # str
            ['thumbnail']       # dict
                ['height']      # int
                ['proxy_url']   # str
                ['url']         # str
                ['width']       # int
            ['title']           # str
            ['type']            # str
            ['url']             # str
        ['id']                  # str
        ['mentions']            # list of dict
            ['avatar']          # str
            ['discriminator']   # str
            ['id']              # str
            ['public_flags']    # int
            ['username']        # str    
        ['published']           # str, datetime object
        ['server]               # str
    """
    if simulation_flag:
        print_channel_post_data(post)
        return
    # format into html file    
    return

def get_discord_chanels(info:dict):
    api_call = 'https://kemono.party/api/discord/channels/lookup?q={}'.format(info['user_id'])
    api_responce = requests.get(api_call) 
    return json.loads(api_responce.text)

def get_posts(info:dict):
    if info['service'] == 'discord':
        print('Saving Discords is still being developed')
        return
    channels = get_discord_chanels(dict(info)) if info['service'] == 'discord' else [0]
    for channel in channels:
        chunk = 0
        while True:
            api_call = 'https://kemono.party/api/{service}/user/{user_id}/post/{post_id}'.format(**info)
            if info['post_id'] == None:
                api_call = 'https://kemono.party/api/{service}/user/{user_id}?o={}'.format(chunk, **info)
                if info['service'] == 'discord':
                    api_call = 'https://kemono.party/api/discord/channel/{id}?skip={}'.format(chunk, **channel) 
            api_responce = requests.get(api_call) 
            data = json.loads(api_responce.text)
            if not data:
                break
            for post in data:
                if info['service'] == 'discord':
                    extract_channel_post(dict(post), dict(info), dict(channel))
                else:
                    extract_post(dict(post), dict(info))
            if not info['post_id'] == None and not info['service'] == 'discord':
                break
            chunk += 10 if info['service'] == 'discord' else 25    
    return

def get_pfp_banner(info:dict):
    list = ['icon', 'banner']
    if info['service'] == 'gumroad': # gumroad does not have banners and when calling /baners/ you just get the icon again
        list = ['icon']
    elif info['service'] == 'discord':
        list = [] 
    folder_path = os.path.join(download_location, info['service'], '{username} [{user_id}]'.format(**info))    
    for item in list:
        file_name = '{username} [{user_id}] {}'.format(item, **info)
        if download_file(file_name, 'https://kemono.party/{}s/{service}/{user_id}'.format(item, **info).format(**info), folder_path):
            try:
                with Image.open(os.path.join(folder_path, file_name)) as image:
                    image.save(os.path.join(folder_path, '{}.{}'.format(file_name, image.format.lower())), format=image.format)
            except: pass
            if os.path.exists(os.path.join(folder_path, file_name)):
                os.remove(os.path.join(folder_path, file_name))
    return

def get_username(service:str, user_id:str):
    api_creators = 'https://kemono.party/api/creators/'
    api_responce = requests.get(api_creators)
    data = json.loads(api_responce.text)
    for creator in data:
        """
        creator            # dict
            ['id']         # str
            ['indexed']    # str 
            ['name']       # str
            ['service']    # str
            ['updated']    # str
        """
        if creator['id'] == user_id and creator['service'] == service:
            return re.sub('[\\/:\"*?<>|]+','', creator['name']) # removing illegal windows characters

def extract_link(link:str):
    found = re.search('https://kemono\.party/([^/]+)/(server|user)/([^/]+)($|/post/([^/]+)$)',link)
    if found:
        info = {'service':found.group(1),
                'user_id':found.group(3),
                'post_id':found.group(5),
                'username': get_username(found.group(1), found.group(3))}
        if not simulation_flag and info['post_id'] == None:
            get_pfp_banner(dict(info))
        get_posts(dict(info))
        return True
    return False    

def get_favorite_users():
    try:
        api_favorites = 'https://kemono.party/api/favorites?type=artist'
        api_responce = requests.get(api_favorites, cookies=cookie_jar)
        api_responce.raise_for_status()
        data = json.loads(api_responce.text)
        if not data:
            print('You have no favorite users.')
            return
        for favorite_user in data:
            """
            favorite_user       # dict
                ['faved_seq']   # int
                ['id']          # str
                ['indexed']     # str, datetime object
                ['name']        # str
                ['service']     # str
                ['updated']     # str, datetime object
            """
            extract_link('https://kemono.party/{service}/user/{id}'.format(**favorite_user))
        return
    except:
        print('Error getting favorite users. Session might have expired, login to kemono.party then get cookies.txt')
        return

def get_favorite_posts():
    try:
        api_favorites = 'https://kemono.party/api/favorites?type=post'
        api_responce = requests.get(api_favorites, cookies=cookie_jar)
        api_responce.raise_for_status()
        data = json.loads(api_responce.text)
        if not data:
            print('You have no favorite posts.')
            return
        for favorite_post in data:
            """
            favorite_post       # dict, same as post
                ['faved_seq']   # int
            """
            extract_link('https://kemono.party/{service}/user/{user}/post/{id}'.format(**favorite_post))
        return
    except:
        print('Error getting favorite posts. Session might have expired, login to kemono.party then get cookies.txt')
        return

def main():
    
    if args['favorite_users']:
        get_favorite_users()
        
    if args['favorite_posts']:
        get_favorite_posts()
        
    if args['links']:
        links = args['links'].split(",")
        for link in links:
            if not extract_link(link.lstrip()):
                print('Error invalid link: {}'.format(link))
                
    if args['fromfile']:
        if not os.path.exists(args['fromfile']):
            print('Error no file found: {}'.format(args['fromfile'])), quit()
            
        with open(args['fromfile'],'r') as f:
            links = f.readlines()
        if not links:
            print('Error {} is empty.'.format(args['fromfile'])), quit()       
        
        for link in links:
            if not extract_link(link.strip()):
                print('Error invalid link: {}'.format(link.strip()))
            
if __name__ == '__main__':
    main()
    print('Done!')
