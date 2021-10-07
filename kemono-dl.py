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
import io

version = '2021.10.07.3'

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
# ap.add_argument("--min-filesize", help="Do not download files smaller than this")
# ap.add_argument("--max-filesize", help="Do not download files larger than this")
# ap.add_argument("-up", "--update", action='store_true', help="Redownloads any post that has been updated (ignores --archive)")
args = vars(ap.parse_args())

if args['version']:
    print(version), quit()

simulation_flag = False
if args['cookies']:
    if not os.path.exists(args['cookies']):
        print('Invalid cookie location: {path}'.format(path=args['cookies'])), quit()
    cookie_jar = MozillaCookieJar(args['cookies'])
    cookie_jar.load()
else:
    simulation_flag = True
    
if args['simulate']:
    simulation_flag = True     

download_location = os.getcwd() + os.path.sep + 'Downloads' # default download location 
if args['output']:
    if not os.path.exists(args['output']):
        print('Invalid download location: {path}'.format(path=args['output'])), quit()
    download_location = args['output']  

archive_flag = False
if args['archive']:
    if not os.path.exists(os.path.dirname(os.path.abspath(args['archive']))):
        print('Invalid archive location: {path}'.format(path=os.path.dirname(os.path.abspath(args['archive'])))), quit()
    archive_flag = True
    archive_file = args['archive']
    # create archive file if none
    if not os.path.exists(archive_file): 
        with open(archive_file,'w') as f: 
            pass

def validate_date(date):
    try: datetime.datetime.strptime(date, r'%Y%m%d')
    except: print("Error incorrect data format, should be YYYYMMDD"), quit()   

check_date_flag = False      
if args['date']:
    validate_date(args['date'])
    check_date_flag = True

if args['datebefore']:
    validate_date(args['datebefore'])
    check_date_flag = True

if args['dateafter']:
    validate_date(args['dateafter'])
    check_date_flag = True
    
def date_check(post_date, date, date_before, date_after):
    if post_date == '00000000':
        return False
    if date_before == None:
        date_before = '00000000'
    if date_after == None:
        date_after = '99999999'
    if date and (date_before or date_after):
        return True if int(post_date) == int(date) or int(post_date) <= int(date_before) or int(post_date) >= int(date_after) else False
    elif date:
        return True if int(post_date) == int(date) else False
    elif date_before or date_after:
        return True if int(post_date) <= int(date_before) or int(post_date) >= int(date_after) else False

def print_error(string):
    print('{cstart}{string}{cstop}'.format(string=string,cstart='\033[91m',cstop='\033[0m'))
                
def download_file(file_name, file_link, file_path):
    try:
        if not os.path.exists(file_path): # make sure file path exists
            os.makedirs(file_path)
        file_name = re.sub('[\\/:\"*?<>|]+','',file_name) # remove illegal windows characters from file name
        print('Downloading: {}'.format(file_name))    
        with requests.get(file_link,stream=True,cookies=cookie_jar) as r:
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
        print_error('Error downloading: {link}'.format(link=file_link))
        print(e)
        if not args['ignore_errors']:
            quit()
        return False

def download_inline(html, file_path, external):
    error_flag = 0
    content_soup = BeautifulSoup(html, 'html.parser')
    inline_images = content_soup.find_all('img')
    file_names = []
    for inline_image in inline_images:
        kemono_hosted = re.search('^/[^*]+', inline_image['src'])
        if kemono_hosted:
            file_name = inline_image['src'].split('/')[-1]
            link = "https://kemono.party/data{path}".format(path=inline_image['src'])
        elif external: # redo downloading and renaming external inline images
            # auto renamer for duplicate inline image names (for non kemono.party hosted images) might not be best in long run
            try: 
                file_name = re.findall('filename="(.+)"', requests.head(inline_image['src'],allow_redirects=True).headers['Content-Disposition'])[0]
                if file_name in file_names:
                    count = 1
                    while re.sub("\.","({num}).".format(num=count), file_name) in file_names:
                        count += 1
                    file_name = re.sub("\.","({num}).".format(num=count), file_name)
                file_names.append(file_name)
                link = inline_image['src']
            except Exception as e:
                print_error('Error downloading: {link}'.format(link=inline_image['src']))
                print(e)
                if not args['ignore_errors']:
                    quit()
                error_flag += 1    
                continue
        if download_file(file_name, link, file_path + os.path.sep + 'inline'):
            inline_image['src'] = file_path + os.path.sep + 'inline' + os.path.sep + file_name
        else:
            error_flag += 1
    return  (content_soup, error_flag)      
    
def simulate(post, username):
    print('Post Title: {title}\nPost ID: {id}\nUsername: {username}\nUser ID: {user}\nPublished Date: {published}\nContent: {content}\n'.format(title=post['title'],id=post['id'],username=username,user=post['user'],published=post['published'],content=post['content']))
    if post['embed']:
        print('Embedded:\n\tTitle: {title}\n\tURL: {url}\n\tDescription: {desc}'.format(title=post['embed']['subject'],url=post['embed']['url'],desc=post['embed']['description']))
    if post['attachments']:
        print('Attachments: {len}'.format(len=len(post['attachments'])))
        for item in post['attachments']:
            print('\tFile name: {name}\n\tFile path: https://kemono.party/data/{path}'.format(name=item['name'],path=item['path']))
    if post['file']:
        print('Files:\n\tFile name: {name}\n\tFile Path: https://kemono.party/data/{path}'.format(name=post['file']['name'],path=post['file']['path']))
    print('{}'.format('-' * 50))    

def extract_post(post, username):
    error_flag = 0
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
            
    if not '{user_id} {post_id}'.format(user_id=post['user'],post_id=post['id']) in archived:

        # convert date and time from API to YYYYMMDD
        try: date = datetime.datetime.strptime(post['published'], r'%a, %d %b %Y %H:%M:%S %Z').strftime(r'%Y%m%d')   
        except: date = '00000000'
        
        if check_date_flag:
            if not date_check(date, args['date'], args['datebefore'], args['dateafter']):
                print('Date out of range: {date} skipping post id: {pos_id} user id: {user_id}'.format(date=date,pos_id=post['id'],user_id=post['user']))
                return        
    
        if simulation_flag:
            simulate(post, username)
            return
    
        post_folder_name =  '[{date}] [{post_id}] {title}'.format(date=date, post_id=post['id'], title=post['title'])
        post_folder_name = re.sub('[\\n\\t]+',' ', re.sub('[\\/:\"*?<>|]+','', post_folder_name )).strip('.').strip() # removing illegal windows characters
        folder_path = download_location + os.path.sep + post['service'] + os.path.sep + username + ' [{user_id}]'.format(user_id=post['user']) + os.path.sep + post_folder_name
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)    
        if not post['content'] == '':
            result = download_inline(post['content'], folder_path, False)
            error_flag += result[1]
            # write content to file 
            with open(folder_path + os.path.sep + 'content.html','wb') as File:
                File.write(result[0].prettify().encode("utf-16"))
        # download post attachments
        for item in post['attachments']:
            if not download_file(item['name'], 'https://kemono.party/data{path}'.format(path=item['path']),folder_path + os.path.sep + 'attachments'):
                error_flag += 1
        # download post file
        if post['file']:
            if not download_file(post['file']['name'], 'https://kemono.party/data{path}'.format(path=post['file']['path']), folder_path):
                error_flag += 1 
        # save embedded links
        if post['embed']:
            with open(folder_path + os.path.sep + 'external_links.txt','wb') as File:
                File.write('{subject}\n{url}\n{description}'.format(subject=post['embed']['subject'],url=post['embed']['url'],description=post['embed']['description']).encode("utf-16"))
        # check total errors            
        if not error_flag:
            if archive_flag:
                with open(archive_file,'a') as f:
                    f.write('{user_id} {post_id}\n'.format(user_id=post['user'],post_id=post['id']))
            print("Completed downloading post id: {post_id} user id: {user_id}".format(post_id=post['id'],user_id=post['user']))
            return    
        print_error('{errors} Error(s) encountered downloading post id: {post_id} user id: {user_id}'.format(errors=error_flag,post_id=post['id'],user_id=post['user']))
        return
    print("Already archived post id: {post_id} user id: {user_id}".format(post_id=post['id'],user_id=post['user']))
    return    
    
def get_posts(service, user_id, post_id, username):
    chunk = 0
    next_chunk = True
    while next_chunk:
        api_link = 'https://kemono.party/api/{service}/user/{user_id}/post/{post_id}'.format(service=service,user_id=user_id,post_id=post_id) # /api/<service>/user/<id>/post/<id>
        if post_id == None:
            api_link = 'https://kemono.party/api/{service}/user/{user_id}?o={chunk}'.format(service=service,user_id=user_id,chunk=chunk) # /api/<service>/user/<id>
        api_responce = requests.get(api_link)  
        data = json.loads(api_responce.text)
        if not data:
            break
        for post in data:
            extract_post(post, username) 
        if not post_id == None:
            break
        chunk += 25
            
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

def get_pfp_banner(service, user_id, username):
    try:
        list = ['icon', 'banner']
        if service == 'gumroad': # gumroad does not have banners and when calling /baners/ you just get the icon again
            list = ['icon']
        if service == 'dlsite': # dlsite icons seem to be broken or their are none
            list = []
        # can not use normal downloader (no header info)
        folder_path = download_location + os.path.sep + service + os.path.sep + username + ' [{user_id}]'.format(user_id=user_id)
        for type in list:
            print('Downloading: {}'.format(type))
            api_call = 'https://kemono.party/{type}s/{service}/{user_id}'.format(type=type,service=service,user_id=user_id) # /icons/{service}/{creator_id} # /banners/{service}/{creator_id}     
            api_responce = requests.get(api_call,allow_redirects=True,cookies=cookie_jar) # this is kind of a bad way but also the only way I can think of doing it. Luckily the images are so small holding them in memory shouldn't be a problem     
            image = Image.open(io.BytesIO(api_responce.content)) # need to use PIL on content to get format, file has no extention
            file_path = "{directory}{username} [{user_id}] {type}.{ext}".format(directory=folder_path + os.path.sep,username=username,user_id=user_id,type=type,ext=image.format.lower())
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            image.save(file_path,format=image.format)
        return
    except Exception as e:
        print_error('Error downloading: {link}'.format(link=api_call))
        print(e)
        if not args['ignore_errors']:
            quit()    

def get_discord():
    print('Discord is not currently supported by this downloader. (in progress)')
    # /discord/server/{serverId}
    # serverId is same as creator id for getting username
    # how to get channel id(s) from server id with api?
    # api_channel = 'https://kemono.party/api/discord/channel/{channelId}?skip={skip}'
    # skip starts at 0 increments by 10
    pass

def extract_link(link):
    found = re.search('https://kemono\.party/([^/]+)/(server|user)/([^/]+)($|/post/([^/]+)$)',link)
    if found:
        service = found.group(1)
        user_id = found.group(3)
        post_id = found.group(5)
        username = get_username(service, user_id)
        if service == 'discord':
            get_discord(service, user_id, post_id, username)
            return True
        if not simulation_flag:
            get_pfp_banner(service, user_id, username)
        get_posts(service, user_id, post_id, username)
        return True
    return False    

def main():
    if args['links']:
        links = args['links'].split(",")
        for link in links:
            if not extract_link(link.lstrip()):
                print_error('Error invalid link: {link}'.format(link=link))
    
    if args['fromfile']:
        if not os.path.exists(args['fromfile']):
            print_error('Error no file found: {file}'.format(file=args['fromfile'])), quit()
            
        with open(args['fromfile'],'r') as f:
            links = f.readlines()
        if not links:
            print_error('Error {file} is empty.'.format(file=args['fromfile'])), quit()       
        
        for link in links:
            if not extract_link(link.strip()):
                print_error('Error invalid link: {link}'.format(link=link.strip()))
            
if __name__ == '__main__':
    main()
    print('Done!')
