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

    parser.add_argument("--path", type=str, default=os.getcwd(), help="Download directory path")
    parser.add_argument("--output", type=str, action="append", metavar="[Type:]Template", default=[KemonoDL.DEFAULT_OUTPUT_TEMPLATE], help="Post attachments output filename tamplate")
    parser.add_argument("--cookies", type=str, action="append", help="Path(s) to cookies files")
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
    parser.add_argument("--skip-attachments", action="store_true", help="Skip downloading post attachments.")
    parser.add_argument("--write-content", action="store_true", help="Write Post content to an html file.")
    parser.add_argument("URL", nargs="*", help="URL(s) to download")

    return parser.parse_args()


def parse_value_type(s):
    inside_braces = 0
    for i, char in enumerate(s):
        if char == "{":
            inside_braces += 1
        elif char == "}":
            inside_braces = max(inside_braces - 1, 0)
        elif char == ":" and inside_braces == 0:
            return [s[:i], s[i + 1 :]]
    return [None, s]


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
            date_type, date_string = parse_value_type(arg)
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

    output_templates = {
        "attachments": KemonoDL.DEFAULT_OUTPUT_TEMPLATE,
        # "pfp": KemonoDL.DEFAULT_OUTPUT_TEMPLATE,
        # "banner": KemonoDL.DEFAULT_OUTPUT_TEMPLATE,
        "content": KemonoDL.DEFAULT_OUTPUT_TEMPLATE,
        # "json": KemonoDL.DEFAULT_OUTPUT_TEMPLATE,
    }

    if args.output:
        for output in args.output:
            output_type, output_value = parse_value_type(output)
            if output_type not in output_templates and output_type is not None:
                print(f"[Error] Invalid output Type {output_type!r} for {output!r}")
                quit()
            if output_type is None:
                for key in output_templates:
                    output_templates[key] = output_value  # type: ignore
            else:
                output_templates[output_type] = output_value  # type: ignore

    kemono_dl = KemonoDL(
        path=args.path,
        output_templates=output_templates,
        restrict_names=args.restrict_names,
        custom_template_variables=custom_template_variables,
        archive_file=args.archive,
        post_filters=post_filters,
        attachment_filters=attachment_filters,
        skip_attachments=args.skip_attachments,
        write_content=args.write_content,
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

    if args.URL:
        for url in args.URL:
            kemono_dl.download_url(url)

    if args.batch_file and os.path.exists(args.batch_file):
        with open(args.batch_file, "r", encoding="utf-8") as f:
            batch_urls = [line.strip() for line in f.readlines() if not line.startswith("#")]

        for url in batch_urls:
            kemono_dl.download_url(url)

    print("Complete")


if __name__ == "__main__":
    main()
