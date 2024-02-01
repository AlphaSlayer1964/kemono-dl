import os
import datetime
import re
import argparse
from http.cookiejar import MozillaCookieJar, LoadError

from .version import __version__

def get_args():

    ap = argparse.ArgumentParser()

    ap.add_argument("--cookies",
                    metavar="FILE", type=str, default=None, required=True,
                    help="Takes in a cookie file or a list of cookie files separated by a comma. Used to get around the DDOS protection. Your cookie file must have been gotten while logged in to use the favorite options.")



    ap.add_argument("--links",
                    metavar="LINKS", type=str, default=None,
                    help="Takes in a url or list of urls separated by a comma.")

    ap.add_argument("--from-file",
                    metavar="FILE", type=str, default=None,
                    help="Reads in a file with urls separated by new lines. Lines starting with # will not be read in.")

    ap.add_argument("--kemono-fav-users",
                    metavar="SERVICE", type=str, default=None,
                    help="Downloads favorite users from kemono.su of specified type or types separated by a comma. Types include: all, patreon, fanbox, gumroad, subscribestar, dlsite, fantia. Your cookie file must have been gotten while logged in to work.")

    ap.add_argument("--coomer-fav-users",
                    metavar="SERVICE", type=str, default=None,
                    help="Downloads favorite users from coomer.su of specified type or types separated by a comma. Types include: all, onlyfans. Your cookie file must have been gotten while logged in to work.")

    ap.add_argument("--kemono-fav-posts",
                    action='store_true', default=False,
                    help="Downloads favorite posts from kemono.su. Your cookie file must have been gotten while logged in to work.")

    ap.add_argument("--coomer-fav-posts",
                    action='store_true', default=False,
                    help="Downloads favorite posts from coomer.su. Your cookie file must have been gotten while logged in to work.")



    ap.add_argument("--inline",
                    action='store_true', default=False,
                    help="Download the inline images from the post content.")

    ap.add_argument("--content",
                    action='store_true', default=False,
                    help="Write the post content to a html file. The html file includes comments if `--comments` is passed.")

    ap.add_argument("--comments",
                    action='store_true', default=False,
                    help="Write the post comments to a html file.")

    ap.add_argument("--json",
                    action='store_true', default=False,
                    help="Write the post json to a file.")

    ap.add_argument("--extract-links",
                    action='store_true', default=False,
                    help="Write extracted links from post content to a text file.")

    ap.add_argument("--dms",
                    action='store_true', default=False,
                    help="Write user dms to a html file. Only works when a user url is passed.")

    ap.add_argument("--icon",
                    action='store_true', default=False,
                    help="Download the users profile icon. Only works when a user url is passed.")

    ap.add_argument("--banner",
                    action='store_true', default=False,
                    help="Download the users profile banner. Only works when a user url is passed.")

    ap.add_argument("--yt-dlp",
                    action='store_true', default=False,
                    help="Try to download the post embed with yt-dlp.")

    ap.add_argument("--skip-attachments",
                    action='store_true', default=False,
                    help="Do not download post attachments.")

    ap.add_argument("--overwrite",
                    action='store_true', default=False,
                    help="Overwrite any previously created files.")



    ap.add_argument("--dirname-pattern",
                    metavar="DIRNAME_PATTERN", type=str, default='Downloads\{service}\{username} [{user_id}]',
                    help="Set the file path pattern for where files are downloaded. See Output Patterns for more detail.")

    ap.add_argument("--filename-pattern",
                    metavar="FILENAME_PATTERN", type=str, default='[{published}] [{id}] {title}\{index}_{filename}.{ext}',
                    help="Set the file name pattern for attachments. See Output Patterns for more detail.")

    ap.add_argument("--inline-filename-pattern",
                    metavar="INLINE_FILENAME_PATTERN", type=str, default='[{published}] [{id}] {title}\inline\{index}_{filename}.{ext}',
                    help="Set the file name pattern for inline images. See Output Patterns for more detail.")

    ap.add_argument("--other-filename-pattern",
                    metavar="OTHER_FILENAME_PATTERN", type=str, default='[{published}] [{id}] {title}\[{id}]_{filename}.{ext}',
                    help="Set the file name pattern for post content, extracted links, and json. See Output Patterns for more detail.")

    ap.add_argument("--user-filename-pattern",
                    metavar="USER_FILENAME_PATTERN", type=str, default='[{user_id}]_{filename}.{ext}',
                    help="Set the file name pattern for icon, banner and dms. See Output Patterns for more detail.")

    ap.add_argument("--date-strf-pattern",
                    metavar="DATE_STRF_PATTERN", type=str, default='%Y%m%d',
                    help="Set the date strf pattern variable. See Output Patterns for more detail.")

    ap.add_argument("--restrict-names",
                    action='store_true', default=False,
                    help='Set all file and folder names to be limited to only the ascii character set.')



    ap.add_argument("--archive",
                    metavar="FILE", type=str, default=None,
                    help="Only download posts that are not recorded in the archive file.")

    ap.add_argument("--date",
                    metavar="YYYYMMDD", type=str, default=None,
                    help="Only download posts published from this date.")

    ap.add_argument("--datebefore",
                    metavar="YYYYMMDD", type=str, default=None,
                    help="Only download posts published before this date.")

    ap.add_argument("--dateafter",
                    metavar="YYYYMMDD", type=str, default=None,
                    help="Only download posts published after this date.")

    ap.add_argument("--user-updated-datebefore",
                    metavar="YYYYMMDD", type=str, default=None,
                    help="Only download user posts if the user was updated before this date.")

    ap.add_argument("--user-updated-dateafter",
                    metavar="YYYYMMDD", type=str, default=None,
                    help="Only download user posts if the user was updated after this date.")

    ap.add_argument("--min-filesize",
                    metavar="SIZE", type=str, default=None,
                    help="Only download attachments or inline images with greater than this file size. (ex #gb | #mb | #kb | #b)")

    ap.add_argument("--max-filesize",
                    metavar="SIZE", type=str, default=None,
                    help="Only download attachments or inline images with less than this file size. (ex #gb | #mb | #kb | #b)")

    ap.add_argument("--only-filetypes",
                    metavar="EXT", type=str, default=[],
                    help="Only download attachments or inline images with the given file type(s). Takes a file extensions or list of file extensions separated by a comma. (ex mp4,jpg,gif,zip)")

    ap.add_argument("--skip-filetypes",
                    metavar="EXT", type=str, default=[],
                    help="Only download attachments or inline images without the given file type(s). Takes a file extensions or list of file extensions separated by a comma. (ex mp4,jpg,gif,zip)")



    ap.add_argument("--version",
                    action='version', version=str(__version__),
                    help="Print the version and exit.")

    ap.add_argument("--verbose",
                    action='store_true', default=False,
                    help="Display debug information and copies output to a file.")

    ap.add_argument("--quiet",
                    action='store_true', default=False,
                    help="Suppress printing except for warnings, errors, and exceptions.")

    ap.add_argument("--simulate",
                    action='store_true', default=False,
                    help="Simulate the given command and do not write to disk.")

    ap.add_argument("--no-part-files",
                    action='store_true', default=False,
                    help="Do not save attachments or inline images as .part files while downloading. Files partially downloaded will not be resumed if program stops. ")

    ap.add_argument("--yt-dlp-args",
                    metavar="YT_DLP_ARGS", type=str, default=None,
                    help="The args yt-dlp will use to download with. Formatted as a python dictionary object. ")

    ap.add_argument("--post-timeout",
                    metavar="SEC", type=int, default=0,
                    help="The time in seconds to wait between downloading posts. (default: 0)")

    ap.add_argument("--retry",
                    metavar="COUNT", type=int, default=5,
                    help="The amount of times to retry / resume downloading a file. (default: 5)")

    ap.add_argument("--ratelimit-sleep",
                    metavar="SEC", type=int, default=120,
                    help="The time in seconds to wait after being ratelimited (default: 120)")

    ap.add_argument("--user-agent",
                    metavar="UA", type=str, default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
                    help="Set a custom user agent")

    args = vars(ap.parse_args())

    # takes a comma seperated lost of cookie files and loads them into a cookie jar
    if args['cookies']:
        cookie_files = [s.strip() for s in args["cookies"].split(",")]
        args['cookies'] = MozillaCookieJar()
        loaded = 0
        for cookie_file in cookie_files:
            try:
                args['cookies'].load(cookie_file)
                loaded += 1
            except LoadError:
                print(F"Unable to load cookie {cookie_file}")
            except FileNotFoundError:
                print(F"Unable to find cookie {cookie_file}")
        if loaded == 0:
            print("No cookies loaded | exiting"), exit()

    # takes a comma seperated string of links and converts them to a list
    if args['links']:
        args['links'] = [s.strip().split('?')[0] for s in args["links"].split(",")]
    else:
        args['links'] = []

    # takes a file and converts it to a list
    if args['from_file']:
        if not os.path.exists(args['from_file']):
            print(f"--from-file {args['from_file']} does not exist")
        with open(args['from_file'],'r') as f:
            # lines starting with '#' are ignored
            args['from_file'] = [line.rstrip().split('?')[0] for line in f if line[0] != '#' and line.strip() != '']
    else:
        args['from_file'] = []

    if args['archive']:
        # the archive file doesn't need to exist but the directory does
        if not os.path.isdir(os.path.dirname(os.path.abspath(args['archive']))):
            print(f"--archive {args['archive']} directory does not exist"), quit()

    if args['only_filetypes'] and args['skip_filetypes']:
        print('--only-filetypes and --skip-filetypes can not be given together'), quit()
    # takes a comma seperated string of extentions and converts them to a list
    if args['only_filetypes']:
        args['only_filetypes'] = [s.strip().lower() for s in args["only_filetypes"].split(",")]
    # takes a comma seperated string of extentions and converts them to a list
    if args['skip_filetypes']:
        args['skip_filetypes'] = [s.strip().lower() for s in args["skip_filetypes"].split(",")]

    def check_date(args, key):
        try:
            args[key] = datetime.datetime.strptime(args[key], r'%Y%m%d')
        except:
            print(f"--{key} {args[key]} is an invalid date | correct format: YYYYMMDD"), exit()

    if args['date']:
        check_date(args, 'date')
    if args['datebefore']:
        check_date(args, 'datebefore')
    if args['dateafter']:
        check_date(args, 'dateafter')
    if args['user_updated_datebefore']:
        check_date(args, 'user_updated_datebefore')
    if args['user_updated_dateafter']:
        check_date(args, 'user_updated_dateafter')

    def check_size(args, key):
        found = re.search(r'([0-9]+)(gb|mb|kb|b)', args[key].lower())
        if found:
            if found.group(2) == 'b':
                args[key] = int(found.group(1))
            elif found.group(2) == 'kb':
                args[key] = int(found.group(1)) * 10**2
            elif found.group(2) == 'mb':
                args[key] = int(found.group(1)) * 10**6
            elif found.group(2) == 'gb':
                args[key] = int(found.group(1)) * 10**9
            return
        print(f"--{key} {args[key]} is an invalid size | correct format: ex 1b 1kb 1mb 1gb"), quit()

    if args['max_filesize']:
        check_size(args, 'max_filesize')
    if args['min_filesize']:
        check_size(args, 'min_filesize')

    if args['kemono_fav_users']:
        temp = []
        for s in args["kemono_fav_users"].split(","):
            if s.strip().lower() in {'all', 'patreon', 'fanbox', 'gumroad', 'subscribestar', 'dlsite', 'fantia'}:
                temp.append(s.strip().lower())
            else:
                print(f"--kemono-fav-users {s.strip()} is not a valid option")
        if len(temp) == 0:
            print(f"--kemono-fav-users no valid options were passed")
        args['kemono_fav_users'] = temp

    if args['coomer_fav_users']:
        temp = []
        for s in args["coomer_fav_users"].split(","):
            if s.strip().lower() in {'all', 'onlyfans'}:
                temp.append(s.strip().lower())
            else:
                print(f"--coomer-fav-users {s.strip()} is not a valid option")
        if len(temp) == 0:
            print(f"--coomer-fav-users no valid options were passed")
        args['coomer_fav_users'] = temp

    return args