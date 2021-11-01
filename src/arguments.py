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

    ap.add_argument("--cookies",
                    required=True,
                    help="File to read cookies from. (REQUIRED)")

    ap.add_argument("-l", "--links",
                    default=[],
                    help="Downloads URLs, can be separated by commas.")

    ap.add_argument("-f", "--fromfile",
                    metavar="FILE", type=str, default=[],
                    help="File containing URLs to download, one URL per line.")

    ap.add_argument("--favorite-users",
                    action='store_true', default=False,
                    help="Downloads all favorite users. (Requires cookies while logged in)")

    ap.add_argument("--favorite-posts",
                    action='store_true', default=False,
                    help="Downloads all favorites posts. (Requires cookies while logged in)")

    ap.add_argument("-o", "--output",
                    metavar="PATH", type=str, default=None,
                    help="Path to download location")

    ap.add_argument("-a", "--archive",
                    metavar="FILE", type=str, default=None,
                    help="Downloads only posts that are not in provided archive file. (Can not be used with --update)")

    ap.add_argument("-u", "--update",
                    action='store_true', default=False,
                    help="Updates already downloaded posts. Post must have json log file. (can not be used with --archive)")

    ap.add_argument("-i", "--ignore-errors",
                    action='store_true', default=False,
                    help="Continue to download posts when an error occurs.")

    ap.add_argument("--yt-dlp",
                    action='store_true', default=False,
                    help="Tries to download embeds with yt-dlp. (experimental)")

    ap.add_argument("--post-timeout",
                    metavar="SEC", type=int, default=0,
                    help="The amount of time in seconds to wait between downloading posts. (default: 0)")

    ap.add_argument("--retry-download",
                    metavar="COUNT", type=int, default=0,
                    help="The amount of times to retry downloading a file. (acts like --ignores-errors) (default: 0)")

    ap.add_argument("--date",
                    metavar="DATE", type=str, default=None,
                    help="Only download posts from this date.")

    ap.add_argument("--datebefore",
                    metavar="DATE", type=str, default=None,
                    help="Only download posts from this date and before.")

    ap.add_argument("--dateafter",
                    metavar="DATE", type=str, default=None,
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
                    help="Skips posts embeds.")

    ap.add_argument("--skip-pfp-banner",
                    action='store_true', default=False,
                    help="Skips user pfp and banner.")

    ap.add_argument("--skip-comments",
                    action='store_true', default=False,
                    help="Skips posts comments.")

    ap.add_argument("--skip-postfile",
                    action='store_true', default=False,
                    help="Skips post file.")

    ap.add_argument("--skip-attachments",
                    action='store_true', default=False,
                    help="Skips attachments.")

    ap.add_argument("--skip-json",
                    action='store_true', default=False,
                    help="Skips json. (--update requires post json)")

    ap.add_argument("--force-external",
                    action='store_true', default=False,
                    help="Save all content links to a file.")

    ap.add_argument("--force-indexing",
                    action='store_true', default=False,
                    help="Attachments and inline images will have indexing numbers added to their file names.")

    ap.add_argument("--force-inline",
                    action='store_true', default=False,
                    help="Download all external inline images found in post content. (experimental)")

    ap.add_argument("--force-yt-dlp",
                    action='store_true', default=False,
                    help="Tries to download content links with yt-dlp. (experimental)")

    args = vars(ap.parse_args())

    if args['version']:
        print(__version__)
        quit()

    if args['update'] and args['archive']:
        print('[Error] Only use one: --archive or --update')
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
            print('[Error] Archive directory does not exist: {}'.format(archive_path))
            quit()

    if args['only_filetypes'] and args['skip_filetypes']:
        print('[Error] Only use one: --only-filetypes or --skip-filetypes')
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
            print("[Error] Incorrect format: {} {}".format(arg, date))
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
            print("[Error] Incorrect format: {} {}".format(arg, size))
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