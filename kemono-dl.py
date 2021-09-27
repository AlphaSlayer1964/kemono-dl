import requests
from bs4 import BeautifulSoup
import os
import re
from http.cookiejar import MozillaCookieJar
import argparse
import sys
import time

version = '2021.09.27.2'

def Download_File(download_url, folder_path, cookie_jar):
    """
    Args:
        download_url (str):             Url of file to download.
        folder_path (str):              Location file should be downloaded to.
        cookie_jar (MozillaCookieJar):  A cookie jar to get past ddos protection.

    Returns:
        (Boolean): True if download was successful returns False if not
    """
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

def Download_Post(link, username, service, download_location, cookie_jar):
    """
    Args:
        link (str):                     Link to the post that should be downloaded.
        username (str):                 Username of the poster.
        service (str):                  Service type of the post.
        download_location (str):        Base location where files are downloaded to.
        cookie_jar (MozillaCookieJar):  A cookie jar to get past ddos protection.
    """
    error_flag = 0
    
    with open('archive.txt','r') as File:
        archives_temp = File.readlines()
    archives = []
    for element in archives_temp:
        archives.append(element.strip())    
    
    if link not in archives:
        page_html = requests.get(link, allow_redirects=True, cookies=cookie_jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        title = page_soup.find("h1", {"class": "post__title"}).text.strip() # get post title            
        time_stamp = page_soup.find("time", {"class": "timestamp"})["datetime"] # get post timestamp
        offset = len(service)+3 # remove service name at end of title
        if time_stamp == '':
            folder_name_temp = title[:-offset]
        else:
            folder_name_temp = '[' + time_stamp + '] ' + title[:-offset]   
        folder_name_temp = re.sub('[\\/:\"*?<>|]+','',folder_name_temp) # remove illegal windows characters
        folder_name_temp = re.sub('[\\n\\t]+',' ',folder_name_temp) # remove possible newlines or tabs in post title      
        folder_name = folder_name_temp.strip('.').strip() # remove trailing '.' and whitespaces because windows will remove them from folder names        
        folder_path = download_location + os.path.sep + service + os.path.sep + username + os.path.sep + folder_name # post folder path
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
                        if Download_File(download_url, content_path + os.path.sep + 'inline', cookie_jar):
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
            downloads = page_soup.find_all("a", {"class": "post__attachment-link"})
            for download in downloads:
                direct_link = re.search('https:\/\/kemono\.party',download['href'])
                download_url = "https://kemono.party" + download['href']
                if direct_link:
                    download_url = download['href']
                if not Download_File(download_url, downloads_path, cookie_jar):
                    error_flag += 1
        # download files
        files = page_soup.find("div", {"class": "post__files"})
        if not files == None:
            if not os.path.exists(files_path):
                os.makedirs(files_path)
            # download images in files                            
            image_files = files.find_all("a", {"class": "fileThumb"})
            if not image_files == []:
                for file in image_files:
                    direct_link = re.search('https:\/\/kemono\.party',file['href'])
                    download_url = "https://kemono.party" + file['href']
                    if direct_link:
                        download_url = file['href']
                    if not Download_File(download_url, files_path, cookie_jar):
                        error_flag += 1
            # save external links in files
            file_external_links = files.find_all("a", {"target": "_blank"})
            if not file_external_links == []:
                with open(files_path + os.path.sep + 'File_External_Links.txt', 'w') as File:
                    for file_external_link in file_external_links:
                        File.write(file_external_link['href'] + '\n')
        
        if error_flag == 0:        
            with open('archive.txt','a') as File: # archive post link
                File.write(link + '\n')
            print("Completed Downloading Post: " + link)
            return
        print('{} Error(s) occurred while downloading post: {}\nPost will not be saved to archive.txt'.format(error_flag, link))
    else:
        print("Post Already Archived : " + link)
        return

def main():
    
    ap = argparse.ArgumentParser()
    ap.add_argument("--Version", action='store_true', help="prints version")
    ap.add_argument("-o", "--output", help="path to download posts")
    ap.add_argument("--cookies", required=True, help="path to cookies.txt")
    args = vars(ap.parse_args())

    if args['Version']:
        print(version)
        quit()

    if args['cookies']:
        cookie_location = args['cookies']
        if not os.path.exists(cookie_location):
            print('Invalid Cookie Location: {}'.format(cookie_location))
            quit()
        cookie_jar = MozillaCookieJar(cookie_location)
        cookie_jar.load()

    download_location = os.getcwd() + os.path.sep + 'Downloads' # default download location 
    if args['output']:
        download_location = args['output']
        if not os.path.exists(download_location):
            print('Invalid Download Location: {}'.format(download_location))
            quit()    

    # create archive file if none
    if not os.path.exists('archive.txt'):
        file = open('archive.txt','w')
        file.close()

    if not os.path.exists('Users.txt'):
        print('No "Users.txt" file found.')
        quit()

    with open('Users.txt','r') as File:
        user_links = File.readlines()
        
    if len(user_links) == 0:
        print('"Users.txt" is empty.')
        quit()
        
    for user_link in user_links:
        user_link = user_link.strip()

        user_post = re.search('(https://kemono\.party/([^/]+)/user/[^/]+)/post/[^/]+', user_link)
        if user_post:
            service = user_post.group(2)
            if service == 'fanbox':
                service = 'pixiv fanbox'
            page_html = requests.get(user_post.group(1), allow_redirects=True, cookies=cookie_jar)
            page_soup = BeautifulSoup(page_html.text, 'html.parser')
            username = page_soup.find("span", {"itemprop": "name"}).text.strip()        
            Download_Post(user_link, username, service, download_location, cookie_jar)
                    
        user_profile = re.search('https://kemono\.party/([^/]+)/user/[^/]+$', user_link)        
        if user_profile:
            post_links = []
            service = user_profile.group(1)
            if service == 'fanbox':
                service = 'pixiv fanbox'            
            page_html = requests.get(user_link, allow_redirects=True, cookies=cookie_jar)
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
                page_html = requests.get(next_page, allow_redirects=True, cookies=cookie_jar)
                page_soup = BeautifulSoup(page_html.text, 'html.parser')
                posts = page_soup.find_all("article")
                for post in posts:
                    post_links.append("https://kemono.party" + post.find('a')["href"])       
                next_page = 'none' 
                next_page_element = page_soup.find("a", {"title": "Next page"})
                if not next_page_element == None:
                    next_page = "https://kemono.party" + next_page_element["href"]
            for post in post_links:
                Download_Post(post, username, service, download_location, cookie_jar)
                
        if not user_post and not user_profile:
            print('Invalid user or post link: {}'.format(user_link))
            
if __name__ == '__main__':
    main()
    print('Done!')
