from dataclasses import asdict, dataclass
from datetime import datetime
from os.path import splitext
from typing import List


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
class Attachment:
    name: str
    path: str
    index: int = 0
    server: str | None = None


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
class FileTemplateVaribales:
    service: str
    creator_id: str
    creator_name: str
    post_id: str
    post_title: str
    attachments_count: int
    added: datetime
    published: datetime
    edited: datetime

    server_filename: str
    server_file_name: str
    server_file_ext: str
    filename: str
    file_name: str
    file_ext: str
    sha256: str
    index: int

    def __init__(self, creator: Creator, post: Post, attachment: Attachment) -> None:
        server_filename = attachment.path.split("/")[-1]
        server_file_name, server_file_ext = splitext(server_filename)
        sha256 = server_file_name
        filename = attachment.name
        file_name, file_ext = splitext(filename)
        index = attachment.index

        self.service = creator.service
        self.creator_id = creator.id
        self.creator_name = creator.name
        self.post_id = post.id
        self.post_title = post.title
        self.added = post.added
        self.published = post.published
        self.edited = post.edited
        self.attachments_count = len(post.attachments)

        self.server_filename = server_filename
        self.server_file_name = server_file_name
        self.server_file_ext = server_file_ext
        self.filename = filename
        self.file_name = file_name
        self.file_ext = file_ext
        self.sha256 = sha256
        self.index = index

    def toDict(self, custom_variables: dict | None = None) -> dict[str, str]:
        template_variables_dict = asdict(self)

        if custom_variables:
            for key, value in custom_variables.items():
                template_variables_dict[key] = eval(value.format(**template_variables_dict))

        return template_variables_dict
