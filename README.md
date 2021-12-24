# kemono-dl
A simple downloader for kemono.party and coomer.party.

## How to use
1.  Install python. (Disable path length limit during install)
2.  Download source code from [releases](https://github.com/AplhaSlayer1964/Kemono.party-Downloader/releases) and extract it
3.  Then install requirements with  `pip install -r requirements.txt`
    - If the command doesn't run try adding `python -m`, `python3 -m`, or `py -m` to the front
4.  Get a cookie.txt file from kemono.party
    - You can get the cookie text file using a [Chrome](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid?hl=en) or [Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) extension
    - A cookie.txt file is required to use downloader.
    - For Firefox users pelase look at [pinned issue](https://github.com/AplhaSlayer1964/kemono-dl/issues/29#issuecomment-986313416)
5.  Run `python kemono-dl.py --cookies "cookie.txt" --links https://kemono.party/SERVICE/user/USERID`
    - If the script doesn't run try replacing `python` with `python3` or `py`

## Options
```
  -h, --help                    Show this help message and exit
  --version                     Displays current version and exits.
  --verbose                     Display extra debug information and create a debug.log
  --quiet                       Suppress printing except for warnings, errors, and critical messages
  --cookies COOKIES             Files to read cookies from, comma separated. (REQUIRED)
  -l, --links LINKS             Downloads URLs, can be separated by commas.
  -f, --fromfile FILE           File containing URLs to download, one URL per line.
  --kemono-favorite-users       Downloads all favorite users from kemono.party. (Requires cookies while logged in)
  --kemono-favorite-posts       Downloads all favorites posts from kemono.party. (Requires cookies while logged in)
  --coomer-favorite-users       Downloads all favorite users from coomer.party. (Requires cookies while logged in)
  --coomer-favorite-posts       Downloads all favorites posts from coomer.party. (Requires cookies while logged in)
  -o, --output PATH             Path to download location
  -a, --archive FILE            Downloads only posts that are not in provided archive file. (Can not be used with --update)
  -u, --update                  Updates already downloaded posts. Post must have json log file. (can not be used with --archive)
  --yt-dlp                      Tries to download embeds with yt-dlp. (experimental)
  --post-timeout SEC            The amount of time in seconds to wait between downloading posts. (default: 0)
  --retry-download COUNT        The amount of times to retry downloading a file. (default: 5)
  --date YYYYMMDD               Only download posts from this date.
  --datebefore YYYYMMDD         Only download posts from this date and before.
  --dateafter YYYYMMDD          Only download posts from this date and after.
  --min-filesize SIZE           Do not download files smaller than SIZE. (ex. #GB | #MB | #KB | #B)
  --max-filesize SIZE           Do not download files larger than SIZE. (ex. #GB | #MB | #KB | #B)
  --only-filetypes EXT          Only downloads attachments and post file with given EXTs, can be separated by commas. (ex. JPG,mp4,mp3,png)
  --skip-filetypes EXT          Skips attachments and post file with given EXTs, can be separated by commas. (ex. JPG,mp4,mp3,png)
  --skip-content                Skips posts content.
  --skip-embeds                 Skips posts embeds.
  --skip-comments               Skips posts comments.
  --skip-attachments            Skips attachments.
  --skip-json                   Skips json. (--update requires post json)
  --save-pfp                    Downloads user pfp
  --save-banner                 Downloads user banner
  --extract-links               Save all content links to a file.
  --no-indexing                 Do not index file names. Might cause issues if attachments have duplicate names.

```
### Notes
-  Default download location is a `Downloads` folder in the current working directory (will be created automatically)
-  link format: `https://kemono.party/{service}/user/{user_id}` or `https://kemono.party/{service}/user/{user_id}/post/{post_is}`
-  Using any date option will not download any gumroad posts because they have no dates
-  Using `--max-filesize` or `--min-filesize` will cause files that don't have `content-length` in their headers to not download. ie. pfp, banner, etc.
-  When using `--kemono-favorite-users`, `--kemono-favorite-posts`, `--coomer-favorite-users`, `--coomer-favorite-posts` you must get your cookies.txt after logging into the site.
-  You may need to install `ffmpeg` for `--yt-dlp` to work
-  If downloading with `--yt-dlp` any yt-dlp errors don't count as a post encountering an error. This means if using `--archive` and the embed does not download the post will still be archived.
-  Kemono.party has duplicate attachments on some posts hopefully they should not be downloaded.
-  Kemono.party has some attachments that have the incorrect hash value. If you get these errors please report them to kemono.party.
-  File and folder naming based on windows.

### Deprecated Options
-  `-i, --ignore-errors` 404 errors are skipped by default and 429 cause a 5 minute waite time. If you get any other errors they probably shouldn't be ignored
-  `--skip-postfile` post file is merged with attachments
-  `--force-indexing` files are indexed by default
-  `--force-inline` causes to many issues. Images not saved by party sites should still show up in content.html
-  `--force-yt-dlp` I found there were too many incorrect links causing issues
-  `--favorite-users` use --kemono-favorite-users or --coomer-favorite-users
-  `--favorite-posts` use --kemono-favorite-posts or --coomer-favorite-posts
-  `--skip-pfp-banner` decided not to download pfp or banner by default

### Renamed Options
-  `--force-external` changed name to better fit action, `--extract-links`



### Examples
```bash
# downloads all users and posts from "kemono.txt" to "C:\Users\User\Downloads" while skipping saved posts in "archive.txt"
python kemono-dl.py --cookies "cookie.txt" -o "C:\Users\User\Downloads" --archive "archive.txt" --fromfile "kemono.txt"

# only downloads user posts that were published on 1/1/21
python kemono-dl.py --cookies "cookie.txt" --date 20210101 --links https://kemono.party/SERVICE/user/USERID

# goes through all favorite users from kemono.party and posts from coomer.party only downloading files smaller than 100MB
python kemono-dl.py --cookies "cookie.txt" --kemono-favorite-users --coomer-favorite-posts --max-filesize 100MB
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
                ├── inline
                │   └── image.ext
                ├── embeds
                │   └── video.ext
                ├── content.html
                ├── comments.html
                ├── embeds.txt
                ├── content_links.txt
                ├── [{index}]_file.ext
                └── {post_id}.json
```

## To do
-  [ ]   Allow file naming structure to be changed in command line
-  [ ]   Allow file path structure to be changed in command line
-  [ ]   Add Discord service (in progress)

## Keep in mind
-  Using this might get you IP banned from kemono.party or coomer.party.
