import requests
from bs4 import BeautifulSoup
import os
import re

Downalod_Loaction = 'CHANGE THIS!!!!!!!!!!!!!'

if Downalod_Loaction == 'CHANGE THIS!!!!!!!!!!!!!':
    print("open this file with a text editor and add your file location at the top and edit the cookie values!")
    quit()

jar = requests.cookies.RequestsCookieJar()
jar.set('__ddgid', 'CHANGE THIS!!!!!!!!!!!!!', domain='.kemono.party', path='/')
jar.set('__ddg2', 'CHANGE THIS!!!!!!!!!!!!!', domain='.kemono.party', path='/')
jar.set('__ddg1', 'CHANGE THIS!!!!!!!!!!!!!', domain='.kemono.party', path='/')
jar.set('__ddgmark', 'CHANGE THIS!!!!!!!!!!!!!', domain='.kemono.party', path='/')

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
# removes new lines at end of each string in archive_temp
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

def Download_Post(link, username):
    if link not in archives:
        page_html = requests.get(link, allow_redirects=True, cookies=jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        title = page_soup.find("h1", {"class": "post__title"}).text.strip()
        time_stamp = page_soup.find("time", {"class": "timestamp"})["datetime"]
        temp_name = '[' + time_stamp + '] ' + title[:-10]
        folder_name = re.sub('[\\/:\"*?<>|]+','',temp_name)
        folder_location = Downalod_Loaction + os.path.sep + username + os.path.sep + folder_name
        if not os.path.exists(folder_location):
            os.makedirs(folder_location)
        try:
            content_html = page_soup.find("div", {"class": "post__content"}).prettify()
            html_file_name = folder_location + os.path.sep + 'Content.html'
            with open(html_file_name,'w') as File:
                File.write(content_html)                           
        except:
            pass
        try:
            comment_html = page_soup.find("div", {"class": "post__comments"}).prettify()
            comment_file_name = folder_location + os.path.sep + 'Comments.html'
            with open(comment_file_name,'wb') as File:
                File.write(comment_html.encode("utf-8"))                           
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
    post_links = []
    kemono_user_profile = re.match('https://kemono\.party/patreon/user/[^/]+', user.strip())
    kemono_user_post = re.search('(https://kemono\.party/patreon/user/[^/]+)/post/[^/]+', user.strip())
    if kemono_user_post:
        page_html = requests.get(kemono_user_post.group(1), allow_redirects=True, cookies=jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        if username == '':
            username = page_soup.find("span", {"itemprop": "name"}).text        
        Download_Post(user.strip(), username)           
        skip = 1    
    if kemono_user_profile and skip == 0:    
        page_html = requests.get(user.strip(), allow_redirects=True, cookies=jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        if username == '':
            username = page_soup.find("span", {"itemprop": "name"}).text
        posts = page_soup.find_all("article")
        for post in posts:
            post_links.append("https://kemono.party" + post.find('a')["href"])
        # Looking for next page 
        try:
            next_page = "https://kemono.party" + page_soup.find("a", {"title": "Next page"})["href"]
        except:
            next_page = 'none'
            pass
        # Loop till there are no new pages
        while not next_page == 'none':
            page_html = requests.get(next_page, allow_redirects=True, cookies=jar)
            page_soup = BeautifulSoup(page_html.text, 'html.parser')
            posts = page_soup.find_all("article")
            for post in posts:
                post_links.append("https://kemono.party" + post.find('a')["href"])
            # Looking for next page        
            try:
                next_page = "https://kemono.party" + page_soup.find("a", {"title": "Next page"})["href"]
            except:
                next_page = 'none'
                pass
        for post in post_links:
            Download_Post(post, username)
