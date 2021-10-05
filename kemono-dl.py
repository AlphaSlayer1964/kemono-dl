import requests
import os
import re
from http.cookiejar import MozillaCookieJar
import argparse
import sys
import time
import datetime
import json

version = '2021.10.05'

ap = argparse.ArgumentParser()
ap.add_argument("--version", action='store_true', help="Displays the current version then exits")
ap.add_argument("--cookies", help="Set path to cookie.txt")
ap.add_argument("-u", "--user", help="Download user posts")
ap.add_argument("-p", "--post", help="Download post")
ap.add_argument("-f", "--fromfile", help="Download users and posts from a file")
ap.add_argument("-o", "--output", help="Set path to download posts")
ap.add_argument("-a", "--archive", help="Downloads only posts that are not in provided archive file")
ap.add_argument("-i", "--ignore-errors", action='store_true', help="Continue to download post(s) when an error occurs")
ap.add_argument("-s", "--simulate", action='store_true', help="Print post(s) info and does not download")
ap.add_argument("--date", help="Only download posts from this date")
ap.add_argument("--datebefore", help="Only download posts from this date and before")
ap.add_argument("--dateafter", help="Only download posts from this date and after")
# ap.add_argument("--min-filesize", help="Do not download files smaller than this")
# ap.add_argument("--max-filesize", help="Do not download files larger than this")
args = vars(ap.parse_args())

if args['version']:
    print(version), quit()

simulation_flag = False
if args['cookies']:
    if not os.path.exists(args['cookies']):
        print('Invalid cookie location: {}'.format(args['cookies'])), quit()
    cookie_jar = MozillaCookieJar(args['cookies'])
    cookie_jar.load()
else:
    simulation_flag = True
    
if args['simulate']:
    simulation_flag = True     

download_location = os.getcwd() + os.path.sep + 'Downloads' # default download location 
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
    # create archive file if none
    if not os.path.exists(args['archive']): 
        with open(args['archive'],'w') as f: 
            pass

def validate_date(date):
    try: datetime.datetime.strptime(date, '%Y%m%d')
    except: print("Incorrect data format, should be YYYYMMDD"), quit()   

check_date_flag = False      
if args['date']:
    validate_date(args['date'])
    check_date_flag = True

date_before = '00000000'
if args['datebefore']:
    validate_date(args['datebefore'])
    date_before = args['datebefore']
    check_date_flag = True

date_after = '99999999'
if args['dateafter']:
    validate_date(args['dateafter'])
    date_after = args['dateafter']
    check_date_flag = True
    
def date_check(post_date):
    if post_date == '':
        return False
    if args['date'] and (args['datebefore'] or args['dateafter']):
        if int(post_date) == int(args['date']) or int(post_date) <= int(date_before) or int(post_date) >= int(date_after):
            return True
        return False
    elif args['date']:
        if int(post_date) == int(args['date']):
            return True
        return False
    elif args['datebefore'] or args['dateafter']:
        if int(post_date) <= int(date_before) or int(post_date) >= int(date_after):
            return True
        return False
                
def download_file(file_name, file_link, file_path):
    try:
        # make sure file_path exists
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        # remove illegal windows characters from file name    
        file_name = re.sub('[\\/:\"*?<>|]+','',file_name) 
        # duplication checking
        if os.path.exists(file_path + os.path.sep + file_name):
            server_file_length = requests.head(file_path,allow_redirects=True, cookies=cookie_jar).headers['Content-Length']
            local_file_size = os.path.getsize(file_path + os.path.sep + file_name)
            if int(server_file_length) == int(local_file_size):
                print('Already downloaded: {}'.format(file_name))
                return True
        print('Downloading: {}'.format(file_name))
        # downloading the file     
        with requests.get(file_link, stream=True, cookies=cookie_jar) as r:
            r.raise_for_status()
            downloaded = 0
            total = int(r.headers.get('content-length'))
            with open(file_path + os.path.sep + file_name, 'wb') as f:
                start = time.time()
                for chunk in r.iter_content(chunk_size=max(int(total/1000), 1024*1024)): 
                    downloaded += len(chunk)
                    f.write(chunk)
                    done = int(50*downloaded/total)
                    sys.stdout.write('\r[{}{}] {}/{} MB, {} Mbps'.format('=' * done, ' ' * (50-done), round(downloaded/1000000,1), round(total/1000000,1), round(downloaded//(time.time() - start) / 100000,1)))
                    sys.stdout.flush() 
            sys.stdout.write('\n')
        return True
    except Exception as e:
        print('Error downloading: {}'.format(file_link))
        print(e)
        if args['ignore_errors']:
            return False
        quit()

def get_username(link):
    # using api patron posts don't have a username but a user id
    # https://www.patreon.com/user?u=
    pass

def simulate(post):
    print('Post Title: {title}\nPost ID: {id}\nUsername or User ID: {user}\nPublished Date: {published}\nContent: {content}'
            .format(title=post['title'],id=post['id'],user=post['user'],published=post['published'],content=post['content']))
    if post['embed']:
        print('Embedded:\n\tTitle: {title}\n\tURL: {url}\n\tDescription: {desc}'
                .format(title=post['embed']['subject'],url=post['embed']['url'],desc=post['embed']['description']))
    print('Number of attachments: {num_attachments}'.format(num_attachments=len(post['attachments'])))
    if post['attachments']:
        for item in post['attachments']:
            print('\tFile name: {name}\n\tFile path: https://kemono.party/data/{path}'
                    .format(name=item['name'],path=item['path']))
    if post['file']:
        print('Files:\n\tFile name: {name}\n\tFile Path: https://kemono.party/data/{path}'
              .format(name=post['file']['name'],path=post['file']['path']))
    print('{}'.format('-' * 50))    

def extract_post(link):
    api_responce = requests.get(link, allow_redirects=True)  
    data = json.loads(api_responce.text)
    for post in data:
        
        # post['title'] # post title
        # post['added'] # added to kemono
        # post['edited'] # last updated by kemono 
        # post['id'] # post id   
        # post['user'] # username or user id
        # post['published'] # published date (from service)
        # post['attachments'] # list of dictionaries each with a ['name'] and ['path']
        # post['file'] # dictionary of attached file ['name'] and ['path'] 
        # post['content'] # text content in html
        # post['shared_file'] # I have no idea what this holds
        # post['embed']: # dictionary for external link ['description'], ['subject'], ['url']
        
        try: 
            published_date = datetime.datetime.strptime(post['published'], r'%a, %d %b %Y %H:%M:%S %Z').strftime(r'%Y%m%d')
            post_folder_name =  '[{time}] [{post_id}] {title}'.format(time=published_date,post_id=post['id'],title=post['title'])
        except: 
            published_date = ''
            post_folder_name =  '[{post_id}] {title}'.format(post_id=post['id'],title=post['title'])
            
        if check_date_flag:
            if not date_check(published_date):
                print('Date out of range skipping post id: {id}'.format(id=post['id']))
                continue        
        
        if simulation_flag:
            simulate(post)
            continue
       
        post_folder_name = re.sub('[\\n\\t]+',' ', re.sub('[\\/:\"*?<>|]+','', post_folder_name )).strip('.').strip() 
        folder_path = download_location + os.path.sep + post['service'] + os.path.sep + post['user'] + os.path.sep + post_folder_name
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
        # need to look into how inline images are handled also no comments with api :/
        if not post['content'] == '':           
            with open(folder_path + os.path.sep + 'Content.html','wb') as File:
                File.write(post['content'].encode("utf-16"))
        
        if post['attachments']:
            for item in post['attachments']:
                download_file(item['name'], 'https://kemono.party/data{path}'.format(path=item['path']), folder_path + os.path.sep + 'attachments')
        
        if post['file']:
            download_file(post['file']['name'], 'https://kemono.party/data{path}'.format(path=post['file']['path']), folder_path) 
        
        if post['embed']:
            with open(folder_path + os.path.sep + 'external_links.tct','w') as File:
                File.write('{subject}:\t{url}\t{description}'.format(subject=post['embed']['subject'], url=post['embed']['url'], description=post['embed']['description']))  
    return

def user(link): 
    # /api/<service>/user/<id>   
    profile = re.search('https://kemono\.party/([^/]+)/user/([^/]+)$', link)        
    if profile:
        # user_link = link # will be need to get patreon user name?
        api_link = 'https://kemono.party/api/{service}/user/{user_id}'.format(service=profile.group(1), user_id=profile.group(2))
        extract_post(api_link)
        return True
    return False

def post(link):
    # /api/<service>/user/<id>/post/<id>
    post = re.search('(https://kemono\.party/([^/]+)/user/([^/]+))/post/([^/]+)$', link)
    if post:
        # user_link = post.group(1) # will be need to get patreon user name?
        api_link = 'https://kemono.party/api/{service}/user/{user_id}/post/{post_id}'.format(service=post.group(2), user_id=post.group(3),post_id=post.group(4))
        extract_post(api_link)
        return True
    return False    

def main():
    
    if args['user']:
        if not user(args['user']):
            print('Error invalid link: {}'.format(args['user']))
    
    if args['post']:    
        if not post(args['post']):
            print('Error invalid link: {}'.format(args['post']))
    
    if args['fromfile']:
        from_file = args['fromfile']  
        if not os.path.exists(from_file):
            print('No file found: {}'.format(from_file)), quit()
        with open(from_file,'r') as f:
            links = f.read().splitlines() 
        if len(links) == 0:
            print('{} is empty.'.format(from_file)), quit()       
        for link in links:
            if not post(link) and not user(link):
                print('Error invalid link: {}'.format(link))
            
            
if __name__ == '__main__':
    main()
    print('Done!')
