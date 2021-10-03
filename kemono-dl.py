import requests
from bs4 import BeautifulSoup
import os
import re
from http.cookiejar import MozillaCookieJar
import argparse
import sys
import time

version = '2021.10.03'

ap = argparse.ArgumentParser()
ap.add_argument("--Version", action='store_true', help="prints version")
ap.add_argument("-o", "--output", help="path to download posts")
ap.add_argument("--cookies", required=True, help="path to cookies.txt")
# ap.add_argument("-s","--simulate", action='store_true', help="lists post links that would be downloaded.")
ap.add_argument("-a","--archive", action='store_true', help="Saves downloaded posts to an archive file")
args = vars(ap.parse_args())

if args['Version']:
    print(version), quit()

if args['cookies']:
    if not os.path.exists(args['cookies']):
        print('Invalid Cookie Location: {}'.format(args['cookies'])), quit()
    cookie_jar = MozillaCookieJar(args['cookies'])
    cookie_jar.load()

download_location = os.getcwd() + os.path.sep + 'Downloads' # default download location 
if args['output']:
    if not os.path.exists(args['output']):
        print('Invalid Download Location: {}'.format(args['output'])), quit()
    download_location = args['output'] 

# simulate_flag = args['simulate']  

archive_flag = False
if args['archive']:
    archive_flag = args['archive']
    # create archive file if none
    if not os.path.exists('archive.txt'): 
        with open('archive.txt','w') as f: pass

def download_file(download_url, folder_path):
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        # checking content type    
        content_type = requests.head(download_url,allow_redirects=True, cookies=cookie_jar).headers['Content-Type'].lower()
        if content_type == 'text' or content_type == 'html':
            print('Error Downloading: {}'.format(download_url))
            return False
        temp_file_name = download_url.split('/')[-1] # get file name from url. might want to find a better method
        file_name = re.sub('[\\/:\"*?<>|]+','',temp_file_name) # remove illegal windows characters
        # duplication checking
        if os.path.exists(folder_path + os.path.sep + file_name):
            server_file_length = requests.head(download_url,allow_redirects=True, cookies=cookie_jar).headers['Content-Length']
            local_file_size = os.path.getsize(folder_path + os.path.sep + file_name)
            if int(server_file_length) == int(local_file_size):
                print('Already Downloaded: {}'.format(file_name))
                return True
        print('Downloading: {}'.format(file_name))
        # downloading the file     
        with requests.get(download_url, stream=True, cookies=cookie_jar) as r:
            r.raise_for_status()
            downloaded = 0
            total = int(r.headers.get('content-length'))
            with open(folder_path + os.path.sep + file_name, 'wb') as f:
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
        print('Error Downloading: {}'.format(download_url))
        print(e)
        return False

def download_post(link, username, service):
    
    archived = []
    if archive_flag:
        with open('archive.txt','r') as f:
            archived = f.read().splitlines()
                    
    if not link in archived:
        error_flag = 0
        page_html = requests.get(link, allow_redirects=True, cookies=cookie_jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        title = page_soup.find("h1", {"class": "post__title"}).text.strip() # get post title            
        time_stamp = page_soup.find("time", {"class": "timestamp"})["datetime"] # get post timestamp
        offset = len(service)+3 # remove service name at end of title
        if time_stamp == '':
            post_folder_name = title[:-offset]
        else:
            post_folder_name = '[' + time_stamp + '] ' + title[:-offset]  
        # remove illegal windows characters
        # remove possible newlines or tabs in post title      
        # remove trailing '.' and whitespaces because windows will remove them from folder names             
        post_folder_name = re.sub('[\\n\\t]+',' ', re.sub('[\\/:\"*?<>|]+','',post_folder_name)).strip('.').strip()  
        folder_path = download_location + os.path.sep + service + os.path.sep + username + os.path.sep + post_folder_name # post folder path
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # saving content
        content_path = folder_path + os.path.sep + 'Content'
        content_html = page_soup.find("div", {"class": "post__content"})
        if not content_html == None:
            if not os.path.exists(content_path):
                os.makedirs(content_path)
            # downloading inline images
            inline_images = content_html.find_all('img')
            if not inline_images == []:
                for inline_image in inline_images:
                    kemono_hosted = re.search('^/[^*]+', inline_image['src'])
                    if kemono_hosted:
                        download_url = "https://kemono.party" + inline_image['src']
                        if download_file(download_url, content_path + os.path.sep + 'inline'):
                            inline_image['src'] = inline_image['src'][1:]
                        else:
                            error_flag += 1
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
            not_supported = re.search('[^ ]+ does not support comment scraping yet\.',comment_html.text)
            if not not_supported:
                if not os.path.exists(content_path):
                    os.makedirs(content_path)
                with open(content_path + os.path.sep + 'Comments.html','wb') as File:
                    File.write(comment_html.prettify().encode("utf-16")) 
        # download downloads                                  
        downloads = page_soup.find_all("a", {"class": "post__attachment-link"}) 
        if not downloads == []:
            for download in downloads:
                kemono_hosted = re.search('^/[^*]+', download['href'])
                if kemono_hosted:
                    if not download_file("https://kemono.party" + download['href'], folder_path + os.path.sep + 'Downloads'):
                        error_flag += 1
        # download files
        files = page_soup.find("div", {"class": "post__files"})
        if not files == None:
            files_path = folder_path + os.path.sep + 'Files'
            # download images in files                            
            image_files = files.find_all("a", {"class": "fileThumb"})
            if not image_files == []:
                for image_file in image_files:
                    kemono_hosted = re.search('^/[^*]+', image_file['href'])
                    if kemono_hosted:
                        if not download_file("https://kemono.party" + image_file['href'], files_path):
                            error_flag += 1
            # save external links in files
            file_external_links = files.find_all("a", {"target": "_blank"})
            if not file_external_links == []:
                if not os.path.exists(files_path):
                    os.makedirs(files_path)
                with open(files_path + os.path.sep + 'File_External_Links.txt', 'w') as File:
                    for file_external_link in file_external_links:
                        File.write(file_external_link['href'] + '\n')
        if error_flag == 0:
            if archive_flag:
                with open('archive.txt','a') as f:
                    f.write(link + '\n')
            print("Post completed downloading: {}".format(link))
            return
        print('{} Error(s) encountered downloading post: {}'.format(error_flag, link))
        return
    else:
        print("Post already archived : {}".format(link))
        return

def get_username(link):
        page_html = requests.get(link, allow_redirects=True, cookies=cookie_jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        return page_soup.find("span", {"itemprop": "name"}).text.strip() 
    
def get_posts(page):
        post_links = []
        page_html = requests.get(page, allow_redirects=True, cookies=cookie_jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        posts = page_soup.find_all("article")
        for post in posts:
            post_links.append("https://kemono.party" + post.find('a')["href"])       
        next_page = 'none' 
        next_page_element = page_soup.find("a", {"title": "Next page"})
        if not next_page_element == None:
            next_page = "https://kemono.party" + next_page_element["href"]
        return (next_page, post_links)

def main():
    
    if not os.path.exists('Users.txt'):
        print('No "Users.txt" file found.'), quit()
        
    with open('Users.txt','r') as f:
        links = f.read().splitlines() 
            
    if len(links) == 0:
        print('"Users.txt" is empty.'), quit()
        
    for link in links:
        
        user_post = re.search('(https://kemono\.party/([^/]+)/user/[^/]+)/post/[^/]+', link)
        if user_post:
            post_link = link
            service = user_post.group(2)
            if service == 'fanbox': service = 'pixiv fanbox'
            username = get_username(user_post.group(1))
            download_post(post_link, username, service)
                        
        user_profile = re.search('https://kemono\.party/([^/]+)/user/[^/]+$', link)        
        if user_profile:
            profile_link = link
            post_links = []
            service = user_profile.group(1)
            if service == 'fanbox': service = 'pixiv fanbox'            
            username = get_username(profile_link)
            while not profile_link == 'none':
                profile_link, post_links_temp = get_posts(profile_link)
                post_links += post_links_temp
            for post_link in post_links:
                download_post(post_link, username, service)
                            
        if not user_post and not user_profile:
            print('Invalid link: {}'.format(link))
            
if __name__ == '__main__':
    main()
    print('Done!')
