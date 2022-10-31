from __future__ import annotations

from datetime import datetime
from xml.dom.minidom import Document, parseString

from dateutil.parser import parse as dt_parse
from bs4 import BeautifulSoup

from entities import ShortenedURL, UserMention, Entity, Media


class Tweet:
    def __init__(self, d: dict):
        self.dict: dict = d["tweet"]
        self.id: int = int(self.dict['id'])
        self.timestamp: datetime = self._parse_time(self.dict['created_at'])
        self.source: str = self._parse_source(self.dict['source'])
        self.favourites: int = int(self.dict['favorite_count'])
        self.retweets: int = int(self.dict['retweet_count'])
        self.full_text_unrepaired: str = self.dict['full_text']

        # Reply
        self.reply_to_id: int | None
        self.reply_to_username: str | None
        self.reply_to_userid: int | None
        try:
            self.reply_to_tweet_id = int(self.dict['in_reply_to_status_id'])
            self.reply_to_username = self.dict["in_reply_to_screen_name"]
            self.reply_to_userid = int(self.dict["in_reply_to_user_id_str"])
        except KeyError:
            self.reply_to_tweet_id = None
            self.reply_to_username = None
            self.reply_to_userid = None

        # Entitles
        # URLs
        self.shortened_urls: list[ShortenedURL]
        try:
            self.shortened_urls = [ShortenedURL(url) for url in self.dict["entities"]["urls"]]
        except KeyError:
            self.shortened_urls = []
        # Mentions
        self.user_mentions: list[UserMention]
        try:
            self.user_mentions = [UserMention(mention) for mention in self.dict["entities"]["user_mentions"]]
        except KeyError:
            self.user_mentions = []
        # Media
        self.media: list[Media]
        try:
            self.media = [Media(image, parent_tweet_id=self.id) for image in self.dict["entities"]["media"]]
        except KeyError:
            self.media = []

    @property
    def text_entities(self) -> list[Entity]:
        return sorted(
            self.shortened_urls
            + self.user_mentions,
            key=lambda e: e.indices[0]
        )

    @property
    def is_reply(self) -> bool:
        return self.reply_to_tweet_id is not None

    @property
    def is_retweet(self) -> bool:
        return self.full_text_unrepaired.startswith("RT @")

    @property
    def is_quotetweet(self) -> bool:
        # Quotetweets end with a twitter url
        if len(self.shortened_urls) == 0:
            return False
        last_url: ShortenedURL = self.shortened_urls[-1]
        if last_url.indices[1] != len(self.full_text_unrepaired):
            return False
        return last_url.url.startswith("https://twitter.com/")

    @property
    def full_text_repaired(self) -> str:
        s = self.full_text_unrepaired
        # Replace text_entities in reverse order
        for entity in reversed(self.text_entities):
            s = entity.replace_in_string(s)
        return s

    def full_text_repaired_as_html(self, doc: Document):
        s = self.full_text_unrepaired
        for entity in reversed(self.text_entities):
            s = entity.replace_in_string_as_html(s, doc)
        return s

    def __hash__(self):
        return hash((self.id, ))

    def __eq__(self, other):
        return self.id == other.id

    def to_str(self) -> str:
        s = ""
        s += self.full_text_repaired
        # Add metadata
        s += "\n("
        s += f"{self.timestamp}"
        if self.is_reply:
            s += f", in reply to {self.reply_to_username}: {self.reply_to_tweet_id}"
        s += ")"
        return s

    def to_div(self, doc: Document):
        div = doc.createElement("div")
        p = parseString("<p>"+self.full_text_repaired_as_html(doc)+"</p>").documentElement
        div.appendChild(p)
        for m in self.media:
            div.appendChild(m.as_tag(doc))
        return div

    @classmethod
    def _parse_time(cls, time_str: str) -> datetime:
        return dt_parse(time_str)

    @classmethod
    def _parse_source(cls, source_str: str) -> str:
        link = BeautifulSoup(source_str, 'html.parser')
        # href = link.a["href"]
        content = link.a.string
        return content
