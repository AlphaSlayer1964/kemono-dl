# kemono-dl
This is a simple kemono.party downloader using python.
I have decided to switch to using kemono.party's API instead of tones of http requests.
The downsides are no comments.

## How to use:
1. Install python
2. Install BeautifulSoup with ```pip insatll bs4```
3. Download ```kemono-dl.py``` from [releases](https://github.com/AplhaSlayer1964/Kemono.party-Downloader/releases)
4. Get a cookie.txt file from kemono.party 
   - You can get the cookie text file using a [chrome](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid?hl=en) or [firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) extension
   - You must pass a cookie file or kemono.party's ddos protection won't let the script access the site 
5. Run ```python kemono-dl.py --cookies "cookie.txt" --user https://kemono.party/SERVICE/user/USERID```


## Options:
- ```-h, --help``` Prints help text then exits
- ```--version``` Displays the current version then exits
-  ```--cookies FILE``` Set path to cookie.txt (**REQUIRED TO DOWNLOAD FILES**)
- ```-u, --user LINK``` Download user posts (only one user)
- ```-p, --post LINK``` Download post (only one post)
- ```-f, --fromfile FILE``` Download users and posts from a file seperated by a newline
- ```-o, --output FOLDER``` Set path to download posts
- ```-a, --archive FILE``` Downloads only posts that are not in archive.txt 
- ```-i, --ignore-errors``` Continue to download post(s) when an error occurs
- ```-s, --simulate``` Print post(s) info and does not download
- ```--date YYYYMMDD``` Only download posts from this date
- ```--datebefore YYYYMMDD``` Only download posts from this date and before
- ```--dateafter YYYYMMDD``` Only download posts from this date and after

## Examples:
- ```python kemono-dl.py --cookies "cookie.txt" -o "C:\Users\User\Downloads" --archive archive.txt --fromfile Users.txt```
- ```python kemono-dl.py --cookies "cookie.txt" --date 20210101 --user https://kemono.party/SERVICE/user/USERID```
- ```python kemono-dl.py --cookies "cookie.txt" -i -p https://kemono.party/SERVICE/user/USERID/post/POSTID```

## Notes:
- If ```--cookie cookie.txt``` is not passed script will run as if ```--simulation``` was passed
- Default download location is a ```Downloads``` folder in the current working directory (will be created automatically)
- Input link format: ```https://kemono.party/{service}/user/{user_id}``` or ```https://kemono.party/{service}/user/{user_id}/post/{post_is}```
- External links will be placed in external_links.txt
- Using any date option will not downlaod any gumroad posts because they have no dates
- For right now if you want multiple users and posts at once you must use ```-f, --fromfile```
- using ```--ignore-erros``` posts with errors will not be archived

## Default File Output Format:
```
CWD
├── kemono-dl.py
└── Downloads
    └── {service}
        └── {username} [{user_id}]
            └── [{date}] [{post_id}] {post_title}
                ├── attachments
                │   └── attachment.ext
                ├── content.html
                ├── external_links.txt
                └── file.ext
```

## To do:
- [ ] Integrate youtube-dl for downloading external video links
- [ ] Allow file naming structure to be changed in command line
- [ ] Allow file path structure to be changed in command line
- [ ] Add Discord service
- [ ] Have ```-u, --user LINK``` take as many users seperated by ```,```
- [ ] Have ```-p, --post LINK``` take as many posts seperated by ```,```

## Keep in mind:
- Using this might get you IP banned from kemono party.
  - This is highly unlikely now that I switched to using their API!
- If the site changes the script might break.
   - This is also now highly unlikely now that I switched to using their API!
