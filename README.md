# kemono-dl
This is a simple kemono.party downloader.

## How to use
1.  Install python
2.  Download source code from [releases](https://github.com/AplhaSlayer1964/Kemono.party-Downloader/releases) and extract it
3.  Then install requirements with  `pip install -r requirements.txt`
4. Get a cookie.txt file from kemono.party 
   - You can get the cookie text file using a [chrome](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid?hl=en) or [firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) extension
   - A cookie.txt file is required to use downloader.
5.  Run `python kemono-dl.py --cookies "cookie.txt" --links https://kemono.party/SERVICE/user/USERID`

## Options
```
-h, --help                       Prints help text then exits

--version                        Displays the current version then exits

--cookies FILE                   Set path to cookie.txt (**REQUIRED**)

-l, --links LINK(s)              Downloads user or post links. Suports comman
                                 seperated lists.
-f, --fromfile FILE              Download users and posts from a file seperated 
                                 by a newline
--favorite-users                 Downloads all users saved in your favorites.

--favorite-posts                 Downloads all posts saved in your favorites.

-o, --output FOLDER              Set path to download posts.

-a, --archive FILE               Downloads only posts that are not in provided 
                                 archive file. 
-i, --ignore-errors              Continue to download post(s) when an error 
                                 occurs.
--yt-dlp                         Tries to Download embeds with yt-dlp. 
                                 (experimental)
--date YYYYMMDD                  Only download posts from this date.
                                 (Format: YYYYMMDD)
--datebefore YYYYMMDD            Only download posts from this date and before.
                                 (Format: YYYYMMDD)
--dateafter YYYYMMDD             Only download posts from this date and after.
                                 (Format: YYYYMMDD)
--min-filesize SIZE              Do not download files smaller than this. 
                                 (Format: 1GB, 1MB, 1KB, 1B)
--max-filesize SIZE              Do not download files larger than this. 
                                 (Format: 1GB, 1MB, 1KB, 1B)
--only-filetypes EXT             Only downloads attachments and post file with 
                                 given extentions. Suports comman seperated lists. 
                                 (Format: JPG,mp4,png)
--skip-filetypes EXT             Skips attachments and post file with given 
                                 extentions. Suports comman seperated lists. 
                                 (Format: JPG,mp4,png)
--skip-content                   Skips saving posts content.

--skip-embeds                    Skips saving posts embeds.

--skip-comments                  Skips saving posts comments.

--skip-pfp-banner                Skips saving users pfp and banner.

--skip-postfile                  Skips saving posts post file.

--skip-attachments               Skips saving posts attachments.

--force-external                 Save all external links in content to a text file.

--force-indexing                 Adds an indexing value to the attachment file 
                                 names to preserve ordering
--force-inline                   Force download all external inline images found 
                                 in post content. (experimental)
--force-yt-dlp                   Tries to Download links in content with yt-dlp. 
                                 (experimental)
```
### Notes
-  Default download location is a `Downloads` folder in the current working directory (will be created automatically)
-  Input link format: `https://kemono.party/{service}/user/{user_id}` or `https://kemono.party/{service}/user/{user_id}/post/{post_is}`
-  Using any date option will not downlaod any gumroad posts because they have no dates
-  Using `--ignore-erros` posts with errors will not be archived
-  Using `--max-filesize` or `--min-filesize` will cause files that don't have `content-length` in their headers to not download. This mainly includes external inline images, pfp, and banners.
-  When using `--favorite-users` or `--favorite-posts` you must get your cookies.txt after logging into kemono.party.
-  You may need to install `ffmpeg` for `yt-dlp` to work
-  If downloading with `yt-dlp` fails that will count as an error and the post won't be archived. This includes yt-dlp failing because the site was just incompatible. I will need to look into seeing if there is a different error for these two circumstances.

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
