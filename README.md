# kemono-dl
This is a simple kemono.party downloader.

## How to use
1.  Install python. (Disable path length limit during install)
2.  Download source code from [releases](https://github.com/AplhaSlayer1964/Kemono.party-Downloader/releases) and extract it
3.  Then install requirements with  `pip install -r requirements.txt`
4. Get a cookie.txt file from kemono.party
   - You can get the cookie text file using a [chrome](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid?hl=en) or [firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) extension
   - A cookie.txt file is required to use downloader.
5.  Run `python kemono-dl.py --cookies "cookie.txt" --links https://kemono.party/SERVICE/user/USERID`

## Options
```
  -h, --help                    show this help message and exit
  --version                     Displays current version and exits.
  --cookies COOKIES             File to read cookies from. (REQUIRED)
  -l LINKS, --links LINKS       Downloads URLs, can be separated by commas.
  -f FILE, --fromfile FILE      File containing URLs to download, one URL per line.
  --favorite-users              Downloads all favorite users. (Requires cookies while logged in)
  --favorite-posts              Downloads all favorites posts. (Requires cookies while logged in)
  -o PATH, --output PATH        Path to download location
  -a FILE, --archive FILE       Downloads only posts that are not in provided archive file. (Can not be used with --update)
  -u, --update                  Updates already downloaded posts. Post must have json log file. (can not be used with --archive)
  -i, --ignore-errors           Continue to download posts when an error occurs.
  --yt-dlp                      Tries to download embeds with yt-dlp. (experimental)
  --post-timeout SEC            The amount of time in seconds to wait between downloading posts. (default: 0)
  --retry-download COUNT        The amount of times to retry downloading a file. (acts like --ignores-errors) (default: 0)
  --date DATE                   Only download posts from this date.
  --datebefore DATE             Only download posts from this date and before.
  --dateafter DATE              Only download posts from this date and after.
  --min-filesize SIZE           Do not download files smaller than SIZE. (ex. #GB | #MB | #KB | #B)
  --max-filesize SIZE           Do not download files larger than SIZE. (ex. #GB | #MB | #KB | #B)
  --only-filetypes EXT          Only downloads attachments and post file with given EXTs, can be separated by commas. (ex. JPG,mp4,mp3,png)
  --skip-filetypes EXT          Skips attachments and post file with given EXTs, can be separated by commas. (ex. JPG,mp4,mp3,png)
  --skip-content                Skips posts content.
  --skip-embeds                 Skips posts embeds.
  --skip-pfp-banner             Skips user pfp and banner.
  --skip-comments               Skips posts comments.
  --skip-postfile               Skips post file.
  --skip-attachments            Skips attachments.
  --skip-json                   Skips json. (--update requires post json)
  --force-external              Save all content links to a file.
  --force-indexing              Attachments and inline images will have indexing numbers added to their file names.
  --force-inline                Download all external inline images found in post content. (experimental)
  --force-yt-dlp                Tries to download content links with yt-dlp. (experimental)
```
### Notes
-  Default download location is a `Downloads` folder in the current working directory (will be created automatically)
-  Input link format: `https://kemono.party/{service}/user/{user_id}` or `https://kemono.party/{service}/user/{user_id}/post/{post_is}`
-  Using any date option will not download any gumroad posts because they have no dates
-  Using `--ignore-errors` posts with errors will not be archived
-  Using `--max-filesize` or `--min-filesize` will cause files that don't have `content-length` in their headers to not download. ie. pfp, banner, etc.
-  When using `--favorite-users` or `--favorite-posts` you must get your cookies.txt after logging into kemono.party.
-  You may need to install `ffmpeg` for `yt-dlp` to work
-  If downloading with `yt-dlp` some errors will not count as errors for kemono-dl: Unsupported URL, Video unavailable, and HTTP Error 404
-  File hashes are checked with server before redownloading.
   - Some files do not have hashes on kemonos website or the file hash is incorrect on their end so some files might redownload even though it is the same.    

### Known Bugs
- When downloading a file it might just stop downloading, I believe this happens when a large file is downloaded and the site doesn't have it cached so the connection gets timed out after a while. I am still looking into this issue.

### Examples
```bash
# downloads all users and posts from "kemono.txt" to "C:\Users\User\Downloads" while skipping saved posts in "archive.txt"
python kemono-dl.py --cookies "cookie.txt" -o "C:\Users\User\Downloads" --archive "archive.txt" --fromfile "kemono.txt"

# only downloads user posts that were published on 1/1/21
python kemono-dl.py --cookies "cookie.txt" --date 20210101 --links https://kemono.party/SERVICE/user/USERID

# goes through all favorite users and posts only downloading files smaller than 100MB
python kemono-dl.py --cookies "cookie.txt" --favorite-users --favorite-posts --max-filesize 100MB

# downloads a post and user while ignoring downloading errors
python kemono-dl.py --cookies "cookie.txt" -i -l https://kemono.party/SERVICE/user/USERID/post/POSTID,https://kemono.party/SERVICE/user/USERID
```

### Default File Output Format
```
CWD
├── kemono-dl.py
└── Downloads
    └── {service}
        └── {username} [{user_id}]
            ├── {username} [{user_id}] icon.ext
            ├── {username} [{user_id}] banner.ext
            └── [{date}] [{post_id}] {post_title}
                ├── external files
                │   └── video.mp4
                ├── attachments
                │   └── attachment.ext
                ├── inline
                │   └── image.ext
                ├── content.html
                ├── comments.html
                ├── embeds.txt
                ├── external_links.txt
                ├── file.ext
                └── {post_id}.json
```

## To do
- [ ] Allow file naming structure to be changed in command line
- [ ] Allow file path structure to be changed in command line
- [ ] Add Discord service (in progress)

## Keep in mind
- Using this might get you IP banned from kemono party.
  - This is highly unlikely now that I switched to using their API!
- If the site changes the script might break.
   - This is also now highly unlikely now that I switched to using their API!
