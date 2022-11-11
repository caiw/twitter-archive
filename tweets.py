from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from re import sub
from xml.dom.minidom import Document, parseString

from dateutil.parser import parse as dt_parse
from bs4 import BeautifulSoup
from pytz import timezone

from entities import ShortenedURL, UserMention, Entity, Media
from paths import tweet_dir_name


class Tweet:

    def __init__(self, d: dict):
        self._dict: dict = d["tweet"]

    @property
    def id(self) -> int: return int(self._dict['id'])

    @property
    def timestamp(self) -> datetime:
        time = self._parse_time(self._dict['created_at'])
        return time.astimezone(timezone("Europe/London"))

    @property
    def source(self) -> str: return self._parse_source(self._dict['source'])

    @property
    def favourites(self) -> int: return int(self._dict['favorite_count'])

    @property
    def retweets(self) -> int: return int(self._dict['retweet_count'])

    @property
    def full_text_unrepaired(self) -> str: return self._dict['full_text']

    # Reply

    @property
    def reply_to_tweet_id(self) -> int | None:
        try: return int(self._dict['in_reply_to_status_id'])
        except KeyError: return None

    @property
    def reply_to_username(self) -> str | None:
        try: return self._dict["in_reply_to_screen_name"]
        except KeyError: return None

    @property
    def reply_to_userid(self) -> int | None:
        try: return int(self._dict["in_reply_to_user_id"])
        except KeyError: return None

    # Entities

    # URLs
    @property
    def shortened_urls(self) -> list[ShortenedURL]:
        try: return [ShortenedURL(url) for url in
                     self._dict["entities"]["urls"]]
        except KeyError: return []

    # Mentions
    @property
    def user_mentions(self) -> list[UserMention]:
        try: return [UserMention(mention) for mention in
                     self._dict["entities"]["user_mentions"]]
        except KeyError: return []

    # Media
    @property
    def media(self) -> list[Media]:
        try: return [Media(image, parent_tweet_id=self.id) for image in
                     self._dict["extended_entities"]["media"]]
        except KeyError: return []

    @property
    def text_entities(self) -> list[Entity]:
        # noinspection PyTypeChecker
        return sorted(
            self.shortened_urls
            + self.user_mentions
            + self.media,
            key=lambda e: e.indices[0]
        )

    @property
    def is_at_message(self) -> bool:
        return self.reply_to_userid is not None

    @property
    def is_reply(self) -> bool:
        return self.reply_to_tweet_id is not None

    @property
    def is_retweet(self) -> bool:
        # Should handle old- and new-style RTs
        return "RT @" in self.full_text_unrepaired

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
        # Replace html entities which failed to be replaced
        s = sub(r"&([^agl])", r"&amp;\1", s)
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
        s += self._format_datetime(self.timestamp)
        if self.is_reply:
            s += f", in reply to {self.reply_to_username}: {self.reply_to_tweet_id}"
        s += ")"
        return s

    def to_div(self, doc: Document, relative_depth):
        tweet = doc.createElement("div")
        tweet.setAttribute("class", "tweet")
        tweet.setAttribute("id", f"tweet{self.id}")
        # Date
        date = doc.createElement("div")
        date.setAttribute("class", "timestamp")
        time = self._format_datetime(self.timestamp)
        date.appendChild(parseString(f'<a href="{tweet_dir_name}/{self.id}.html">{time}</a>').documentElement)
        tweet.appendChild(date)
        # Reply
        if self.is_at_message:
            reply_note = doc.createElement("div")
            reply_note.setAttribute("class", "reply-note")
            if self.is_reply:
                # Repy to direct tweet
                reply_note.appendChild(parseString(
                    f'<p>In reply to <a href="https://twitter.com/{self.reply_to_username}/status/{self.reply_to_tweet_id}">@{self.reply_to_username}</a></p>'
                ).documentElement)
            # else:
            #     # Just @-message
            #     reply_note.appendChild(parseString(
            #         f'<p>In reply to <a href="https://twitter.com/{self.reply_to_username}">@{self.reply_to_username}</a></p>'
            #     ).documentElement)
            tweet.appendChild(reply_note)
        # Tweet p
        p = parseString("<p>"+self.full_text_repaired_as_html(doc)+"</p>").documentElement
        tweet.appendChild(p)
        # Images
        for m in self.media:
            tweet.appendChild(m.as_tag(doc, relative_depth))
        return tweet

    @classmethod
    def _parse_time(cls, time_str: str) -> datetime:
        return dt_parse(time_str)

    @classmethod
    def _format_datetime(cls, dt: datetime) -> str:
        ordinal = defaultdict(lambda: 'th', {'1': 'st', '2': 'nd', '3': 'rd'})

        day_name = f"{dt:%A}"  # Thursday
        day = f"{dt:%-d}"  # 3
        th = ordinal[day[-1]]  # rd
        month = f"{dt:%B}"  # November
        year = f"{dt:%Y}"  # 2022
        hour = f"{dt:%-I}"  # 9
        minute = f"{dt:%M}"  # 29
        am_pm = f"{dt:%p}".lower()  # am

        return f"{day_name} {day}{th} {month} {year}, at {hour}:{minute} {am_pm}"

    @classmethod
    def _parse_source(cls, source_str: str) -> str:
        link = BeautifulSoup(source_str, 'html.parser')
        # href = link.a["href"]
        content = link.a.string
        return content
