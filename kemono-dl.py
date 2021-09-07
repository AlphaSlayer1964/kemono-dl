import requests
from bs4 import BeautifulSoup
import os
import re

Downalod_Loaction = 'CHANGE THIS!!!!!!!!!!!!!'

if Downalod_Loaction == 'CHANGE THIS!!!!!!!!!!!!!':
    print("open this file with a text editor and add your file location at the top and the cookie values!")
    quit()

jar = requests.cookies.RequestsCookieJar()
jar.set('__ddgid', 'CHANGE THIS!!!!!!!!!!!!!', domain='.kemono.party', path='/')
jar.set('__ddg2', 'CHANGE THIS!!!!!!!!!!!!!', domain='.kemono.party', path='/')
jar.set('__ddg1', 'CHANGE THIS!!!!!!!!!!!!!', domain='.kemono.party', path='/')
jar.set('__ddgmark', 'CHANGE THIS!!!!!!!!!!!!!', domain='.kemono.party', path='/')

def Download_Post(link, username):
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
        content_text = page_soup.find("div", {"class": "post__content"}).get_text("\n", strip=True)
        text_file_name = folder_location + os.path.sep + 'Content.txt'
        html_file_name = folder_location + os.path.sep + 'Content.html'
        if not os.path.exists(html_file_name):
            with open(html_file_name,'w') as File:
                File.write(content_html)
        if not os.path.exists(text_file_name):
            with open(text_file_name,'w') as File:
                File.write(content_text)                            
    except:
        pass
    try:
        downloads = page_soup.find_all("a", {"class": "post__attachment-link"})
        for download in downloads:
            download_url = "https://kemono.party" + download['href']
            temp_filename = download_url.split('/')[-1]
            local_filename = re.sub('[\\/:\"*?<>|]+','',temp_filename)
            if not os.path.exists(folder_location + os.path.sep + local_filename):
                print("Downloading " + local_filename)
                with requests.get(download_url, stream=True, cookies=jar) as r:
                    r.raise_for_status()
                    with open(folder_location + os.path.sep + local_filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192): 
                            f.write(chunk)            
    except:
        pass
    try:
        files = page_soup.find_all("a", {"class": "fileThumb"})
        for file in files:
            file_url = "https://kemono.party" + file['href']
            temp_filename = download_url.split('/')[-1]
            local_filename = re.sub('[\\/:\"*?<>|]+','',temp_filename)
            if not os.path.exists(folder_location + os.path.sep + local_filename):
                print("Downloading " + local_filename)
                with requests.get(file_url, stream=True, cookies=jar) as r:
                    r.raise_for_status()
                    with open(folder_location + os.path.sep + local_filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192): 
                            f.write(chunk)             
    except:
        pass    


with open('Users.txt','r') as File:
    users = File.readlines()

post_links = []
username = ''
for user in users:
    result = re.match('https://kemono\.party/patreon/user/[^/]+', user.strip())
    if result:    
        page_html = requests.get(user.strip(), allow_redirects=True, cookies=jar)
        page_soup = BeautifulSoup(page_html.text, 'html.parser')
        if username == '':
            username = page_soup.find("span", {"itemprop": "name"}).text
        posts = page_soup.find_all("article")
        for post in posts:
            post_links.append("https://kemono.party/" + post.find('a')["href"])
        try:
            next_page = "https://kemono.party/" + page_soup.find("a", {"title": "Next page"})["href"]
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
                next_page = "https://kemono.party/" + page_soup.find("a", {"title": "Next page"})["href"]
            except:
                next_page = 'none'
                pass
        for post in post_links:
            Download_Post(post, username)