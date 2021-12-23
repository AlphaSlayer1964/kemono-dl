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
                    help="Displays current version and exits.")

    ap.add_argument("--verbose",
                    action='store_true', default=False,
                    help="Display extra debug information and create a debug.log")

    ap.add_argument("--cookies",
                    metavar="FILE", type=str, default=None,
                    help="Files to read cookies from, comma separated. (REQUIRED)")

    ap.add_argument("-l", "--links",
                    default=[],
                    help="Downloads URLs, can be separated by commas.")

    ap.add_argument("-f", "--fromfile",
                    metavar="FILE", type=str, default=[],
                    help="File containing URLs to download, one URL per line. Lines starting with a '#' don't count")

    ap.add_argument("--kemono-favorite-users",
                    action='store_true', default=False,
                    help="Downloads all favorite users from kemono.party. (Requires cookies while logged in)")

    ap.add_argument("--kemono-favorite-posts",
                    action='store_true', default=False,
                    help="Downloads all favorites posts from kemono.party. (Requires cookies while logged in)")

    ap.add_argument("--coomer-favorite-users",
                    action='store_true', default=False,
                    help="Downloads all favorite users from coomer.party. (Requires cookies while logged in)")

    ap.add_argument("--coomer-favorite-posts",
                    action='store_true', default=False,
                    help="Downloads all favorites posts from coomer.party. (Requires cookies while logged in)")

    ap.add_argument("-o", "--output",
                    metavar="PATH", type=str, default=None,
                    help="Path to download location")

    ap.add_argument("-a", "--archive",
                    metavar="FILE", type=str, default=None,
                    help="Downloads only posts that are not in provided archive file. (Can not be used with --update)")

    ap.add_argument("-u", "--update",
                    action='store_true', default=False,
                    help="Updates already downloaded posts. Post must have json log file. (can not be used with --archive)")

    ap.add_argument("--yt-dlp",
                    action='store_true', default=False,
                    help="Tries to download embeds with yt-dlp. (experimental)")

    ap.add_argument("--post-timeout",
                    metavar="SEC", type=int, default=0,
                    help="The amount of time in seconds to wait between downloading posts. (default: 0)")

    ap.add_argument("--retry-download",
                    metavar="COUNT", type=int, default=5,
                    help="The amount of times to retry downloading a file. (default: 5)")

    ap.add_argument("--date",
                    metavar="YYYYMMDD", type=str, default=None,
                    help="Only download posts from this date.")

    ap.add_argument("--datebefore",
                    metavar="YYYYMMDD", type=str, default=None,
                    help="Only download posts from this date and before.")

    ap.add_argument("--dateafter",
                    metavar="YYYYMMDD", type=str, default=None,
                    help="Only download posts from this date and after.")

    ap.add_argument("--min-filesize",
                    metavar="SIZE", type=str, default='0B',
                    help="Do not download files smaller than SIZE. (ex. #GB | #MB | #KB | #B)")

    ap.add_argument("--max-filesize",
                    metavar="SIZE", type=str, default='inf',
                    help="Do not download files larger than SIZE. (ex. #GB | #MB | #KB | #B)")

    ap.add_argument("--only-filetypes",
                    metavar="EXT", type=str, default=[],
                    help="Only downloads attachments and post file with given EXTs, can be separated by commas. (ex. JPG,mp4,mp3,png)")

    ap.add_argument("--skip-filetypes",
                    metavar="EXT", type=str, default=[],
                    help="Skips attachments and post file with given EXTs, can be separated by commas. (ex. JPG,mp4,mp3,png)")

    ap.add_argument("--skip-content",
                    action='store_true', default=False,
                    help="Skips posts content.")

    ap.add_argument("--skip-embeds",
                    action='store_true', default=False,
                    help="Skips posts embeds. Also skips downloading post embeds using --yt-dlp")

    ap.add_argument("--skip-comments",
                    action='store_true', default=False,
                    help="Skips posts comments.")

    ap.add_argument("--skip-attachments",
                    action='store_true', default=False,
                    help="Skips attachments.")

    ap.add_argument("--skip-json",
                    action='store_true', default=False,
                    help="Skips json. (--update requires post json)")

    ap.add_argument("--extract-links",
                    action='store_true', default=False,
                    help="Save all content links to a file.")

    ap.add_argument("--no-indexing",
                    action='store_true', default=False,
                    help="Do not index file names. Might cause issues if attachments have duplicate names.")

    ap.add_argument("--quiet",
                    action='store_true', default=False,
                    help="Suppress printing except for warnings, errors, and critical messages")

    ap.add_argument("--save-pfp",
                    action='store_true', default=False,
                    help="Downloads user pfp")

    ap.add_argument("--save-banner",
                    action='store_true', default=False,
                    help="Downloads user banner")

    # renamed
    ap.add_argument("--force-external",
                    action='store_true', default=False,
                    help="RENAMED changed name to better fit action, --extract-links")
    # deprecated
    ap.add_argument("-i", "--ignore-errors",
                    action='store_true', default=False,
                    help="DEPROCATED 404 errors are skipped by default and 429 cause a 5 minute waite time. If you get any other errors they probably shouldn\'t be ignored")
    ap.add_argument("--skip-postfile",
                    action='store_true', default=False,
                    help="DEPROCATED post file is merged with attachments")
    ap.add_argument("--force-indexing",
                    action='store_true', default=False,
                    help="DEPROCATED files are indexed by default")
    ap.add_argument("--force-inline",
                    action='store_true', default=False,
                    help="DEPROCATED causes to many issues. Images not saved by party sites should still show up in content.html")
    ap.add_argument("--force-yt-dlp",
                    action='store_true', default=False,
                    help="DEPROCATED I found there were too many incorrect links causing issues")
    ap.add_argument("--favorite-users",
                    action='store_true', default=False,
                    help="DEPROCATED use --kemono-favorite-users or --coomer-favorite-users")
    ap.add_argument("--favorite-posts",
                    action='store_true', default=False,
                    help="DEPROCATED use --kemono-favorite-posts or --coomer-favorite-posts")
    ap.add_argument("--skip-pfp-banner",
                    action='store_true', default=False,
                    help="DEPROCATED decided not to download pfp or banner by default")

    args = vars(ap.parse_args())

    # deprocated
    if args['favorite_users']:
        print('--favorite-users: DEPROCATED use --kemono-favorite-users or --coomer-favorite-users')
    if args['favorite_posts']:
        print('--favorite-posts: DEPROCATED use --kemono-favorite-posts or --coomer-favorite-posts')
    if args['force_yt_dlp']:
        print('--force-yt-dlp: DEPROCATED I found there were too many incorrect links causing issues')
    if args['force_inline']:
        print('--force-inline: DEPROCATED causes to many issues. Images not saved by party sites should still show up in content.html')
    if args['ignore_errors']:
        print('--ignore-errors: DEPROCATED 404 errors are skipped by default and 429 cause a 5 minute waite time. If you get any other errors they probably shouldn\'t be ignored')
    if args['skip_postfile']:
        print('--skip-postfile: DEPROCATED post files is merged with attachments')
    if args['force_indexing']:
        print('--force-indexing: DEPROCATED files are indexed by default')
    if args['skip_pfp_banner']:
        print('--skip-pfp-banner: DEPROCATED decided not to download pfp or banner by default')
    # renamed
    if args['force_external']:
        print('--force-external: RENAMED to --extract-links : changed name to better fit action')

    if args['version']:
        print(__version__)
        quit()

    if args['update'] and args['archive']:
        print('--archive, --update: Only use one at a time')
        quit()

    # takes a list of cookie files and marges than and makes them usable by requests
    if args['cookies']:
        cookie_files = args['cookies'].split(',')
        try:
            if len(cookie_files) == 1:
                args['cookies'] = MozillaCookieJar(args['cookies'])
                args['cookies'].load()
            elif len(cookie_files) == 2:
                args['cookies'] = MozillaCookieJar()
                args['cookies'].load(cookie_files[0])
                args['cookies'].load(cookie_files[1])
            else:
                print('--cookies: You should only be passing in two cookie files, one for kemono.party and one for coomer.party')
        except (LoadError, FileNotFoundError) as e:
            print(e)
            quit()
    else:
        print('--cookies: No file passed')
        quit()

    # takes in a file directory
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
            print(f"--archive {archive_path}: Archive directory does not exist")
            quit()

    if args['only_filetypes'] and args['skip_filetypes']:
        print('--only-filetypes, --skip-filetypes: Only use one at a time')
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

    def valid_date(date, arg):
        try:
            return datetime.datetime.strptime(date, r'%Y%m%d')
        except:
            print(f"{arg} {date}: Incorrect format: YYYYMMDD")
            quit()

    args['date'] = valid_date(args['date'], '--date') if args['date'] else datetime.datetime.min
    args['datebefore'] = valid_date(args['datebefore'], '--datebefore') if args['datebefore'] else datetime.datetime.min
    args['dateafter'] = valid_date(args['dateafter'], '--dateafter') if args['dateafter'] else datetime.datetime.max

    def valid_size(size, arg):
        if size in {'0', 'inf'}:
            return size
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
            print(f"{arg} {size}: Incorrect format: ex 1B 1KB 1MB 1GB")
            quit()

    if args['max_filesize']:
        args['max_filesize'] = valid_size(args['max_filesize'], '--max-filesize')
    if args['min_filesize']:
        args['min_filesize'] = valid_size(args['min_filesize'], '--min-filesize')

    if args['links']:
        links = args['links'].split(',')
        args['links'] = []
        for link in links:
            args['links'].append(link.strip().lstrip(' ').split('?')[0])

    if args['fromfile']:
        if not os.path.isfile(args['fromfile']):
            print(f"--fromfile {args['fromfile']}: No file found / Not a file")
            quit()
        with open(args['fromfile'],'r') as f:
            links = f.readlines()
        if not links:
            print(f"--fromfile {args['fromfile']}: File is empty")
            quit()
        args['fromfile'] = []
        for link in links:
            # lines starting with '#' are ignored
            if link[0] != '#':
                args['fromfile'].append(link.strip().lstrip().split('?')[0])

    return args