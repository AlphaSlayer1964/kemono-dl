import argparse
import json
import os
from datetime import datetime

from .kemono_dl import KemonoDL
from .version import __version__

COOMER_COOKIES = "coomer.st_cookies.txt"
KEMONO_COOKIES = "kemono.cr_cookies.txt"
DOWNLOAD_FAVORITE_CREATORS_COOMER = True
DOWNLOAD_FAVORITE_CREATORS_KEMONO = True
DOWNLOAD_FAVORITE_POSTS_COOMER = False
DOWNLOAD_FAVORITE_POSTS_KEMONO = False


def parse_args():
    parser = argparse.ArgumentParser(description="KemonoDL Downloader")

    parser.add_argument("--path", type=str, default=os.path.join(os.getcwd(), "Downloads"), help="Download directory path")
    parser.add_argument("--output", type=str, default="{service}/{creator_id}/{post_id}/{filename}", help="Post attachments output filename tamplate")
    # parser.add_argument("--output-special", type=str, default="{service}/{creator_id}/{type}_{sha256}.{file_ext}", help="Creator profile picture and banner output filename tamplate")
    parser.add_argument("--cookies", type=str, nargs="+", help="Path(s) to cookies files")
    parser.add_argument("--favorite-creators-coomer", action="store_true", help="Download favorite creators from Coomer")
    parser.add_argument("--favorite-creators-kemono", action="store_true", help="Download favorite creators from Kemono")
    # parser.add_argument("--favorite-posts-coomer", action="store_true", help="Download favorite posts from Coomer")
    # parser.add_argument("--favorite-posts-kemono", action="store_true", help="Download favorite posts from Kemono")
    parser.add_argument("--batch-file", type=str, help="Download URLs from a file")
    parser.add_argument("--restrict-names", action="store_true", help="Restrict output file to ASCII characters.")
    parser.add_argument("--version", action="store_true", help="Print program version and exit")
    parser.add_argument("--coomer-login", nargs=2, metavar=("USERNAME", "PASSWORD"), help="Login for Coomer")
    parser.add_argument("--kemono-login", nargs=2, metavar=("USERNAME", "PASSWORD"), help="Login for Kemono")
    parser.add_argument("--custom-template-variables", type=str, help="Path to a json file with your custom template variables")
    parser.add_argument("--archive", metavar="FILE", type=str, help="Path to archive file containing a list of post urls")
    parser.add_argument("--date", metavar="[Type:]DATE", type=str, help="Download only posts uploaded on this date. Format 'YYYYMMDD'")
    parser.add_argument("--datebefore", metavar="[Type:]DATE", type=str, help="Download only videos uploaded on or before this date. Format 'YYYYMMDD'")
    parser.add_argument("--dateafter", metavar="[Type:]DATE", type=str, help="Download only videos uploaded on or after this date. Format 'YYYYMMDD'")
    parser.add_argument("--skip-extensions", metavar="EXTs", type=str, help="A comma seperated list of file extensions to skip (Do not include the period) (Checks the extention of the filename not the server filename).")
    parser.add_argument("urls", nargs="*", help="URLs to download")

    return parser.parse_args()


def parse_date_string(s):
    parts = s.split(":", 1)
    return parts if len(parts) == 2 else (None, parts[0])


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def main() -> None:
    args = parse_args()

    if args.version:
        print(__version__)
        quit()

    custom_template_variables = {}
    if args.custom_template_variables:
        with open(args.custom_template_variables, "r", encoding="utf-8") as f:
            custom_template_variables = json.load(f)

    post_filters = {
        "date": {"added": None, "edited": None, "published": None},
        "datebefore": {"added": None, "edited": None, "published": None},
        "dateafter": {"added": None, "edited": None, "published": None},
    }

    for arg, filter in [
        (args.date, post_filters["date"]),
        (args.datebefore, post_filters["datebefore"]),
        (args.dateafter, post_filters["dateafter"]),
    ]:
        if arg:
            date_type, date_string = parse_date_string(arg)
            if date_type not in filter and date_type is not None:
                print(f"[Error] Invalid date filter: {arg!r}")
                quit()
            try:
                if date_type is None:
                    filter["published"] = datetime.strptime(date_string, "%Y%m%d")  # type: ignore
                else:
                    filter[date_type] = datetime.strptime(date_string, "%Y%m%d")  # type: ignore
            except ValueError:
                print(f"[Error] Invalid date format. {date_string!r} does not match '%Y%m%d'")
                quit()

    attachment_filters = {
        "skip_extensions": [],
    }

    if args.skip_extensions:
        attachment_filters["skip_extensions"] = [ext.strip() for ext in args.skip_extensions.split(",")]

    kemono_dl = KemonoDL(
        path=args.path,
        output_template=args.output,
        restrict_names=args.restrict_names,
        custom_template_variables=custom_template_variables,
        archive_file=args.archive,
        post_filters=post_filters,
        attachment_filters=attachment_filters,
    )

    if args.cookies:
        for cookie_file in args.cookies:
            kemono_dl.load_cookies(cookie_file)

    if args.coomer_login:
        kemono_dl.login(KemonoDL.COOMER_DOMAIN, args.coomer_login[0], args.coomer_login[1])
        print(kemono_dl.isLoggedin(KemonoDL.COOMER_DOMAIN))

    if args.kemono_login:
        kemono_dl.login(KemonoDL.KEMONO_DOMAIN, args.kemono_login[0], args.kemono_login[1])
        print(kemono_dl.isLoggedin(KemonoDL.KEMONO_DOMAIN))

    if args.favorite_creators_coomer:
        kemono_dl.download_favorite_creators(KemonoDL.COOMER_DOMAIN)

    if args.favorite_creators_kemono:
        kemono_dl.download_favorite_creators(KemonoDL.KEMONO_DOMAIN)

    if args.urls:
        for url in args.urls:
            kemono_dl.download_url(url)

    if args.batch_file and os.path.exists(args.batch_file):
        with open(args.batch_file, "r", encoding="utf-8") as f:
            batch_urls = [line.strip() for line in f.readlines() if not line.startswith("#")]

        for url in batch_urls:
            kemono_dl.download_url(url)

    print("Complete")


if __name__ == "__main__":
    main()
