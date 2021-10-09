import requests
from bs4 import BeautifulSoup
from http.cookiejar import MozillaCookieJar
import os
import re
import argparse
import sys
import time
import datetime
import json
from PIL import Image

version = '2021.10.08.1'

ap = argparse.ArgumentParser()
ap.add_argument("--version", action='store_true', help="Displays the current version then exits")
ap.add_argument("--cookies", help="Set path to cookie.txt (REQUIRED TO DOWNLOAD FILES)")
ap.add_argument("-l", "--links", help="Downloads user or post links seperated by a comma (,)")
ap.add_argument("-f", "--fromfile", help="Download users and posts from a file seperated by a newline")
ap.add_argument("-o", "--output", help="Set path to download posts")
ap.add_argument("-a", "--archive", help="Downloads only posts that are not in provided archive file")
ap.add_argument("-i", "--ignore-errors", action='store_true', help="Continue to download post(s) when an error occurs")
ap.add_argument("-s", "--simulate", action='store_true', help="Print post(s) info and does not download")
ap.add_argument("--date", help="Only download posts from this date")
ap.add_argument("--datebefore", help="Only download posts from this date and before")
ap.add_argument("--dateafter", help="Only download posts from this date and after")
ap.add_argument("--force-inline", action='store_true', help="Force download all external inline images found in post content")
# ap.add_argument("--min-filesize", help="Do not download files smaller than this")
# ap.add_argument("--max-filesize", help="Do not download files larger than this")
# ap.add_argument("-up", "--update", action='store_true', help="Redownloads any post that has been updated (ignores --archive)")
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
    if not os.path.exists(archive_file): 
        with open(archive_file,'w') as f: 
            pass

def validate_date(date):
    try: 
        datetime.datetime.strptime(date, r'%Y%m%d')
        return True
    except: 
        print("Error incorrect data format, should be YYYYMMDD"), quit()   

check_date_flag = False      
if args['date']: check_date_flag = validate_date(args['date'])

if args['datebefore']: check_date_flag = validate_date(args['datebefore'])

if args['dateafter']: check_date_flag = validate_date(args['dateafter'])
    
def check_date(post_date, date, date_before, date_after):
    if post_date == '00000000': return False
    if date_before == None: date_before = '00000000'
    if date_after == None: date_after = '99999999'
    if date and (date_before or date_after):
        return True if int(post_date) == int(date) or int(post_date) <= int(date_before) or int(post_date) >= int(date_after) else False
    elif date:
        return True if int(post_date) == int(date) else False
    elif date_before or date_after:
        return True if int(post_date) <= int(date_before) or int(post_date) >= int(date_after) else False
                
def download_file(file_name, url, file_path):
    try:
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        file_name = re.sub('[\\/:\"*?<>|]+','',file_name) # remove illegal windows characters from file name
        print('Downloading: {}'.format(file_name))    
        with requests.get(url,stream=True,cookies=cookie_jar) as r:
            r.raise_for_status()
            downloaded = 0
            total = int(r.headers.get('content-length', 0))
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
        print('Error downloading: {link}'.format(link=url))
        print(e)
        if not args['ignore_errors']:
            quit()
        return False

def download_inline(html, file_path, external):
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
                    print('Error downloading inline image: {}'.format(inline_image['src']))
                    # if not args['ignore_errors']:
                    #     quit()
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
    
def simulate(post):
    print('Post Title: {title}\nPost ID: {id}\nUser ID: {user}\nService: {service}\nPublished Date: {published}\nContent: {content}\n'.format(**post))
    if post['embed']:
        print('Embedded:\n\tSubject: {subject}\n\tURL: {url}\n\tDescription: {description}'.format(**post['embed']))
    if post['attachments']:
        print('Attachments: {}'.format(len(post['attachments'])))
        for attachment in post['attachments']:
            print('\tFile name: {name}\n\tFile path: https://kemono.party/data/{path}'.format(**attachment))
    if post['file']:
        print('Files:\n\tFile name: {name}\n\tFile Path: https://kemono.party/data/{path}'.format(**post['file']))
    print('-' * 50)   

def extract_post(post, info):
    """        
    post['title']         # str, post title
    post['added']         # str, date added
    post['edited']        # str, date last editied
    post['id']            # str, post id
    post['user']          # str, user id
    post['published']     # str, date published
    post['attachments']   # list of dict, {"name": str, "path": str}
    post['file']          # dict, {"name": str, "path": str} 
    post['content']       # str, html of content
    post['shared_file']   # bool, 
    post['embed']:        # dict, {"description": str, "subject": str, "url": str}, external link
    """
    archived = []
    if archive_flag:
        with open(archive_file,'r') as f:
            archived = f.read().splitlines() 
               
    errors = 0
    info['post_id'] = post['id']
         
    if not '{service} {user_id} {post_id}'.format(**info) in archived:
        
        try: date = datetime.datetime.strptime(post['published'], r'%a, %d %b %Y %H:%M:%S %Z').strftime(r'%Y%m%d')   
        except: date = '00000000'
        
        if check_date_flag:
            if not check_date(date, args['date'], args['datebefore'], args['dateafter']):
                print('Date out of range: {date} service: {service} user id: {user_id} post id: {pos_id}'.format(**info, date=date))
                return        
    
        if simulation_flag:
            simulate(post)
            return
    
        post_title = re.sub('[\\n\\t]+',' ', re.sub('[\\/:\"*?<>|]+','', post['title'] )).strip('.').strip() # removing illegal windows characters
        post_path = os.path.join(download_location, info['service'], '{username} [{user_id}]'.format(**info), '[{}] [{post_id}] {}'.format(date, post_title, **info))
        if not os.path.exists(post_path):
            os.makedirs(post_path)
                
        if not post['content'] == '':
            result = download_inline(post['content'], post_path, args['force_inline'])
            errors += result[1]
            # write content to file 
            with open(os.path.join(post_path, 'content.html'),'wb') as File:
                File.write(result[0].prettify().encode("utf-16"))
                
        # download post attachments
        for item in post['attachments']:
            errors += 1 if not download_file(item['name'], 'https://kemono.party/data{path}'.format(**item), os.path.join(post_path, 'attachments')) else 0
                
        # download post file
        if post['file']:
            errors += 1 if not download_file(post['file']['name'], 'https://kemono.party/data{path}'.format(**post['file']), post_path) else 0
                 
                
        # save embedded links
        if post['embed']:
            with open(os.path.join(post_path, 'external_links.txt'),'wb') as f:
                f.write('{subject}\n{url}\n{}'.format(post['embed']['description'].encode("utf-16"), **post['embed']))
                
        # check total errors            
        if not errors:
            if archive_flag:
                with open(archive_file,'a') as f:
                    f.write('{service} {user_id} {post_id}\n'.format(**info))
            print("Completed downloading post. service: {service} user id: {user_id} post id: {post_id}".format(**info))
            return    
        print('{} Error(s) encountered downloading post. service: {service} user id: {user_id} post id: {post_id}'.format(errors, **info))
        return
    print("Already archived post. service: {service} user id: {user_id} post id: {pos_id}".format(**info))
    return    
    
def get_posts(info):
    chunk = 0
    next_chunk = True
    while next_chunk:
        api_link = 'https://kemono.party/api/{service}/user/{user_id}/post/{post_id}'.format(**info) # /api/<service>/user/<id>/post/<id>
        if info['post_id'] == None:
            api_link = 'https://kemono.party/api/{service}/user/{user_id}?o={}'.format(chunk, **info) # /api/<service>/user/<id>
        api_responce = requests.get(api_link)  
        data = json.loads(api_responce.text)
        if not data:
            break
        for post in data:
            extract_post(post, dict(info)) 
        if not info['post_id'] == None:
            break
        chunk += 25
    return

def get_pfp_banner(info):
    list = ['icon', 'banner']
    if info['service'] == 'gumroad': # gumroad does not have banners and when calling /baners/ you just get the icon again
        list = ['icon'] 
    folder_path = os.path.join(download_location, info['service'], '{username} [{user_id}]'.format(**info))    
    for item in list:
        # /icons/{service}/{creator_id} 
        # /banners/{service}/{creator_id}
        file_name = '{username} [{user_id}] {}'.format(item, **info)
        download_file(file_name, 'https://kemono.party/{}s/{service}/{user_id}'.format(item, **info).format(**info), folder_path)
        try:
            image = Image.open(os.path.join(folder_path, file_name))
            image.save(os.path.join(folder_path, '{}.{}'.format(file_name, image.format.lower())), format=image.format)
            os.remove(os.path.join(folder_path, file_name)) 
        except:
            os.remove(os.path.join(folder_path, file_name)) # site might return garbage data if no icon or banner is found

def get_discord():
    print('Discord is not currently supported by this downloader. (in progress)')
    # /discord/server/{serverId}
    # serverId is same as creator id for getting username
    # how to get channel id(s) from server id with api?
    # api_channel = 'https://kemono.party/api/discord/channel/{channelId}?skip={skip}'
    # skip starts at 0 increments by 10
    pass

def get_username(service, user_id):
    api_creators = 'https://kemono.party/api/creators/'
    api_responce = requests.get(api_creators)
    data = json.loads(api_responce.text)
    for creator in data:
        """
        creator['id']         # str
        creator['indexed']    # str 
        creator['name']       # str
        creator['service']    # str
        creator['updated']    # str
        """
        if creator['id'] == user_id and creator['service'] == service:
            return re.sub('[\\/:\"*?<>|]+','', creator['name']) # removing illegal windows characters

def extract_link(link):
    found = re.search('https://kemono\.party/([^/]+)/(server|user)/([^/]+)($|/post/([^/]+)$)',link)
    if found:
        info = {'service':found.group(1), 'user_id':found.group(3), 'post_id':found.group(5), 'username': get_username(found.group(1), found.group(3))}
        if info['service'] == 'discord':
            get_discord(info)
            return True
        if not simulation_flag:
            get_pfp_banner(info)
        get_posts(info)
        return True
    return False    

def main():
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
