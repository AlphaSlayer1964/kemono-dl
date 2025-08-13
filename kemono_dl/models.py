from dataclasses import asdict, dataclass, fields
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
    server: str | None


@dataclass
class Post:
    id: str
    user: str
    service: str
    title: str
    content: str
    shared_file: bool
    added: str
    published: str
    edited: str
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
        self.added = post.get("added", "")
        self.published = post.get("published", "")
        self.edited = post.get("edited", "")
        self.poll = post.get("poll", None)
        self.embed = post.get("embed", {})

        attachment = None
        field_names = {f.name for f in fields(Attachment)}
        file = post.get("file")
        if file and isinstance(file, dict):
            filtered_data = {k: v for k, v in file.items() if k in field_names}

            attachment = Attachment(
                **filtered_data,
                server=findSeverFromPath(
                    attachments,
                    previews,
                    file.get("path", ""),
                ),
            )

        self.attachments = []
        for a in post.get("attachments", []):
            if a and isinstance(a, dict):
                filtered_data = {k: v for k, v in a.items() if k in field_names}
                self.attachments.append(
                    Attachment(
                        **filtered_data,
                        server=findSeverFromPath(
                            attachments,
                            previews,
                            a.get("path", ""),
                        ),
                    )
                )
        if attachment and attachment not in self.attachments:
            self.attachments.append(attachment)
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
    post_id: str
    post_title: str
    server_filename: str
    server_file_name: str
    server_file_ext: str
    filename: str
    file_name: str
    file_ext: str
    sha256: str

    def __init__(self, creator: Creator, post: Post, attachment: Attachment) -> None:
        self.service = creator.service
        self.creator_id = creator.id
        self.post_id = post.id
        self.post_title = post.title

        self.server_filename = attachment.path.split("/")[-1]
        self.server_file_name, self.server_file_ext = splitext(self.server_filename)
        self.sha256 = self.server_file_name

        self.filename = attachment.name
        self.file_name, self.file_ext = splitext(self.filename)

    def __post_init__(self) -> None:
        for f in fields(self):
            val = getattr(self, f.name)
            setattr(self, f.name, make_path_safe(val))

    def toDict(self) -> dict[str, str]:
        return asdict(self)
