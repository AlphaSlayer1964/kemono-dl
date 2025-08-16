import http.cookiejar
import mimetypes
import os
import re
import time
from http.cookiejar import LoadError
from typing import List, Literal

from requests.exceptions import RequestException

from .downloader import download_file
from .models import Creator, FavoriteCreator, ParsedUrl, Post, TemplateVaribale
from .session import CustomSession
from .utils import generate_file_path, get_sha256_hash, get_sha256_url_content, make_path_safe

OverwriteMode = Literal[False, "soft", True]
# "soft" will not overwrite the file if it has the expected sha256 hash
# NOTE: if two attachments have the same name (and in the same directory) but different sha256 hashes it will overwirte the first file with the second


class KemonoDL:
    COOMER_DOMAIN = "https://coomer.st"
    KEMONO_DOMAIN = "https://kemono.cr"
    POST_STEP_SIZE = 50
    URL_PARSE_PATTERN = r"^https://(kemono|coomer)\.\w+/([^/]+)/user/([^/]+)(?:/post/([^/]+))?$"

    def __init__(
        self,
        path: str = os.getcwd(),
        output_template: str = "{service}/{creator_id}/{server_filename}",
        output_template_special: str = "{service}/{creator_id}/{type}_{sha256}.{file_ext}",
        restrict_names: bool = False,
        custom_template_variables: dict = {},
        force_overwrite: OverwriteMode = "soft",
        max_retries: int = 3,
    ) -> None:
        self.domain = KemonoDL.COOMER_DOMAIN
        self.session = CustomSession()
        self.creators_cache: dict[tuple[str, str], Creator] = {}
        self.path = path
        self.output_template = output_template
        self.output_template_special = output_template_special
        self.restrict_names = restrict_names
        self.custom_template_variables = custom_template_variables
        self.force_overwrite = force_overwrite
        self.max_retries = max_retries

    def parse_url(self, url) -> ParsedUrl | None:
        match = re.match(KemonoDL.URL_PARSE_PATTERN, url)
        if match:
            site, service, creator_id, post_id = match.groups()
            return ParsedUrl(site, service, creator_id, post_id)
        return None

    def load_cookies(self, cookies_file: str) -> bool:
        try:
            jar = http.cookiejar.MozillaCookieJar()
            jar.load(cookies_file)
            for cookie in jar:
                self.session.cookies.set_cookie(cookie)
            return True
        except (LoadError, OSError) as e:
            print(f"[Error] Failed to load cookies from {cookies_file}: {e}")
            return False

    def login(self, domain: str, username: str, password: str) -> bool:
        try:
            url = f"{domain}/api/v1/authentication/login"
            response = self.session.post(url, json={"username": username, "password": password})
            response.raise_for_status()
            return True
        except RequestException as e:
            print(f"[Error] Unable to login: {e}")
            return False

    def isLoggedin(self, domain: str) -> bool:
        url = f"{domain}/api/v1/account"
        response = self.session.get(url, headers={"accept": "text/css"})
        return response.ok

    def get_creator_profile(self, domain: str, service: str, creator_id: str) -> Creator | None:
        try:
            creator = self.creators_cache.get((service, creator_id), None)
            if creator is None:
                url = f"{domain}/api/v1/{service}/user/{creator_id}/profile"
                response = self.session.get(url, headers={"accept": "text/css"})
                response.raise_for_status()
                creator = Creator(**response.json())
                self.creators_cache[(service, creator_id)] = creator
            return creator
        except (RequestException, ValueError) as e:
            print(f"[Error] Failed to fetch creator profile from {url!r}: {e}")
            return None

    def get_creator_post_ids(self, domain: str, service: str, creator_id: str, offset: int = 0) -> list[str]:
        try:
            url = f"{domain}/api/v1/{service}/user/{creator_id}/posts"
            response = self.session.get(url, params={"o": offset}, headers={"accept": "text/css"})
            response.raise_for_status()
            posts = response.json()
            return [post.get("id") for post in posts]
        except (RequestException, ValueError) as e:
            print(f"[Error] Failed to fetch posts from {url!r}: {e}")
            return []

    def get_all_creator_post_ids(self, domain: str, service: str, creator_id: str, limit: int = 0, offset: int = 0) -> list[str]:
        posts = []
        while True:
            posts_chunk = self.get_creator_post_ids(domain, service, creator_id, offset)
            posts += posts_chunk
            if len(posts) >= limit and limit > 0:
                posts = posts[:limit]
                break
            if len(posts_chunk) < KemonoDL.POST_STEP_SIZE:
                break
            offset += KemonoDL.POST_STEP_SIZE
            time.sleep(0.5)
        return posts

    def get_post(self, domain: str, service: str, creator_id: str, post_id: str) -> Post | None:
        try:
            url = f"{domain}/api/v1/{service}/user/{creator_id}/post/{post_id}"
            response = self.session.get(url, headers={"accept": "text/css"})
            response.raise_for_status()
            post_api = response.json()
            return Post(post_api)
        except (RequestException, ValueError) as e:
            print(f"[Error] Failed to fetch post from {url!r}: {e}")
            return None

    def get_favorit_creators(self, domain: str) -> List[FavoriteCreator] | None:
        try:
            url = f"{domain}/api/v1/account/favorites"
            response = self.session.get(url, params={"type": "artist"}, headers={"accept": "text/css"})
            response.raise_for_status()
            creators = response.json()
            return [FavoriteCreator(**creator) for creator in creators]
        except (RequestException, ValueError) as e:
            print(f"[Error] Failed to fetch favorite creators from {url!r}: {e}")
            return None

    def get_favorit_post_ids(self, domain: str) -> List[str] | None:
        try:
            url = f"{domain}/api/v1/account/favorites"
            response = self.session.get(url, params={"type": "post"}, headers={"accept": "text/css"})
            response.raise_for_status()
            posts = response.json()
            return [post.get("id") for post in posts]
        except (RequestException, ValueError) as e:
            print(f"[Error] Failed to fetch favorite posts from {url!r}: {e}")
            return None

    def download_favorite_creators(self, domain: str) -> None:
        if not self.isLoggedin(domain):
            print(f"[Error] You are not logged into {domain!r}")
            return

        creators = self.get_favorit_creators(domain)

        if creators is None:
            return

        for creator in creators:
            post_ids = self.get_all_creator_post_ids(domain, creator.service, creator.id)
            for post_id in post_ids:
                time.sleep(0.5)
                post = self.get_post(domain, creator.service, creator.id, post_id)
                if post:
                    self.download_post(domain, post)

    def download_favorite_posts(self, domain: str):
        pass

    def download_url(self, url: str) -> None:
        parsed_url = self.parse_url(url)

        if parsed_url is None:
            print("Invalid URL:" + url)
            return

        domain = KemonoDL.KEMONO_DOMAIN if parsed_url.site == "kemono" else KemonoDL.COOMER_DOMAIN
        if parsed_url.post_id:
            post = self.get_post(domain, parsed_url.service, parsed_url.creator_id, parsed_url.post_id)
            if post:
                self.download_post(domain, post)
        else:
            post_ids = self.get_all_creator_post_ids(domain, parsed_url.service, parsed_url.creator_id)
            for post_id in post_ids:
                time.sleep(0.5)
                post = self.get_post(domain, parsed_url.service, parsed_url.creator_id, post_id)
                if post:
                    self.download_post(domain, post)

    def download_creator_banner(self, domain: str, service: str, creator_id: str) -> None:
        self._download_special(domain, service, creator_id, "banner")

    def download_creator_icon(self, domain: str, service: str, creator_id: str) -> None:
        self._download_special(domain, service, creator_id, "icon")

    def _download_special(self, domain: str, service: str, creator_id: str, type: str) -> None:
        creator = self.get_creator_profile(domain, service, creator_id)
        if creator is None:
            return
        url = self.domain + f"{type}s/{service}/{creator_id}"
        response = self.session.head(url, allow_redirects=True)
        contentType = response.headers.get("Content-Type", "")
        ext = (mimetypes.guess_extension(contentType) or ".bin")[1:]

        sha256 = get_sha256_url_content(self.session, url) if "{sha256}" in self.output_template_special else ""

        file_path = generate_file_path(
            self.path,
            self.output_template_special,
            {
                "service": creator.service,
                "creator_id": creator.id,
                "filename": creator_id + "." + ext,
                "file_name": creator_id,
                "file_ext": ext,
                "type": type,
                "sha256": sha256,
            },
            self.restrict_names,
        )

        download_file(
            session=self.session,
            url=url,
            filepath=file_path,
        )

    def download_post(self, domain: str, post: Post) -> None:
        print(f"[downloading] Post: {make_path_safe(post.title)[:100]}")
        self.download_post_attachments(domain, post)

    def download_post_attachments(self, domain: str, post: Post) -> None:
        if not post.attachments:
            return

        creator = self.get_creator_profile(domain, post.service, post.user)
        if creator is None:
            return

        print(f"[downloading] Attachments: {len(post.attachments)}")

        for attachment in post.attachments:
            template_variables = TemplateVaribale(creator, post, attachment)

            template_variables_dict = template_variables.toDict()
            for key, value in self.custom_template_variables.items():
                if key in template_variables_dict:
                    print(f"[Warning] Custom variable key {key!r} conflicts with default variable keys. Skipping.")
                    continue
                template_variables_dict[key] = eval(value.format(**template_variables_dict))

            file_path = generate_file_path(
                self.path,
                self.output_template,
                template_variables_dict,
                self.restrict_names,
            )
            expected_sha256 = template_variables.sha256

            if os.path.exists(file_path):
                actual_sha256 = get_sha256_hash(file_path)

                if self.force_overwrite is False:
                    print(f"[info] File already exists at {file_path}")
                    if expected_sha256 != actual_sha256:
                        print(f'[warning] File sha256 mismatch. Expected "{expected_sha256}" recieved"{actual_sha256}"')
                    continue

                elif self.force_overwrite == "soft" and expected_sha256 == actual_sha256:
                    print(f"[info] File already exists with matching sha256 at {file_path}")
                    continue

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            url = f"{attachment.server}/data{attachment.path}"

            for attempt in range(self.max_retries):
                try:
                    download_file(self.session, url, file_path)
                    break
                except Exception as e:
                    print(f"[Error] Failed to download attachment from {url!r}: {e}")
            else:
                print(f"[Error] All {self.max_retries} download reties failed")
                return

            actual_sha256 = get_sha256_hash(file_path)
            if expected_sha256 != actual_sha256:
                print(f"[Error] File downloaded with incorrect SHA-256. Expected: {expected_sha256} Actual: {actual_sha256}")
