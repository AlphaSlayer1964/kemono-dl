import sqlite3
from typing import List

from models import Attachment, Post


class KemonoDB:
    def __init__(self, db_name="test.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                user TEXT,
                service TEXT,
                title TEXT,
                content TEXT,
                shared_file INTEGER,
                added TEXT,
                published TEXT,
                edited TEXT,
                poll INTEGER)
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            path TEXT,
            UNIQUE(name, path))
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_attachments (
            post_id TEXT,
            attachment_id INTEGER,
            FOREIGN KEY(post_id) REFERENCES posts(id),
            FOREIGN KEY(attachment_id) REFERENCES attachments(id),
            PRIMARY KEY (post_id, attachment_id))
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS captions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE)
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_captions (
            post_id TEXT,
            caption_id INTEGER,
            FOREIGN KEY(post_id) REFERENCES posts(id),
            FOREIGN KEY(caption_id) REFERENCES captions(id),
            PRIMARY KEY (post_id, caption_id))
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE)
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_tags(
            post_id TEXT,
            tag_id INTEGER,
            FOREIGN KEY(post_id) REFERENCES posts(id),
            FOREIGN KEY(tag_id) REFERENCES tags(id),
            PRIMARY KEY (post_id, tag_id))
        """)

        self.conn.commit()

    def insert_post(self, post: Post):
        serializedData = post.serializeForDb()

        self.cursor.execute(
            """
        INSERT OR IGNORE INTO posts (id, user, service, title, content, shared_file, added, published, edited, poll)
        VALUES (:id, :user, :service, :title, :content, :shared_file, :added, :published, :edited, :poll)
        """,
            serializedData["post"],
        )
        self.conn.commit()

        post_id = serializedData["post"]["id"]
        self.add_tags_for_post(post_id, serializedData["tags"])
        self.add_captions_for_post(post_id, serializedData["captions"])
        self.add_attachments_for_post(post_id, serializedData["attachments"])

    def add_tags_for_post(self, post_id, tag_names):
        tag_ids = []

        for name in tag_names or []:
            # Insert tag if it doesn't exist
            self.cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
            self.cursor.execute("SELECT id FROM tags WHERE name = ?", (name,))
            tag_id = self.cursor.fetchone()[0]
            tag_ids.append(tag_id)

        # Link post to each tag
        for tag_id in tag_ids:
            self.cursor.execute(
                "INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)",
                (post_id, tag_id),
            )

        self.conn.commit()

    def add_captions_for_post(self, post_id, caption_names):
        caption_ids = []

        for name in caption_names or []:
            # Insert tag if it doesn't exist
            self.cursor.execute("INSERT OR IGNORE INTO captions (name) VALUES (?)", (name,))
            self.cursor.execute("SELECT id FROM captions WHERE name = ?", (name,))
            caption_id = self.cursor.fetchone()[0]
            caption_ids.append(caption_id)

        # Link post to each tag
        for caption_id in caption_ids:
            self.cursor.execute(
                "INSERT OR IGNORE INTO post_captions (post_id, caption_id) VALUES (?, ?)",
                (post_id, caption_id),
            )

        self.conn.commit()

    def add_attachments_for_post(self, post_id, attachments: List[dict]):
        attachment_ids = []

        for attachment in attachments or []:
            name = attachment["name"]
            path = attachment["path"]
            # Insert tag if it doesn't exist
            self.cursor.execute(
                "INSERT OR IGNORE INTO attachments (name, path) VALUES (?, ?)",
                (name, path),
            )
            self.cursor.execute("SELECT id FROM attachments WHERE name = ? AND path = ?", (name, path))
            attachment_id = self.cursor.fetchone()[0]
            attachment_ids.append(attachment_id)

        # Link post to each tag
        for attachment_id in attachment_ids:
            self.cursor.execute(
                "INSERT OR IGNORE INTO post_attachments (post_id, attachment_id) VALUES (?, ?)",
                (post_id, attachment_id),
            )

        self.conn.commit()
