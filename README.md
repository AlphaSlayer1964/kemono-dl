# kemono-dl
This is a simple kemono.party downloader using python and kemono.party's API.

## How to use:
1. Install python
2. Install BeautifulSoup with ```pip insatll bs4```
3. Download source code from [releases](https://github.com/AplhaSlayer1964/Kemono.party-Downloader/releases) and extract it
4. Then install requirements with  ```pip install -r requirements.txt```
5. Get a cookie.txt file from kemono.party 
   - You can get the cookie text file using a [chrome](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid?hl=en) or [firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) extension
   - A cookie.txt file is needed to download files 
6. Run ```python kemono-dl.py --cookies "cookie.txt" --links https://kemono.party/SERVICE/user/USERID```


## Options:
- ```-h, --help``` Prints help text then exits
- ```--version``` Displays the current version then exits
-  ```--cookies FILE``` Set path to cookie.txt (**REQUIRED TO DOWNLOAD FILES**)
- ```-l, --links LINK(s)``` Downloads user or post links seperated by a comma (,)
- ```-f, --fromfile FILE``` Download users and posts from a file seperated by a newline
- ```-o, --output FOLDER``` Set path to download posts
- ```-a, --archive FILE``` Downloads only posts that are not in provided archive file 
- ```-i, --ignore-errors``` Continue to download post(s) when an error occurs
- ```-s, --simulate``` Print post(s) info and does not download
- ```--date YYYYMMDD``` Only download posts from this date
- ```--datebefore YYYYMMDD``` Only download posts from this date and before
- ```--dateafter YYYYMMDD``` Only download posts from this date and after
- ```--force-inline``` Force download all external inline images found in post content

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
            ├── {username} [{user_id}] icon.ext
            ├── {username} [{user_id}] banner.ext
            └── [{date}] [{post_id}] {post_title}
                ├── attachments
                │   └── attachment.ext
                ├── inline
                │   └── image.ext
                ├── content.html
                ├── external_links.txt
                └── file.ext
```

## Examples:
- ```python kemono-dl.py --cookies "cookie.txt" -o "C:\Users\User\Downloads" --archive archive.txt --fromfile Users.txt```
- ```python kemono-dl.py --cookies "cookie.txt" --date 20210101 --links https://kemono.party/SERVICE/user/USERID```
- ```python kemono-dl.py --cookies "cookie.txt" -i -l https://kemono.party/SERVICE/user/USERID/post/POSTID,https://kemono.party/SERVICE/user/USERID```

## To do:
- [ ] Integrate youtube-dl for downloading external video links
- [ ] Allow file naming structure to be changed in command line
- [ ] Allow file path structure to be changed in command line
- [ ] Add Discord service (in progress)
- [ ] Download comments using API (if possible, might not be)

## Keep in mind:
- Using this might get you IP banned from kemono party.
  - This is highly unlikely now that I switched to using their API!
- If the site changes the script might break.
   - This is also now highly unlikely now that I switched to using their API!
