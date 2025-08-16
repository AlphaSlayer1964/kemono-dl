from dataclasses import asdict, dataclass, fields
from datetime import datetime
from os.path import splitext
from typing import List

from .utils import make_path_safe


@dataclass
class ParsedUrl:
    site: str
    service: str
    creator_id: str
    post_id: str | None = None


@dataclass
class Creator:
    id: str
    name: str
    service: str
    indexed: int
    updated: int
    public_id: str
    relation_id: str | None
    post_count: int | None
    dm_count: int | None
    share_count: int | None
    chat_count: int | None
    has_chats: bool | None = None


@dataclass
class FavoriteCreator:
    id: str
    name: str
    service: str
    indexed: str
    updated: str
    public_id: int | None
    relation_id: int | None
    faved_seq: int
    last_imported: str
    has_chats: bool | None = None


@dataclass
class AttachmentPreviews:
    type: str
    server: str
    name: str
    path: str


@dataclass
class Attachment:
    name: str
    path: str
    index: int
    server: str | None
    count: int = 1


@dataclass
class Post:
    id: str
    user: str
    service: str
    title: str
    content: str
    shared_file: bool
    added: datetime
    published: datetime
    edited: datetime
    poll: bool | None  # no idea what type this is

    embed: dict
    attachments: List[Attachment]
    captions: List[str] | None
    tags: List[str] | None

    def __init__(self, post_api: dict) -> None:
        post = post_api.get("post", {})
        attachments = post_api.get("attachments")
        previews = post_api.get("previews")

        self.id = post.get("id", "")
        self.user = post.get("user", "")
        self.service = post.get("service", "")
        self.title = post.get("title", "")
        self.content = post.get("content", "")
        self.shared_file = post.get("shared_file", False)

        try:
            self.added = datetime.fromisoformat(post.get("added", ""))
        except Exception:
            print(f"[Warning] Invalid isoformat string for `added`: '{post.get('added', '')}' ")
            self.added = datetime.min

        try:
            self.published = datetime.fromisoformat(post.get("published", ""))
        except Exception:
            print(f"[Warning] Invalid isoformat string for `published`: '{post.get('published', '')}' ")
            self.published = datetime.min

        try:
            self.edited = datetime.fromisoformat(post.get("edited", ""))
        except Exception:
            print(f"[Warning] Invalid isoformat string for `edited`: '{post.get('edited', '')}' ")
            self.edited = datetime.min

        self.poll = post.get("poll", None)
        self.embed = post.get("embed", {})

        self.attachments = []

        file = post.get("file")
        if file and file.get("name", False) and file.get("path", False):
            self.attachments.append(
                Attachment(
                    name=file.get("name"),
                    path=file.get("path"),
                    index=len(self.attachments),
                    server=findSeverFromPath(
                        attachments,
                        previews,
                        file.get("path"),
                    ),
                )
            )

        for a in post.get("attachments", []):
            if a and a.get("name", False) and a.get("path", False):
                self.attachments.append(
                    Attachment(
                        name=a.get("name"),
                        path=a.get("path"),
                        index=len(self.attachments),
                        server=findSeverFromPath(
                            attachments,
                            previews,
                            a.get("path"),
                        ),
                    )
                )

        seen_pairs = set()
        name_counts = {}

        for attachment in self.attachments:
            key = (attachment.name, attachment.path)
            if key not in seen_pairs:
                seen_pairs.add(key)
                name_counts[attachment.name] = name_counts.get(attachment.name, 0) + 1
            attachment.count = name_counts[attachment.name]

        self.captions = post.get("captions", None)
        self.tags = post.get("tags", None)


def findSeverFromPath(attachments, previews, path):
    for attachment in attachments:
        if attachment.get("path") == path:
            return attachment.get("server")
    for preview in previews:
        if preview.get("path") == path:
            return preview.get("server")
    return None


@dataclass
class TemplateVaribale:
    service: str
    creator_id: str
    creator_name: str
    post_id: str
    post_title: str
    server_filename: str
    server_file_name: str
    server_file_ext: str
    filename: str
    file_name: str
    file_ext: str
    sha256: str
    index: int
    count: int
    added: datetime
    published: datetime
    edited: datetime

    def __init__(self, creator: Creator, post: Post, attachment: Attachment) -> None:
        self.service = creator.service
        self.creator_id = creator.id
        self.creator_name = creator.name
        self.post_id = post.id
        self.post_title = post.title
        self.index = attachment.index
        self.count = attachment.count
        self.server_filename = attachment.path.split("/")[-1]
        self.server_file_name, self.server_file_ext = splitext(self.server_filename)
        self.sha256 = self.server_file_name

        self.filename = attachment.name
        self.file_name, self.file_ext = splitext(self.filename)

        self.added = post.added
        self.published = post.published
        self.edited = post.edited

        for f in fields(self):
            if f.type is not str:
                continue
            val = getattr(self, f.name)
            setattr(self, f.name, make_path_safe(val))

    def toDict(self) -> dict[str, str]:
        return asdict(self)
