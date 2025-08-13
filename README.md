# kemono-dl
A downloader tool for kemono and coomer websties.

## How to use
1.  Install python 3. (Disable path length limit during install)
2.  Download source code for the [latest release](https://github.com/AplhaSlayer1964/kemono-dl/releases/latest) and extract it
3.  Then install requirements with  `pip install -r requirements.txt`
    - If the command doesn't run try adding `python -m`, `python3 -m`, or `py -m` to the front
4.  Run `python -m kemono_dl "https://kemono.party/SERVICE/user/USERID"`
    - If the script doesn't run try replacing `python` with `python3` or `py`

# Command Line Options

`--path PATH`  
Set the base path for downloads.

`--output OUTPUT_TEMPLATE`  
Set the file name pattern for attachments. Default "{service}/{creator_id}/{server_filename}"   

`--batch-file FILE`
A file with one url per line.

`--coomer-cookies FILE`  
A cookies file for the coomer site. Required for `--favorite-creators-coomer`

`--kemono-cookies FILE`  
A cookies file for the kemono site. Required for `--favorite-creators-kemono`

`--favorite-creators-coomer`  
Downloads all favorite creators from coomer site

`--favorite-creators-kemono`  
Downloads all favorite creators from kemono site

## Output Template Variables

-   `{service}`  
The service of the post.  
-   `{creator_id}`  
The user id of the poster.  
-   `{post_id}`  
The post id.  
-   `{post_title}`  
The post title.
-   `{server_filename}`  
The server file name.  
-   `{server_file_name}`  
The server file name without the extention.
-   `{server_file_ext}`  
The server file extension.  
-   `{filename}`  
The original file name.  
-   `{file_name}`  
The original file name without the extention.
-   `{file_ext}`  
The original file extension.  
-   `{sha256}`  
The sha256 hash of the file.
