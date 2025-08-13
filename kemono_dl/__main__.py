import argparse
import os

from .kemono_dl import KemonoDL

COOMER_COOKIES = "coomer.st_cookies.txt"
KEMONO_COOKIES = "kemono.cr_cookies.txt"
DOWNLOAD_FAVORITE_CREATORS_COOMER = True
DOWNLOAD_FAVORITE_CREATORS_KEMONO = True
DOWNLOAD_FAVORITE_POSTS_COOMER = False
DOWNLOAD_FAVORITE_POSTS_KEMONO = False


def parse_args():
    parser = argparse.ArgumentParser(description="KemonoDL Downloader")

    parser.add_argument("--path", type=str, default=os.path.join(os.getcwd(), "Downloads"), help="Download directory path")
    parser.add_argument("--output", type=str, default="{service}/{creator_id}/{server_filename}", help="Post attachments output filename tamplate")
    # parser.add_argument("--output-special", type=str, default="{service}/{creator_id}/{type}_{sha256}.{file_ext}", help="Creator profile picture and banner output filename tamplate")
    parser.add_argument("--coomer-cookies", type=str, default="coomer.st_cookies.txt", help="Path to Coomer cookies file")
    parser.add_argument("--kemono-cookies", type=str, default="kemono.cr_cookies.txt", help="Path to Kemono cookies file")
    parser.add_argument("--favorite-creators-coomer", action="store_true", help="Download favorite creators from Coomer")
    parser.add_argument("--favorite-creators-kemono", action="store_true", help="Download favorite creators from Kemono")
    # parser.add_argument("--favorite-posts-coomer", action="store_true", help="Download favorite posts from Coomer")
    # parser.add_argument("--favorite-posts-kemono", action="store_true", help="Download favorite posts from Kemono")
    parser.add_argument("--batch-file", type=str, help="Download URLs from a file")
    parser.add_argument("urls", nargs="*", help="URLs to download")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    kemono_dl = KemonoDL(path=args.path, output_template=args.output)

    if args.favorite_creators_coomer:
        kemono_dl.load_cookies(args.coomer_cookies)

    if args.favorite_creators_kemono:
        kemono_dl.load_cookies(args.kemono_cookies)

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
