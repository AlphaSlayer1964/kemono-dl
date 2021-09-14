# Kemono.party-Downloader
This is a quick and dirty kemono.party downloader using python.

## How to use
1. Install python
2. Install bs4 using the command ```pip install bs4``` 
3. Edit kemono-dl.py and change all four of the cookie values for kemonoparty
   - You can get the cookie values from using a chrome or firefox extension
   - You must pass a cookie value or their ddos protection won't let the script access the site 
4. Place users main page link or post link in the Users.txt file with one entry per line
   - links should look like: https://<span></span>kemono.party/patreon/user/USERID or https://<span></span>kemono.party/patreon/user/USERID/post/POSTID
5. Run ```python kemono-dl.py``` or with a download location ```python kemono-dl.py "C:\Users\User\Downloads"```
   - If no download location is passed then file will be download to the current working directory

## To do:
- [ ] Integrate youtube-dl for downloading external video links
- [ ] Extract all external links to a single file
- [ ] Duplicate names for files and downloads
- [ ] Images in content section might not display in Content.html? (maybe new method of saving content is needed)
- [ ] Allow file structure to be changed in command line
- [X] Allow file location to be set in command line
- [ ] Allow a cookie.txt file to be read in 

## Keep in mind
- Using this might get you IP banned from kemono party.
  - This has not happened to me but is a possibility 
- If the site changes the script might break.
- Kemono party places some external links as "files" currently they will not be downloaded.
- Kemono party seems to have files in the download section that are broken.
  - ie the file isn't actually a file
