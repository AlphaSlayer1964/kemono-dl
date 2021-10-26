import os
import datetime
import re
import argparse
from http.cookiejar import MozillaCookieJar, LoadError

from .version import __version__

def get_args():

    ap = argparse.ArgumentParser()

    ap.add_argument("--version",
                    action='store_true', default=False,
                    help="Displays the current version then exits")

    ap.add_argument("--cookies",
                    required=True,
                    help="Set path to cookie.txt (REQUIRED)")

    ap.add_argument("-l", "--links",
                    default=[],
                    help="Downloads user or post links. Suports comman seperated lists.")

    ap.add_argument("-f", "--fromfile",
                    default=[],
                    help="Download users and posts from a file seperated by a newline")

    ap.add_argument("--favorite-users",
                    action='store_true', default=False,
                    help="Downloads all users saved in your favorites. (Requires --cookies)")

    ap.add_argument("--favorite-posts",
                    action='store_true', default=False,
                    help="Downloads all posts saved in your favorites. (Requires --cookies)")

    ap.add_argument("-o", "--output",
                    default=None,
                    help="Set path to download posts")

    ap.add_argument("-a", "--archive",
                    default=None,
                    help="Downloads only posts that are not in provided archive file")

    ap.add_argument("-i", "--ignore-errors",
                    action='store_true', default=False,
                    help="Continue to download post(s) when an error occurs")

    ap.add_argument("--yt-dlp",
                    action='store_true', default=False,
                    help="Tries to Download embeds with yt-dlp. (experimental)")

    ap.add_argument("--date",
                    metavar="YYYYMMDD", default=None,
                    help="Only download posts from this date.")

    ap.add_argument("--datebefore",
                    metavar="YYYYMMDD", default=None,
                    help="Only download posts from this date and before.")

    ap.add_argument("--dateafter",
                    metavar="YYYYMMDD", default=None,
                    help="Only download posts from this date and after.")

    ap.add_argument("--min-filesize",
                    metavar="SIZE", default=None,
                    help="Do not download files smaller than SIZE. (ex. 100B, 20KB, 5MB, 1GB)")

    ap.add_argument("--max-filesize",
                    metavar="SIZE", default=None,
                    help="Do not download files larger than SIZE. (ex. 100B, 20KB, 5MB, 1GB)")

    ap.add_argument("--only-filetypes",
                    metavar="EXT", default=[],
                    help="Only downloads attachments and post file with given EXTs. Suports comman seperated lists. (ex. JPG, mp4, mp3, png)")

    ap.add_argument("--skip-filetypes",
                    metavar="EXT", default=[],
                    help="Skips attachments and post file with given EXTs. Suports comman seperated lists. (ex. JPG, mp4, mp3, png)")

    ap.add_argument("--skip-content",
                    action='store_true', default=False,
                    help="Skips saving posts content.")

    ap.add_argument("--skip-embeds",
                    action='store_true', default=False,
                    help="Skips saving posts embeds.")

    ap.add_argument("--skip-pfp-banner",
                    action='store_true', default=False,
                    help="Skips saving users pfp and banner.")

    ap.add_argument("--skip-comments",
                    action='store_true', default=False,
                    help="Skips saving posts comments.")

    ap.add_argument("--skip-postfile",
                    action='store_true', default=False,
                    help="Skips saving posts post file.")

    ap.add_argument("--skip-attachments",
                    action='store_true', default=False,
                    help="Skips saving posts attachments.")

    ap.add_argument("--force-external",
                    action='store_true', default=False,
                    help="Save all external links in content to a text file.")

    ap.add_argument("--force-indexing",
                    action='store_true', default=False,
                    help="Adds an indexing value to the attachment file names to preserve ordering.")

    ap.add_argument("--force-inline",
                    action='store_true', default=False,
                    help="Force download all external inline images found in post content. (experimental)")

    ap.add_argument("--force-yt-dlp",
                    action='store_true', default=False,
                    help="Tries to Download links in content with yt-dlp. (experimental)")

    args = vars(ap.parse_args())
    
    if args['version']: 
        print(__version__)
        quit()

    if args['cookies']:
        try:
            args['cookies'] = MozillaCookieJar(args['cookies']) 
            args['cookies'].load()
        except (LoadError, FileNotFoundError) as e:
            print(e)
            quit()

    if args['output']:
        if not os.path.exists(args['output']):
            try:
                os.makedirs(args['output'])
                args['output']= os.path.abspath(args['output'])
            except OSError as e:
                print(e)
                quit() 
    else:
        args['output'] = os.path.join(os.getcwd(), 'Downloads')

    if args['archive']:
        archive_path = os.path.dirname(os.path.abspath(args['archive']))
        if not os.path.isdir(archive_path):
            print('[Error] Invalid archive location: {}'.format(archive_path))
            quit()

    if args['only_filetypes'] and args['skip_filetypes']:
        print('[Error] You can only use one: --only-filetypes or --skip-filetypes')
        quit()
        
    def filetype_list(file_types):
        temp = []
        file_types = file_types.split(',')
        for file_type in file_types:
            temp.append(file_type.lower().strip().lstrip(' '))
        return temp
        
    if args['only_filetypes']:
        args['only_filetypes'] = filetype_list(args['only_filetypes'])
        
    if args['skip_filetypes']:
        args['skip_filetypes'] = filetype_list(args['skip_filetypes'])
    
    def valid_date(date, name):
        try: 
            return datetime.datetime.strptime(date, r'%Y%m%d')  
        except: 
            print("[Error] Incorrect data format for {}: {}, should be YYYYMMDD".format(name, date))
            quit()   
        
    if args['date']:
        args['date'] = valid_date(args['date'], 'date')
        
    if args['datebefore']:
        args['datebefore'] = valid_date(args['datebefore'], 'datebefore')
        
    if args['dateafter']:
        args['dateafter'] = valid_date(args['dateafter'], 'dateafter')

    def valid_size(size):
        found = re.search(r'([0-9]+)(GB|MB|KB|B)', size)
        if found:
            if found.group(2) == 'B':
                return str(int(found.group(1)))
            elif found.group(2) == 'KB':
                return str(int(found.group(1)) * 10**2) 
            elif found.group(2) == 'MB':
                return str(int(found.group(1)) * 10**6)
            elif found.group(2) == 'GB': 
                return str(int(found.group(1)) * 10**9)
        else: 
            print("[Error] Incorrect size format: {}, should be #GB, #MB, #KB, #B".format(size))
            quit()

    if args['max_filesize']:
        args['max_filesize'] = valid_size(args['max_filesize'])
        
    if args['min_filesize']:
        args['min_filesize'] = valid_size(args['min_filesize'])
   
    if args['links']:
        links = args['links'].split(',')
        args['links'] = []
        for link in links:
            args['links'].append(link.strip().lstrip(' ').split('?')[0])        
                
    if args['fromfile']:
        if not os.path.isfile(args['fromfile']):
            print('[Error] No file found: {}'.format(args['fromfile']))
            quit()
   
        with open(args['fromfile'],'r') as f:
            links = f.readlines()
        if not links:
            print('[Error] File is empty: {}'.format(args['fromfile']))
            quit()       
        
        args['fromfile'] = []
        for link in links:
            args['fromfile'].append(link.strip().lstrip().split('?')[0])

    return args