# kemono-dl
A downloader tool for kemono.party and coomer.party.

## How to use
1.  Install python 3. (Disable path length limit during install)
2.  Download source code for the [latest release](https://github.com/AplhaSlayer1964/kemono-dl/releases/latest) and extract it
3.  Then install requirements with  `pip install -r requirements.txt`
    - If the command doesn't run try adding `python -m`, `python3 -m`, or `py -m` to the front
4.  Get a cookie.txt file from kemono.party/coomer.party
    - You can get a cookie text file on [Chrome](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) or [Firefox](https://addons.mozilla.org/firefox/addon/cookies-txt/) with this extension.
    - A cookie.txt file is required to use downloader!
5.  Run `python kemono-dl.py --cookies "cookie.txt" --links https://kemono.party/SERVICE/user/USERID`
    - If the script doesn't run try replacing `python` with `python3` or `py`

# Command Line Options

## Required!

`--cookies FILE`  
Takes in a cookie file or a list of cookie files separated by a comma. Used to get around the DDOS protection. Your cookie file must have been gotten while logged in to use the favorite options.  

## What posts to download

`--links LINKS`  
Takes in a url or list of urls separated by a comma.  
`--from-file FILE`  
Reads in a file with urls separated by new lines. Lines starting with # will not be read in.  
`--kemono-fav-users SERVICE`  
Downloads favorite users from kemono.party/su of specified type or types separated by a comma. Types include: all, patreon, fanbox, gumroad, subscribestar, dlsite, fantia. Your cookie file must have been gotten while logged in to work.  
`--coomer-fav-users SERVICE`  
Downloads favorite users from coomer.party/su of specified type or types separated by a comma. Types include: all, onlyfans. Your cookie file must have been gotten while logged in to work.  
`--kemono-fav-posts`  
Downloads favorite posts from kemono.party/su. Your cookie file must have been gotten while logged in to work.  
`--coomer-fav-posts`  
Downloads favorite posts from coomer.party/su. Your cookie file must have been gotten while logged in to work.  

## What files to download

`--inline`  
Download the inline images from the post content.  
`--content`  
Write the post content to a html file. The html file includes comments if `--comments` is passed.  
`--comments`  
Write the post comments to a html file.  
`--json`  
Write the post json to a file.  
`--extract-links`  
Write extracted links from post content to a text file.  
`--dms`  
Write user dms to a html file. Only works when a user url is passed.  
`--icon`  
Download the users profile icon. Only works when a user url is passed.  
`--banner`  
Download the users profile banner. Only works when a user url is passed.  
`--yt-dlp` (UNDER CONSTRUCTION)  
Try to download the post embed with yt-dlp.  
`--skip-attachments`  
Do not download post attachments.  
`--skip-local-hash`  
Do not check hash for downloaded local files.  
`--overwrite`  
Overwrite any previously created files.  

## Output

`--dirname-pattern PATTERN`  
Set the file path pattern for where files are downloaded. See [Output Patterns](https://github.com/AplhaSlayer1964/kemono-dl#output-patterns=) for more detail.  
`--filename-pattern PATTERN`  
Set the file name pattern for attachments. See [Output Patterns](https://github.com/AplhaSlayer1964/kemono-dl#output-patterns=) for more detail.  
`--inline-filename-pattern PATTERN`  
Set the file name pattern for inline images. See [Output Patterns](https://github.com/AplhaSlayer1964/kemono-dl#output-patterns=) for more detail.  
`--other-filename-pattern PATTERN`  
Set the file name pattern for post content, extracted links, and json. See [Output Patterns](https://github.com/AplhaSlayer1964/kemono-dl#output-patterns=) for more detail.  
`--user-filename-pattern PATTERN`  
Set the file name pattern for icon, banner, and dms. See [Output Patterns](https://github.com/AplhaSlayer1964/kemono-dl#output-patterns=) for more detail.  
`--date-strf-pattern PATTERN`  
Set the date strf pattern variable. See [Output Patterns](https://github.com/AplhaSlayer1964/kemono-dl#output-patterns=) for more detail.  
`--restrict-names`  
Set all file and folder names to be limited to only the ascii character set.  

## Download Filters

`--archive FILE`  
Only download posts that are not recorded in the archive file.  
`--date YYYYMMDD`  
Only download posts published from this date.  
`--datebefore YYYYMMDD`  
Only download posts published before this date.  
`--dateafter YYYYMMDD`  
Only download posts published after this date.  
`--user-updated-datebefore YYYYMMDD`  
Only download user posts if the user was updated before this date.  
`--user-updated-dateafter YYYYMMDD`  
Only download user posts if the user was updated after this date.  
`--min-filesize SIZE`  
Only download attachments or inline images with greater than this file size. (ex #gb | #mb | #kb | #b)  
`--max-filesize SIZE`  
Only download attachments or inline images with less than this file size. (ex #gb | #mb | #kb | #b)  
`--only-filetypes EXT`  
Only download attachments or inline images with the given file type(s). Takes a file extensions or list of file extensions separated by a comma. (ex mp4,jpg,gif,zip)  
`--skip-filetypes EXT`  
Only download attachments or inline images without the given file type(s). Takes a file extensions or list of file extensions separated by a comma. (ex mp4,jpg,gif,zip)  

## Other

`--help`  
Prints all available options and exit.  
`--version`  
Print the version and exit.  
`--verbose`  
Display debug information and copies output to a file.  
`--quite`  
Suppress printing except for warnings, errors, and exceptions.  
`--simulate`  
Simulate the given command and do not write to disk.  
`--no-part-files`  
Do not save attachments or inline images as .part files while downloading. Files partially downloaded will not be resumed if program stops.  
`--yt-dlp-args ARGS` (UNDER CONSTRUCTION)  
The args yt-dlp will use to download with. Formatted as a python dictionary object.  
`--post-timeout SEC`  
The time in seconds to wait between downloading posts. (default: 0)  
`--retry COUNT`  
The amount of times to retry / resume downloading a file. (default: 5)  
`--ratelimit-sleep SEC`  
The time in seconds to wait after being ratelimited (default: 120)    

# Notes
-   Excepted link formats:
    -   `https://{site}.party/{service}/user/{user_id}`
    -   `https://{site}.party/{service}/user/{user_id}/post/{post_id}`
-   By default files are saved as .part files until completed.
-   I assume the .party site has the correct hash for attachments. This may not be the case in rare cases.
    -   If the server is incorrect the file will remain a .part file. 
    -   You can remove the .part from the file name and see if it downloaded correctly.
        -   If it is correct but the downloader said the hash was wrong please report it in the [pinned issue]() so I can report it to the .party site.
-   Some files do not have the file size in the response header and will not be downloaded when using `--min-filesize` or `--max-filesize`.
    -   `.pdf` is a known file type that will never return file size from response headers.
-   Gumroad posts published date is not provided so `--date`, `--datebefore`, and `--dateafter` will always skip Gumroad posts.  
-   Files will not be overwritten by default.
-   Inline images default names are the file hash.
-   For getting `--yt-dlp` to work please follow its instillation [guide](https://github.com/yt-dlp/yt-dlp#installation=).
-   For `--yt-dlp-args ARGS` refer to this for available [options](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L181). 

# Output Patterns

## Variables

The pattern options allow you to modify the file path and file name using variables from the post. `--dirname-pattern` is the base file path for all post files. 
All file name patterns are appended to the end of the `--dirname-pattern`. File name patterns may also contain sub folder paths specific to that type of file such as with the default pattern for `--inline-filename-pattern`.  
  
All variables referring to dates are controlled by `--date-strf-pattern`. Standard python datetime strftime() format codes can be found [here](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).

### All Options
-   `{site}`  
The .party site the post is hosted on.  (ie. kemono.party or coomer.party)
-   `{service}`  
The service of the post.  
-   `{user_id}`  
The user id of the poster.  
-   `{username}`  
The user name of the poster.  
-   `{id}`  
The post id.  
-   `{title}`  
The post title.  
-   `{published}`  
The published date of the post.  
-   `{added}`  
The date the post was added to the .party site.  
-   `{updated}`  
The date the post was last updated on the .party site.  
-   `{user_updated}`  
The date the user was last updated on the .party site.  

### Only file names
-   `{ext}`  
The file extension.  
-   `{filename}`  
The original file name.  
-   `{index}`  
The files index order. Only `--filename-pattern` and `--inline-filename-pattern`  
-   `{hash}`  
The hash of the file. Only `--filename-pattern` and `--inline-filename-pattern`    


## Default Patterns
`--dirname-pattern`  
```python
"Downloads\{service}\{username} [{user_id}]"  
```
`--filename-pattern`  
```python
"[{published}] [{id}] {title}\{index}_{filename}.{ext}"  
```
`--inline-filename-pattern`  
```python
"[{published}] [{id}] {title}\inline\{index}_{filename}.{ext}"  
```
`--other-filename-pattern`  
```python
"[{published}] [{id}] {title}\[{id}]_{filename}.{ext}"  
```
`--user-filename-pattern`  
```python
"[{user_id}]_{filename}.{ext}"  
```
`--date-strf-pattern`  
```python
"%Y%m%d"  
```

## Examples
TODO
