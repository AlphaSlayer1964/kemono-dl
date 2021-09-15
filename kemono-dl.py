import requests
from bs4 import BeautifulSoup
import os
import re
import sys

# Change the 0000000000000000 to your values
jar = requests.cookies.RequestsCookieJar()
jar.set('__ddgid', '0000000000000000', domain='.kemono.party', path='/')
jar.set('__ddg2', '0000000000000000', domain='.kemono.party', path='/')
jar.set('__ddg1', '0000000000000000', domain='.kemono.party', path='/')
jar.set('__ddgmark', '0000000000000000', domain='.kemono.party', path='/')

# change this value to a 1 when you change the cookie values above
I_changed_the_cookies = 0

if I_changed_the_cookies == 0:
    print("You did not change the cookies value the script will not work!")
    quit()

try:
    DL = sys.argv[1]
    if not os.path.exists(DL):
        print('Invalid Download Location:' + DL)
        quit()
    Download_Location = DL
except:
    Download_Location = os.getcwd()

if not os.path.exists('archive.txt'):
    file = open('archive.txt','w')
    file.close()

if not os.path.exists('Users.txt'):
    print('No "Users.txt" file found!')
    quit()

with open('Users.txt','r') as File:
    users = File.readlines()

with open('archive.txt','r') as File:
    archives_temp = File.readlines()

archives = []
for element in archives_temp:
    archives.append(element.strip())

def Download_File(download, folder_location):
    download_url = "https://kemono.party" + download['href']
    content_type = requests.head(download_url,allow_redirects=True, cookies=jar).headers['Content-Type'].lower()
    if content_type == 'text' or content_type == 'html':
        return 'File Not Downloadable'
    temp_filename = download_url.split('/')[-1]
    local_filename = re.sub('[\\/:\"*?<>|]+','',temp_filename)
    if os.path.exists(folder_location + os.path.sep + local_filename):
        server_file_length = requests.head(download_url,allow_redirects=True, cookies=jar).headers['Content-Length']
        local_file_size = os.path.getsize(folder_location + os.path.sep + local_filename)
        if int(server_file_length) == int(local_file_size):
            return 'File already Downloaded'
    print("Downloading: " + local_filename)
    with requests.get(download_url, stream=True, cookies=jar) as r:
        r.raise_for_status()
        with open(folder_location + os.path.sep + local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk) 
    return ("Downloaded: " + local_filename)    

def Download_Post(link, username, service):
    if link not in archives:
        page_html = requests.get(link, allow_redirects=True, cookies=jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        title = page_soup.find("h1", {"class": "post__title"}).text.strip()
        time_stamp = page_soup.find("time", {"class": "timestamp"})["datetime"]
        offset = len(service)+3
        temp_name = '[' + time_stamp + '] ' + title[:-offset]
        temp_name2 = re.sub('[\\/:\"*?<>|]+','',temp_name)
        temp_name3 = re.sub('\\n',' ',temp_name2)
        folder_name = re.sub('\\t',' ',temp_name3)
        folder_name = folder_name.strip('.').strip()
        folder_location = Download_Location + os.path.sep + service + os.path.sep + username + os.path.sep + folder_name
        if not os.path.exists(folder_location):
            os.makedirs(folder_location)
        try:
            content_html = page_soup.find("div", {"class": "post__content"}).prettify()
            html_file_name = folder_location + os.path.sep + 'Content.html'
            with open(html_file_name,'wb') as File:
                File.write(content_html.encode("utf-16"))                           
        except:
            pass
        try:
            comment_html = page_soup.find("div", {"class": "post__comments"}).prettify()
            comment_file_name = folder_location + os.path.sep + 'Comments.html'
            with open(comment_file_name,'wb') as File:
                File.write(comment_html.encode("utf-16"))                           
        except:
            pass          
        try:
            downloads = page_soup.find_all("a", {"class": "post__attachment-link"})
            for download in downloads:
                status = Download_File(download, folder_location)
                print(status)            
        except:
            pass
        try:
            files = page_soup.find_all("a", {"class": "fileThumb"})
            for file in files:
                status = Download_File(file, folder_location)
                print(status)
        except:
            pass
        with open('archive.txt','a') as File:
            File.write(link + '\n')
        print("Completed Downloading Post: " + link)
    else:
        print("Post Already Archived : " + link)

for user in users:
    skip = 0
    username = ''
    service = ''
    post_links = []
    kemono_user_profile = re.search('https://kemono\.party/([^/]+)/user/[^/]+', user.strip())
    kemono_user_post = re.search('(https://kemono\.party/([^/]+)/user/[^/]+)/post/[^/]+', user.strip())
    if kemono_user_post:
        service = kemono_user_post.group(2)
        if service == 'fanbox':
            service = 'pixiv fanbox'
        page_html = requests.get(kemono_user_post.group(1), allow_redirects=True, cookies=jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        if username == '':
            username = page_soup.find("span", {"itemprop": "name"}).text        
        Download_Post(user.strip(), username, service)           
        skip = 1    
    if kemono_user_profile and skip == 0:
        service = kemono_user_profile.group(1)
        if service == 'fanbox':
            service = 'pixiv fanbox'            
        page_html = requests.get(user.strip(), allow_redirects=True, cookies=jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        if username == '':
            username = page_soup.find("span", {"itemprop": "name"}).text
        posts = page_soup.find_all("article")
        for post in posts:
            post_links.append("https://kemono.party" + post.find('a')["href"]) 
        try:
            next_page = "https://kemono.party" + page_soup.find("a", {"title": "Next page"})["href"]
        except:
            next_page = 'none'
            pass
        while not next_page == 'none':
            page_html = requests.get(next_page, allow_redirects=True, cookies=jar)
            page_soup = BeautifulSoup(page_html.text, 'html.parser')
            posts = page_soup.find_all("article")
            for post in posts:
                post_links.append("https://kemono.party" + post.find('a')["href"])       
            try:
                next_page = "https://kemono.party" + page_soup.find("a", {"title": "Next page"})["href"]
            except:
                next_page = 'none'
                pass
        for post in post_links:
            Download_Post(post, username, service)
