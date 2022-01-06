# kemono-dl
A simple downloader for kemono.party and coomer.party.

## How to use
1.  Install python. (Disable path length limit during install)
2.  Download source code for the [latest release](https://github.com/AplhaSlayer1964/kemono-dl/releases/latest) and extract it
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
-h, --help                                show this help message and exit
--version                                 Displays current version and exits.
--verbose                                 Display extra debug information and create a debug.log
--quiet                                   Suppress printing except for warnings, errors, and critical messages
--cookies FILE                            Files to read cookies from, can take a comma separated list. (REQUIRED)
-l, --links LINKS                         URLs to be downloaded, can take a comma separated list.
-f, --from-file FILE                      File containing URLs to download, one URL per line. Lines starting with a "#" are counted as comments (Alias:--fromfile)
--kemono-favorite-users                   Adds all favorite users posts from kemono.party. (Requires cookies while logged in)
--coomer-favorite-users                   Adds all favorite users posts from coomer.party. (Requires cookies while logged in)
--favorite-users-updated-within N_DAYS    Only download favorite users that have been updated within the last N days.
--kemono-favorite-posts                   Adds all favorites posts from kemono.party. (Requires cookies while logged in)
--coomer-favorite-posts                   Adds all favorites posts from coomer.party. (Requires cookies while logged in)
-o, --output PATH                         Path to download location
--restrict-names                          Restrict file names and folder names to only ASCII characters, and remove "&" and spaces
--no-indexing                             Do not index file names. Might cause issues if attachments have duplicate names.
-a, --archive FILE                        Downloads only posts that are not in provided archive file. (Can not be used with --update-posts)
--update-posts                            Updates already downloaded posts. Post must have json log file. (can not be used with --archive)
--yt-dlp                                  Tries to download embed with yt-dlp. (experimental)
--post-timeout SEC                        The amount of time in seconds to wait between downloading posts. (default: 0)
--retry-download COUNT                    The amount of times to retry / resume downloading a file. (default: 5)
--date YYYYMMDD                           Only download posts from this date.
--datebefore YYYYMMDD                     Only download posts from this date and before.
--dateafter YYYYMMDD                      Only download posts from this date and after.
--min-filesize SIZE                       Do not download files smaller than SIZE. (ex. #GB | #MB | #KB | #B)
--max-filesize SIZE                       Do not download files larger than SIZE. (ex. #GB | #MB | #KB | #B)
--only-filetypes EXT                      Only downloads files with the given extension(s), can take a comma separated list. (ex. "JPG,mp4,mp3,png")
--skip-filetypes EXT                      Skips files with the given extension(s), can take a comma separated list. (ex. "JPG,mp4,mp3,png")
--skip-content                            Skips saving post content to a file.
--skip-inline                             Skips saving post content inline images.
--skip-comments                           Skips saving post comments to file.
--skip-attachments                        Skips downloading ost attachments.
--skip-embed                              Skips saving post embed to file. (Alias: --skip-embeds)
--skip-json                               Skips saving post json. (--update-posts requires post json)
--save-icon                               Downloads user icon (Alias: --save-pfp)
--save-banner                             Downloads user banner
--extract-links                           Save all content links to a file. (Alias: --force-external)
--simulate                                Simulate Downloads (Applies all --skip commands and ignores --save-icon, --save-banner, --extract-links, --yt-dlp) (If using --archive file will be read from but not written to)
--user-agent UA                           Set a custom user agent
```
### Notes
-   Default download location is a `Downloads` folder in the current working directory (will be created automatically)
-   Excepted link formats:
    -   `https://{site}.party/{service}/user/{user_id}`
    -   `https://{site}.party/{service}/user/{user_id}/post/{post_id}`
    -   kemono.party Discord links are not supported 
-   Gumroad posts are not compatible with any date options.
-   You must get your cookie file while logged in to use:
    -   `--kemono-favorite-users`
    -   `--kemono-favorite-posts`
    -   `--coomer-favorite-users`
    -   `--coomer-favorite-posts`
-   You may need to install `ffmpeg` for `--yt-dlp` to work.
-   If you get an error with yt-dlp the post will still be archived when using `--archive`.
-   If you get an error with yt-dlp please report it to their [github](https://github.com/yt-dlp/yt-dlp)
-   If you get a 416 this should be fine, it should only happen if the file hash on the server is wrong.
    -   If this happens please check that the file downloaded correctly, if so report that the hash is incorrect to the appropriate site.
-   Kemono.party sometimes gives attachments filenames that are links (seems to only happen on patreon posts). This will remove the correct extension making it seem like an extensionless file. Hopefully they fix this or I will try to make a work around for it. 
### Examples
```bash
# downloads all users and posts from "users.txt" to "C:\Users\User\Downloads" while skipping saved posts in "archive.txt"
python kemono-dl.py --cookies "coomer_cookies.txt" -o "C:\Users\User\Downloads" --archive "archive.txt" --from-file "users.txt"

# only downloads user posts that were published on 1/1/21
python kemono-dl.py --cookies "kemono_cookies.txt" --date 20210101 --links "https://kemono.party/{service}/user/{user_id}"

# goes through all favorite users from kemono.party and posts from coomer.party only downloading files smaller than 100MB
python kemono-dl.py --cookies "kemono_cookies.txt,coomer_cookies.txt" --kemono-favorite-users --coomer-favorite-posts --max-filesize 100MB
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
If you wish to change the folder path for now you will need to edit these two functions in `main.py`

-   _set_current_user_path()
-   _set_current_post_path()

If you edit these functions and the program doesn't work correctly you will have to figure out the problem yourself. Do not file an issue in this case.
### Deprecated Options
```
-i, --ignore-errors
--skip-postfile
--force-indexing
--force-inline
--force-yt-dlp
--favorite-users
--favorite-posts
--skip-pfp-banner
```
## To do
-  [ ]   Allow file naming structure to be changed in command line
-  [ ]   Allow file path structure to be changed in command line
-  [ ]   Add Discord service (in progress)

## Keep in mind
-  Using this might get you IP banned from kemono.party or coomer.party.
