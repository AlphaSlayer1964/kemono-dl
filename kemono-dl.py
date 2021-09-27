import requests
from bs4 import BeautifulSoup
import os
import re
from http.cookiejar import MozillaCookieJar
import argparse
import sys
import time

version = '2021.09.27'

ap = argparse.ArgumentParser()
ap.add_argument("--Version", action='store_true', help="prints version")
ap.add_argument("-o", "--output", help="path to download posts")
ap.add_argument("--cookies", required=True, help="path to cookies.txt")
# ap.add_argument("-i", "--ignore-errors", action='store_true', help="Continue on download posts and ignore errors")
args = vars(ap.parse_args())

if args['Version']:
    print(version)
    quit()

if args['cookies']:
    cookie_location = args['cookies']
    if not os.path.exists(cookie_location):
        print('Invalid Cookie Location:' + cookie_location)
        quit()
    jar = MozillaCookieJar(cookie_location)
    jar.load()
    
Download_Location = os.getcwd() + os.path.sep + 'Downloads'
if args['output']:
    DL = args['output']
    if not os.path.exists(DL):
        print('Invalid Download Location:' + DL)
        quit()
    Download_Location = DL
  
# re work this in the future 
def Download_Status(dl_status):
    if dl_status[0] == 0: # download completed
        return True
    elif dl_status[0] == 1: # file already downloaded
        print('Already Downloaded: ' + dl_status[1])
        return True
    elif dl_status[0] == 2: # wrong content type
        print('File type incorrect: ' + dl_status[1])
        return False
    # other error
    print('Error occurred downloading from: ' + dl_status[1])
    return False    
    
def Download_File(download_url, folder_path):
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        # checking content type    
        content_type = requests.head(download_url,allow_redirects=True, cookies=jar).headers['Content-Type'].lower()
        if content_type == 'text' or content_type == 'html':
            return (2,download_url)
        temp_file_name = download_url.split('/')[-1] # get file name from url. might want to find a better method
        file_name = re.sub('[\\/:\"*?<>|]+','',temp_file_name) # remove illegal windows characters
        # duplication checking
        if os.path.exists(folder_path + os.path.sep + file_name):
            server_file_length = requests.head(download_url,allow_redirects=True, cookies=jar).headers['Content-Length']
            local_file_size = os.path.getsize(folder_path + os.path.sep + file_name)
            if int(server_file_length) == int(local_file_size):
                return (1,file_name)
        # downloading the file
        print("Downloading: " + file_name)     
        with requests.get(download_url, stream=True, cookies=jar) as r:
            r.raise_for_status()
            downloaded = 0
            total = int(r.headers.get('content-length'))
            with open(folder_path + os.path.sep + file_name, 'wb') as f:
                start = time.time()
                for chunk in r.iter_content(chunk_size=max(int(total/1000), 1024*1024)): 
                    downloaded += len(chunk)
                    f.write(chunk)
                    done = int(50*downloaded/total)
                    sys.stdout.write('\r[{}{}] {}/{} MB , {} Mbps'.format('=' * done, ' ' * (50-done), downloaded//1000000, total//1000000, round(downloaded//(time.time() - start) / 100000,1)))
                    sys.stdout.flush() 
            sys.stdout.write('\n')
        return (0,file_name)
    except Exception as e:
        print(e)
        return (3,download_url)

def Download_Post(link, username, service):
    
    with open('archive.txt','r') as File:
        archives_temp = File.readlines()
    archives = []
    for element in archives_temp:
        archives.append(element.strip())    
    
    if link not in archives:
        page_html = requests.get(link, allow_redirects=True, cookies=jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        title = page_soup.find("h1", {"class": "post__title"}).text.strip() # get post title            
        time_stamp = page_soup.find("time", {"class": "timestamp"})["datetime"] # get post timestamp
        offset = len(service)+3 # remove service name at end of title
        if time_stamp == None:
            folder_name_temp = title[:-offset]
        else:
            folder_name_temp = '[' + time_stamp + '] ' + title[:-offset]   
        folder_name_temp = re.sub('[\\/:\"*?<>|]+','',folder_name_temp) # remove illegal windows characters
        folder_name_temp = re.sub('[\\n\\t]+',' ',folder_name_temp) # remove possible newlines or tabs in post title      
        folder_name = folder_name_temp.strip('.').strip() # remove trailing '.' because windows will remove them from folder names        
        folder_path = Download_Location + os.path.sep + service + os.path.sep + username + os.path.sep + folder_name # post folder path
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        content_path = folder_path + os.path.sep + 'Content'
        files_path = folder_path + os.path.sep + 'Files'
        downloads_path = folder_path + os.path.sep + 'Downloads'
        # saving content
        content_html = page_soup.find("div", {"class": "post__content"})
        if not content_html == None:
            if not os.path.exists(content_path):
                os.makedirs(content_path)
            # downloading inline images
            inline_images = content_html.find_all('img')
            if not inline_images == []:
                for inline_image in inline_images:
                    found = re.search('/inline/[^*]+', inline_image['src'])
                    if found:
                        download_url = "https://kemono.party" + inline_image['src']
                        if Download_Status(Download_File(download_url, content_path + os.path.sep + 'inline')):
                            inline_image['src'] = inline_image['src'][1:]
            # save external links found in content    
            content_external_links = content_html.find_all('a', href=True)
            if not content_external_links == []:
                with open(content_path + os.path.sep + 'Content_External_Links.txt', 'w') as File:
                    for content_external_link in content_external_links:
                        File.write(content_external_link['href'] + '\n')
            # saving content to html file to keep formatting         
            html_file_path = content_path + os.path.sep + 'Content.html'
            with open(html_file_path,'wb') as File:
                File.write(content_html.prettify().encode("utf-16"))
        # save comments to html file to keep formatting (considered part of the content section)                                   
        comment_html = page_soup.find("div", {"class": "post__comments"})
        if not comment_html == None:
            if not os.path.exists(content_path):
                os.makedirs(content_path)
            with open(content_path + os.path.sep + 'Comments.html','wb') as File:
                File.write(comment_html.prettify().encode("utf-16")) 
        # download downloads                                  
        downloads = page_soup.find_all("a", {"class": "post__attachment-link"}) 
        if not downloads == []:
            downloads = page_soup.find_all("a", {"class": "post__attachment-link"})
            for download in downloads:
                download_url = "https://kemono.party" + download['href']
                Download_Status(Download_File(download_url, downloads_path))
        # download files 
        files = page_soup.find("div", {"class": "post__files"})
        if not files == None:
            if not os.path.exists(files_path):
                os.makedirs(files_path)
            # download images in files                            
            image_files = files.find_all("a", {"class": "fileThumb"})
            if not image_files == []:
                for file in image_files:
                    download_url = "https://kemono.party" + file['href']
                    Download_Status(Download_File(download_url, files_path))
            # save external links in files
            file_external_links = files.find_all("a", {"target": "_blank"})
            if not file_external_links == []:
                with open(files_path + os.path.sep + 'File_External_Links.txt', 'w') as File:
                    for file_external_link in file_external_links:
                        File.write(file_external_link['href'] + '\n')
                
        with open('archive.txt','a') as File: # archive post link
            File.write(link + '\n')
        print("Completed Downloading Post: " + link)
    else:
        print("Post Already Archived : " + link)

# create archive file if none
if not os.path.exists('archive.txt'):
    file = open('archive.txt','w')
    file.close()

if not os.path.exists('Users.txt'):
    print('No "Users.txt" file found.')
    quit()

with open('Users.txt','r') as File:
    users = File.readlines()
    
if len(users) == 0:
    print('"Users.txt" is empty.')
    quit()
    
for user in users:

    user_post = re.search('(https://kemono\.party/([^/]+)/user/[^/]+)/post/[^/]+', user.strip())
    if user_post:
        service = user_post.group(2)
        if service == 'fanbox':
            service = 'pixiv fanbox'
        page_html = requests.get(user_post.group(1), allow_redirects=True, cookies=jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        username = page_soup.find("span", {"itemprop": "name"}).text.strip()        
        Download_Post(user.strip(), username, service)
                   
    user_profile = re.search('https://kemono\.party/([^/]+)/user/[^/]+$', user.strip())        
    if user_profile:
        post_links = []
        service = user_profile.group(1)
        if service == 'fanbox':
            service = 'pixiv fanbox'            
        page_html = requests.get(user.strip(), allow_redirects=True, cookies=jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        username = page_soup.find("span", {"itemprop": "name"}).text.strip() 
        posts = page_soup.find_all("article")
        for post in posts:
            post_links.append("https://kemono.party" + post.find('a')["href"])
        next_page = 'none' 
        next_page_element = page_soup.find("a", {"title": "Next page"})
        if not next_page_element == None:
            next_page = "https://kemono.party" + next_page_element["href"]
            
        while not next_page == 'none':
            page_html = requests.get(next_page, allow_redirects=True, cookies=jar)
            page_soup = BeautifulSoup(page_html.text, 'html.parser')
            posts = page_soup.find_all("article")
            for post in posts:
                post_links.append("https://kemono.party" + post.find('a')["href"])       
            next_page = 'none' 
            next_page_element = page_soup.find("a", {"title": "Next page"})
            if not next_page_element == None:
                next_page = "https://kemono.party" + next_page_element["href"]
        for post in post_links:
            Download_Post(post, username, service)
