# Kemono.party-Downloader
This is a quick and dirty kemono.party downloader using python. This is in very alpha state so many changes will happen over a short period of time.

## How to use:
1. Install python
2. Install bs4 using the command ```pip install bs4``` 
3. Download ```kemono-dl.py``` from [releases](https://github.com/AplhaSlayer1964/Kemono.party-Downloader/releases)
4. Get a cookie.txt file from kemono.party 
   - You can get the cookie text file using a [chrome](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid?hl=en) or [firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) extension
   - You must pass a cookie file or kemono.party's ddos protection won't let the script access the site 
5. Place users main page link or post link in the Users.txt file with one entry per line
   - links should look like: https://<span></span>kemono.party/SERVICE/user/USERID or https://<span></span>kemono.party/SERVICE/user/USERID/post/POSTID
6. Run ```python kemono-dl.py --cookies "cookie.txt"```
   - If no cookie.txt is passed in the script will quit
   - If no download location is passed then files will be saved to a Downloads folder in the current working directory

## Options:
- ```-h, --help``` Prints help test then exits
- ```--Verion``` Displays the current version then exits
- ```-o, --output``` Set path to download posts
- **REQUIRED** ```--cookies``` Set path to cookie.txt 

## Examples:
- ```python kemono-dl.py --cookies "cookie.txt" -o "C:\Users\User\Downloads"```

## Notes:
- Current file format is ```/Serivce_Name/User_name/[Posts date and time] post title```

## To do:
- [ ] Integrate youtube-dl for downloading external video links
- [ ] Extract all external links to a single file
- [ ] Duplicate files and downloads (Seems to be a problem on kemonos end with patreon)
- [ ] Images in content section aren't actually downloaded and might not display in Content.html
- [ ] Allow file naming structure to be changed in command line
- [X] Allow file location to be set in command line
- [X] Allow a cookie.txt file to be read in
- [ ] Add Discord service
- [ ] Stop comment.html from being made when there are no comments
- [X] fix encoding issue with content.html and comment.html
- [ ] gumroad does not lod dates and time (remove from folder name) 

## Keep in mind:
- Using this might get you IP banned from kemono party.
  - This has not happened to me but is a possibility 
- If the site changes the script might break.
- Kemono party places some external links as "files" currently they will not be downloaded.
- Kemono party seems to have files in the download section that are broken.
  - ie the file isn't actually a file
