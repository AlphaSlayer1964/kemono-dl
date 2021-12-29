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

    ap.add_argument("--quiet",
                    action='store_true', default=False,
                    help="Suppress printing except for warnings, errors, and critical messages")

    ap.add_argument("--cookies",
                    metavar="FILE", type=str, default=None,
                    help="Files to read cookies from, can take a comma separated list. (REQUIRED)")

    ap.add_argument("-l","--links",
                    metavar="LINKS", type=str, default=[],
                    help="URLs to be downloaded, can take a comma separated list.")

    ap.add_argument("-f","--from-file","--fromfile",
                    metavar="FILE", type=str, default=[],
                    help="File containing URLs to download, one URL per line. Lines starting with a \"#\" are counted as comments (Aliese: --fromfile)")

    ap.add_argument("--kemono-favorite-users",
                    action='store_true', default=False,
                    help="Adds all favorite users posts from kemono.party. (Requires cookies while logged in)")

    ap.add_argument("--coomer-favorite-users",
                    action='store_true', default=False,
                    help="Adds all favorite users posts from coomer.party. (Requires cookies while logged in)")

    ap.add_argument("--favorite-users-updated-within",
                    metavar="N_DAYS", type=int, default=0,
                    help="Only download favorite users that have been updated within the last N days.")

    ap.add_argument("--kemono-favorite-posts",
                    action='store_true', default=False,
                    help="Adds all favorites posts from kemono.party. (Requires cookies while logged in)")

    ap.add_argument("--coomer-favorite-posts",
                    action='store_true', default=False,
                    help="Adds all favorites posts from coomer.party. (Requires cookies while logged in)")

    ap.add_argument("-o","--output",
                    metavar="PATH", type=str, default=None,
                    help="Path to download location")

    ap.add_argument("--restrict-names",
                    action='store_true', default=False,
                    help='Restrict filenames and foldernames to only ASCII characters, and remove "&" and spaces')

    ap.add_argument("--no-indexing",
                    action='store_true', default=False,
                    help="Do not index file names. Might cause issues if attachments have duplicate names.")

    ap.add_argument("-a","--archive",
                    metavar="FILE", type=str, default=None,
                    help="Downloads only posts that are not in provided archive file. (Can not be used with --update-posts)")

    ap.add_argument("--update-posts",
                    action='store_true', default=False,
                    help="Updates already downloaded posts. Post must have json log file. (can not be used with --archive)")

    ap.add_argument("--yt-dlp",
                    action='store_true', default=False,
                    help="Tries to download embed with yt-dlp. (experimental)")

    ap.add_argument("--post-timeout",
                    metavar="SEC", type=int, default=0,
                    help="The amount of time in seconds to wait between downloading posts. (default: 0)")

    ap.add_argument("--retry-download",
                    metavar="COUNT", type=int, default=5,
                    help="The amount of times to retry / resume downloading a file. (default: 5)")

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
                    help="Only downloads files with the given extension(s), can take a comma separated list. (ex. \"JPG,mp4,mp3,png\")")

    ap.add_argument("--skip-filetypes",
                    metavar="EXT", type=str, default=[],
                    help="Skips files with the given extension(s), can take a comma separated list. (ex. \"JPG,mp4,mp3,png\")")

    ap.add_argument("--skip-content",
                    action='store_true', default=False,
                    help="Skips saving post content to a file.")

    ap.add_argument("--skip-comments",
                    action='store_true', default=False,
                    help="Skips saving post comments to file.")

    ap.add_argument("--skip-attachments",
                    action='store_true', default=False,
                    help="Skips downloading ost attachments.")

    ap.add_argument("--skip-embed","--skip-embeds",
                    action='store_true', default=False,
                    help="Skips saving post embed to file. (--yt-dlp is ignored) (Aliese: --skip-embeds)")

    ap.add_argument("--skip-json",
                    action='store_true', default=False,
                    help="Skips saving post json. (--update-posts requires post json)")

    ap.add_argument("--save-icon","--save-pfp",
                    action='store_true', default=False,
                    help="Downloads user icon (Aliese: --save-pfp)")

    ap.add_argument("--save-banner",
                    action='store_true', default=False,
                    help="Downloads user banner")

    ap.add_argument("--extract-links","--force-external",
                    action='store_true', default=False,
                    help="Save all content links to a file. (Aliese: --force-external)")

    # add more simulation options
    ap.add_argument("--simulate",
                    action='store_true', default=False,
                    help="Simulate Downloads")

    ap.add_argument("--user-agent",
                    metavar="UA", type=str, default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
                    help="Set a custom user agent")

    # want to add
    # --windows-filenames
    # --trim-filenames LENGTH
    # --force-overwrites
    # --no-continue
    # --part
    # --no-part

    # deprecated
    deprecated_list = (
        "--ignore-errors",
        "--skip-postfile",
        "--force-indexing",
        "--force-inline",
        "--force-yt-dlp",
        "--favorite-users",
        "--favorite-posts",
        "--skip-pfp-banner"
    )
    ap.add_argument("-i", "--ignore-errors",action='store_true',default=False,help="DEPROCATED")
    ap.add_argument("--skip-postfile",action='store_true',default=False,help="DEPROCATED")
    ap.add_argument("--force-indexing",action='store_true',default=False,help="DEPROCATED")
    ap.add_argument("--force-inline",action='store_true',default=False,help="DEPROCATED")
    ap.add_argument("--force-yt-dlp",action='store_true',default=False,help="DEPROCATED")
    ap.add_argument("--favorite-users",action='store_true',default=False,help="DEPROCATED")
    ap.add_argument("--favorite-posts",action='store_true',default=False,help="DEPROCATED")
    ap.add_argument("--skip-pfp-banner",action='store_true',default=False,help="DEPROCATED")

    args = vars(ap.parse_args())

    # print deprocated arguments
    for key, value in args.items():
        if key in deprecated_list and value:
            print(f"The argument \"{key}\" is DEPROCATED and will be ignored")

    if args['version']:
        print(__version__)
        quit()

    if args['update_posts'] and args['archive']:
        print('--archive, --update-posts: Only use one at a time')
        quit()

    # takes a list of cookie files and loads them all into a cookie jar
    if args['cookies']:
        cookie_files = args['cookies'].split(',')
        try:
            args['cookies'] = MozillaCookieJar()
            for cookie_file in cookie_files:
                args['cookies'].load(cookie_file)
        except (LoadError, FileNotFoundError) as e:
            print(e)
            quit()
    else:
        print('--cookies: No file passed')
        quit()

    # set default path
    if not args['output']:
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

    if args['from_file']:
        if not os.path.isfile(args['from_file']):
            print(f"--from-file {args['from_file']}: No file found / Not a file")
            quit()
        with open(args['from_file'],'r') as f:
            links = f.readlines()
        if not links:
            print(f"--from-file {args['from_file']}: File is empty")
            quit()
        args['from_file'] = []
        for link in links:
            # lines starting with '#' are ignored
            if link[0] != '#':
                args['from_file'].append(link.strip().lstrip().split('?')[0])

    if args['favorite_users_updated_within']:
        args['favorite_users_updated_within'] = (datetime.datetime.now() - datetime.timedelta(days=args['favorite_users_updated_within']))
    else:
        args['favorite_users_updated_within'] = datetime.datetime.min

    if args['simulate']:
        args['skip_content'] = True
        args['skip_comments'] = True
        args['skip_attachments'] = True
        args['skip_embed'] = True
        args['skip_json'] = True
        args['save_icon'] = False
        args['save_banner'] = False

    return args