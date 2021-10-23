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
import yt_dlp

version = '2021.10.23.1'

ap = argparse.ArgumentParser()
ap.add_argument("--version", action='store_true', help="Displays the current version then exits")
ap.add_argument("--cookies", required=True, help="Set path to cookie.txt (REQUIRED)")
ap.add_argument("-l", "--links", help="Downloads user or post links seperated by a comma (,)")
ap.add_argument("-f", "--fromfile", help="Download users and posts from a file seperated by a newline")
ap.add_argument("-o", "--output", help="Set path to download posts")
ap.add_argument("-a", "--archive", help="Downloads only posts that are not in provided archive file")
ap.add_argument("-i", "--ignore-errors", action='store_true', help="Continue to download post(s) when an error occurs")
ap.add_argument("-s", "--simulate", action='store_true', help="Do not download users or posts and do not write to disk")
ap.add_argument("--date", help="Only download posts from this date. (Format: YYYYMMDD)")
ap.add_argument("--datebefore", help="Only download posts from this date and before. (Format: YYYYMMDD)")
ap.add_argument("--dateafter", help="Only download posts from this date and after. (Format: YYYYMMDD)")
ap.add_argument("--force-inline", action='store_true', help="Force download all external inline images found in post content. (experimental)")
ap.add_argument("--force-external", action='store_true', help="Save all external links in content to a text file")
ap.add_argument("--min-filesize", help="Do not download files smaller than this. (Format: 1GB, 1MB, 1KB, 1B)")
ap.add_argument("--max-filesize", help="Do not download files larger than this. (Format: 1GB, 1MB, 1KB, 1B)")
ap.add_argument("--skip-content", action='store_true', help="Skips creating content.html")
ap.add_argument("--skip-embeds", action='store_true', help="Skips creating embeds.txt")
ap.add_argument("--favorite-users", action='store_true', help="Downloads all users saved in your favorites. (Requires --cookies)")
ap.add_argument("--favorite-posts", action='store_true', help="Downloads all posts saved in your favorites. (Requires --cookies)")
ap.add_argument("--force-indexing", action='store_true', help="Adds an indexing value to the attachment file names to preserve ordering")
ap.add_argument("--yt-dlp", action='store_true', help="Tries to Download embeds with yt-dlp. (experimental)")
ap.add_argument("--force-yt-dlp", action='store_true', help="Tries to Download links in content with yt-dlp. (experimental)")
ap.add_argument("--skip-comments", action='store_true', help="Skips creating comments.html")
args = vars(ap.parse_args())

if args['version']: print(version), quit()

if args['cookies']:
    if not os.path.exists(args['cookies']):
        print('Invalid cookie location: {}'.format(args['cookies'])), quit()
    cookie_jar = MozillaCookieJar(args['cookies'])
    cookie_jar.load()   

if args['output']:
    if not os.path.exists(args['output']):
        print('Invalid download location: {}'.format(args['output'])), quit()
else:
    args['output'] = os.path.join(os.getcwd(), 'Downloads') # default download location

if args['archive']:
    if not os.path.exists(os.path.dirname(os.path.abspath(args['archive']))): # checks archive.txt location exists (file doesn't need to exist, will be created)
        print('Invalid archive location: {}'.format(os.path.dirname(os.path.abspath(args['archive'])))), quit()

def valid_date(date:str, name:str):
    try: 
        return datetime.datetime.strptime(date, r'%Y%m%d')  
    except: 
        print("Error incorrect data format for {}, should be YYYYMMDD".format(name)), quit()   
    
if args['date']: args['date'] = valid_date(args['date'], 'date')
if args['datebefore']: args['datebefore'] = valid_date(args['datebefore'], 'datebefore')
if args['dateafter']: args['dateafter'] = valid_date(args['dateafter'], 'dateafter')

def valid_size(size:str):
    giga = re.search('([0-9]+)GB', size)
    mega = re.search('([0-9]+)MB', size)
    kilo = re.search('([0-9]+)KB', size)
    byte = re.search('([0-9]+)B', size)
    if giga: return str(int(giga.group(1)) * 10**9)
    elif mega: return str(int(mega.group(1)) * 10**6)
    elif kilo: return str(int(kilo.group(1)) * 10**2)
    elif byte: return str(int(byte.group(1)))
    else: print("Error incorrect size format, should be 1GB, 1MB, 1KB, 1B"), quit()

if args['max_filesize']: args['max_filesize'] = valid_size(args['max_filesize'])
if args['min_filesize']: args['min_filesize'] = valid_size(args['min_filesize'])

def download_yt_dlp(path:str, link:str):
    ydl_opts = {
        "format" :"bestvideo+bestaudio",
        "outtmpl" : "{}/%(title)s.%(ext)s".format(path),
        "noplaylist" : True,
        "merge_output_format" : "mp4",
        "ignoreerrors" : True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])
    
def check_size(size:int):
    if not args['min_filesize'] and not args['max_filesize']: return True
    if size == 0: return False
    if not args['min_filesize']: args['min_filesize'] = '0'
    if not args['max_filesize']: args['max_filesize'] = 'inf'
    return True if size <= float(args['max_filesize']) and size >= int(args['min_filesize']) else False    
           
def download_file(file_name:str, url:str, file_path:str):
    file_name = re.sub('[\\/:\"*?<>|]+','',file_name) # remove illegal windows characters from file name (assume no file names are greater than 255)    
    print('Downloading: {}'.format(file_name))
    try:  
        with requests.get(url,stream=True,cookies=cookie_jar) as r:
            r.raise_for_status()
            downloaded = 0
            total = int(r.headers.get('content-length', '0'))
            if not check_size(total):
                print('File size out of range: {} bytes'.format(total))
                return True
            if args['simulate']:
                if total:
                    print('[{}] 0.0/{} MB, 0.0 Mbps'.format('='*50, round(total/1000000,1))) # fake download bar with correct filesize
                else:
                    print('[{}] 0.0/??? MB, 0.0 Mbps'.format('='*50))
                return True
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            with open(os.path.join(file_path, file_name), 'wb') as f: # if I removed the download bar this would be a bit cleaner
                start = time.time()
                for chunk in r.iter_content(chunk_size=max(int(total/1000), 1024*1024)):                   
                    downloaded += len(chunk)
                    f.write(chunk)
                    if total:
                        done = int(50*downloaded/total)
                        sys.stdout.write('\r[{}{}] {}/{} MB, {} Mbps'.format('='*done, ' '*(50-done), round(downloaded/1000000,1), round(total/1000000,1), round(downloaded//(time.time() - start) / 100000,1)))
                        sys.stdout.flush()
                    else:
                        sys.stdout.write('\r[{}] 0.0/??? MB, 0.0 Mbps'.format('='*50))
                        sys.stdout.flush()
            sys.stdout.write('\n')
        return True
    except Exception as e:
        print('Error downloading: {}'.format(url))
        print(e)
        if args['ignore_errors']:
            return False
        quit()        

def download_inline(html:str, file_path:str, external:bool):
    errors = 0
    content_soup = BeautifulSoup(html, 'html.parser')
    inline_images = content_soup.find_all('img')
    file_names = []
    for inline_image in inline_images:
        kemono_hosted = re.search('^/[^*]+', inline_image['src'])
        if kemono_hosted:
            file_name = inline_image['src'].split('/')[-1] # might want to check content-disposition
            link = "https://kemono.party/data{}".format(inline_image['src'])
        else:
            if external: # can't think of a better way of doing this!
                Content_Disposition = re.findall('filename="(.+)"', requests.head(inline_image['src'],allow_redirects=True).headers.get('Content-Disposition', ''))
                file_name = inline_image['src'].split('?')[0].split('/')[-1]
                if Content_Disposition:
                    file_name = Content_Disposition[0]
                extention = re.search('([^.]+)\.([^*]+)', file_name)
                if not extention:
                    print('Error downloading inline image: {}'.format(inline_image['src'])) # these errors will always be skipped
                    errors += 1
                    break   
                if file_name in file_names: # auto rename duplicate image names
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

def save_content_links(html:str, post_path:str, download:bool):
    content_soup = BeautifulSoup(html, 'html.parser')
    links = content_soup.find_all('a', href=True)
    if links:
        if args['force_external']:
            print('Saving external links in content to content_links.txt')        
            with open(os.path.join(post_path, 'content_links.txt'),'a') as f:
                for link in links:
                    f.write(link['href'] + '\n')
        if download:
            print('Trying to download content links with yt_dlp')
            for link in links:
                download_yt_dlp(os.path.join(post_path, 'external files'), link['href'])
    return

def save_comments(post:dict, post_path:str):
    # no api method to get comments so using from html (not future proof)
    page_html = requests.get('https://kemono.party/{service}/user/{user}/post/{id}'.format(**post), allow_redirects=True, cookies=cookie_jar)
    page_soup = BeautifulSoup(page_html.text, 'html.parser')                                   
    comment_html = page_soup.find("div", {"class": "post__comments"})
    if comment_html:
        not_supported = re.search('[^ ]+ does not support comment scraping yet\.',comment_html.text)
        if not not_supported:
            print('Saving comments to comments.html')
            if not args['simulate']:
                if not os.path.exists(post_path):
                    os.makedirs(post_path)
                with open(os.path.join(post_path, 'comments.html'),'wb') as f:
                    f.write(comment_html.prettify().encode("utf-16"))    
    return

def check_archived(post:dict):
    if args['archive']:
        if os.path.exists(args['archive']):
            with open(args['archive'],'r') as f:
                archived = f.read().splitlines()
            try:    
                if '/{service}/user/{user}/post/{id}'.format(**post) in archived:
                    return False
            except:
                if '/discord/server/{server}/channel/{id}'.format(**post) in archived:
                    return False            
    return True
        
def check_date(date):
    if not args['date'] and not args['datebefore'] and not args['dateafter']: return True
    if date == datetime.datetime.min: return False
    if not args['datebefore']: args['datebefore'] = datetime.datetime.min
    if not args['dateafter']: args['dateafter'] = datetime.datetime.max
    if not args['date']: args['date'] = datetime.datetime.min
    return True if date == args['date'] or date <= args['datebefore'] or date >= args['dateafter'] else False

def save_post(post:dict, info:dict):

    print('Downloading post: {title}'.format(**post))
    print('service: [{service}] user_id: [{user}] post_id: [{id}]'.format(**post))
    
    if check_archived(dict(post)):
        
        try: 
            date = datetime.datetime.strptime(post['published'], r'%a, %d %b %Y %H:%M:%S %Z')
            date_string = date.strftime(r'%Y%m%d')   
        except: 
            date = datetime.datetime.min
            date_string = '00000000'        
        
        if not check_date(date):
            print('Date out of range {}\n{}'.format(date_string, '-'*100)) 
            return
        
        errors = 0
        
        post_title = re.sub('[\\n\\t]+',' ', re.sub('[\\/:\"*?<>|]+','', post['title'] )).strip('.').strip() # removing illegal windows characters
        post_folder = '[{}] [{id}] {}'.format(date_string, post_title, **post)[:248].strip() # shorten folder name length for windows 
        post_path = os.path.join(info['path'], post_folder)
        
        for index, item in enumerate(post['attachments']):
            file_name = '{}'.format(item['name'])
            if args['force_indexing']:
                if len(post['attachments']) < 10:
                    file_name = '[{:01d}]_{}'.format(index+1, item['name'])
                elif len(post['attachments']) < 100:
                    file_name = '[{:02d}]_{}'.format(index+1, item['name'])
                else:
                    file_name = '[{:03d}]_{}'.format(index+1, item['name'])
            errors += 0 if download_file(file_name, 'https://kemono.party/data{path}'.format(**item), os.path.join(post_path, 'attachments')) else 1
            # extract zip files?
                
        if post['file']:
            errors += 0 if download_file(post['file']['name'], 'https://kemono.party/data{path}'.format(**post['file']), post_path) else 1

        if post['content'] and not args['skip_content']:
            if not args['simulate']: 
                print('Saving content to content.html')
                result = download_inline(post['content'], post_path, args['force_inline'])
                errors += result[1]  
                if not os.path.exists(post_path):
                    os.makedirs(post_path)                
                with open(os.path.join(post_path, 'content.html'),'wb') as File:
                    File.write(result[0].prettify().encode("utf-16"))
                save_content_links(post['content'], post_path, args['force_yt_dlp'])
                
        if post['embed'] and not args['skip_embeds']:
            print('Saving embeds to embeds.txt')
            if not args['simulate']:
                if not os.path.exists(post_path):
                    os.makedirs(post_path)
                with open(os.path.join(post_path, 'embeds.txt'),'wb') as f:
                    f.write('{subject}\n{url}\n{description}'.format(**post['embed']).encode("utf-16"))
                if args['yt_dlp']:
                    print('Trying to download embed with yt_dlp')
                    download_yt_dlp(os.path.join(post_path, 'external files'), post['embed']['url'])     
        
        if not args['skip_comments']:               
            save_comments(dict(post), post_path)
                    
        if not errors:
            if not args['simulate']:
                with open(os.path.join(post_path,'{id}.json'.format(**post)),'w') as f:
                    json.dump(post, f)           
                if args['archive']:
                    with open(args['archive'],'a') as f:
                        f.write('/{service}/user/{user}/post/{id}\n'.format(**post))
            print('Completed downloading post: {title}\n{}'.format('-'*100, **post)) 
            return    
        print('{} Error(s) encountered downloading post: {title}\n{}'.format(errors, '-'*100, **post)) 
        return
    print('Already archived post: {title}\n{}'.format('-'*100, **post)) 
    return 

# no testing has been done with this code!
def save_channel(post:dict, info:dict, channel:dict):
    pass

    # print('Downloading post: {channel}'.format(**post)) 
    # print('service: [discord] server_id: [{user}] channel_id: [{id}]'.format(**post))    
    
    # if check_archived(dict(post)):
        
    #     errors = 0
    #     # download images
    #     # save links to file    
    #     # format into html file
    #     if not errors:           
    #         if args['archive']:
    #             with open(args['archive'],'a') as f:
    #                 f.write('/discord/server/{server}/channel/{id}'.format(**post))
    #         print('Completed downloading channel: {channel}\n{}'.format('-'*100, **post)) 
    #         return    
    #     print('{} Error(s) encountered downloading channel: {channel}\n{}'.format(errors, '-'*100, **post)) 
    #     return
    # print('Already archived channel: {channel}\n{}'.format('-'*100, **post)) 
    # return

def get_posts(info:dict):
    chunk = 0
    while True:
        if info['post_id'] == None:
            api_call = 'https://kemono.party/api/{service}/user/{user_id}?o={}'.format(chunk, **info)
        else:
            api_call = 'https://kemono.party/api/{service}/user/{user_id}/post/{post_id}'.format(**info)
        api_response = requests.get(api_call)
        api_response.raise_for_status()
        data = json.loads(api_response.text)
        for post in data:
            save_post(dict(post), dict(info))
        if info['post_id'] or not data:
            return
        chunk += 25    
    
def get_channels(info:dict):
    for channel in info['channels']:
        skip = 0
        while True:
            api_call = 'https://kemono.party/api/discord/channel/{id}?skip={}'.format(skip, **channel) 
            api_response = requests.get(api_call)
            api_response.raise_for_status()
            data = json.loads(api_response.text)
            for post in data:
                save_channel(dict(post), dict(info), dict(channel))
            if not data:
                break
            skip += 10    
    return

def get_channel_ids(info:dict):
    api_call = 'https://kemono.party/api/discord/channels/lookup?q={}'.format(info['user_id'])
    api_response = requests.get(api_call)
    api_response.raise_for_status()
    return json.loads(api_response.text)

def get_icon_banner(info:dict):
    if info['post_id'] == None and not info['service'] == 'discord':
        for item in ['icon','banner']: 
            file_name = '{username} [{user_id}] {}'.format(item, **info)
            if download_file(file_name, 'https://kemono.party/{}s/{service}/{user_id}'.format(item, **info), info['path']):
                try:
                    with Image.open(os.path.join(info['path'], file_name)) as image:
                        image.save(os.path.join(info['path'], '{}.{}'.format(file_name, image.format.lower())), format=image.format)
                except: pass
                if os.path.exists(os.path.join(info['path'], file_name)):
                    os.remove(os.path.join(info['path'], file_name))
    return   

def get_username(service:str, user_id:str):
    api_call = 'https://kemono.party/api/creators/'
    api_response = requests.get(api_call)
    api_response.raise_for_status()
    for creator in json.loads(api_response.text):
        if creator['id'] == user_id and creator['service'] == service:
            return re.sub('[\\/:\"*?<>|]+','', creator['name']) # removing illegal windows characters

def extract_link(link:str):
    found = re.search('https://kemono\.party/([^/]+)/(server|user)/([^/]+)($|/post/([^/]+)$)',link)
    if found:
        info = {'service':found.group(1),
                'user_id':found.group(3), # holds server_id for discord
                'post_id':found.group(5),
                'username': get_username(found.group(1), found.group(3))}
        info['path'] = os.path.join(args['output'], info['service'], '{username} [{user_id}]'.format(**info))
        if info['service'] == 'discord':
            return False
            info['channels'] = get_channel_ids(info)
        else:
            get_icon_banner(dict(info))
            get_posts(dict(info))
        return True
    return False    

def get_favorites(type:str):
    api_call = 'https://kemono.party/api/favorites?type={}'.format(type)
    api_response = requests.get(api_call, cookies=cookie_jar)
    if not api_response.ok:
        print('Error getting favorite {}s. Session might have expired, re-log in to kemono.party and get a new cookies.txt'.format(type))
        return
    data = json.loads(api_response.text)
    for favorite in data:
        if type == 'post':
            extract_link('https://kemono.party/{service}/user/{user}/post/{id}'.format(**favorite))
        elif type == 'artist':
            extract_link('https://kemono.party/{service}/user/{id}'.format(**favorite))
    if not data:
        print('You have no favorite {}s.'.format(type))
    return
        
def main():
    
    if args['favorite_users']:
        get_favorites('artist')
        
    if args['favorite_posts']:
        get_favorites('post')
        
    if args['links']:
        links = args['links'].split(",")
        for link in links:
            if not extract_link(link.lstrip().strip().split('?')[0]):
                print('Error invalid link: {}'.format(link))
                
    if args['fromfile']:
        if not os.path.exists(args['fromfile']):
            print('Error no file found: {}'.format(args['fromfile'])), quit()
            
        with open(args['fromfile'],'r') as f:
            links = f.readlines()
        if not links:
            print('Error {} is empty.'.format(args['fromfile'])), quit()       
        
        for link in links:
            if not extract_link(link.lstrip().strip().split('?')[0]):
                print('Error invalid link: {}'.format(link.strip()))
            
if __name__ == '__main__':
    main()
    print('Done!')
