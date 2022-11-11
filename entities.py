from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from xml.dom.minidom import Document, Element

from paths import thumbs_dir_name, media_target_dir_name


@dataclass
class User:
    id: int
    name: str
    # display_name: str | None


class Entity(ABC):
    def __init__(self, d: dict):
        indices: list[int] = list(int(i) for i in d["indices"])
        assert len(indices) == 2
        self.indices: tuple[int, int] = (indices[0], indices[1])

    @abstractmethod
    def replace_in_string(self, s: str) -> str:
        pass

    def replace_in_string_as_html(self, s: str, doc: Document):

        new_s = s[:self.indices[0]]
        new_s += self.as_tag(doc).toxml()
        new_s += s[self.indices[1]:]
        return new_s

    @abstractmethod
    def as_tag(self, doc: Document):
        pass


class ShortenedURL(Entity):
    def __init__(self, d: dict):
        super().__init__(d)
        self.url: str = d["expanded_url"]
        self.shortened_url: str = d["url"]
        self.display_url: str = d["display_url"]

    def as_tag(self, doc: Document) -> Element:
        a = doc.createElement("a")
        a.appendChild(doc.createTextNode(self.display_url))
        a.setAttribute("href", self.url)
        return a

    def replace_in_string(self, s: str) -> str:
        new_s = s[:self.indices[0]]
        new_s += self.url
        new_s += s[self.indices[1]:]
        return new_s


class UserMention(Entity):
    def __init__(self, d: dict):
        super().__init__(d)
        self.username: str = d["screen_name"]
        self.userid: int = int(d["id"])
        self.display_name: str = d["name"]

    def as_tag(self, doc: Document):
        a = doc.createElement("a")
        a.appendChild(doc.createTextNode(f"@{self.username}"))
        a.setAttribute("href", "https://twitter.com/" + self.username)
        a.setAttribute("class", "at_handle")
        return a

    def replace_in_string(self, s: str) -> str:
        new_s = s[:self.indices[0]]
        new_s += "@" + self.username
        new_s += s[self.indices[1]:]
        return new_s


class Media(ShortenedURL):
    def __init__(self, d: dict, parent_tweet_id: int):
        super().__init__(d)
        self.id: int = int(d["id"])
        self.url_original: str = d["media_url_https"]
        self.parent_tweet_id: int = parent_tweet_id
        self.name: str = self._get_name(from_url=self.url_original)
        self.extension: str = self._get_extension(from_url=self.url_original)

    @property
    def url_localised(self) -> str:
        extension = self.url_original[-3:]
        return f"{media_target_dir_name}/{self.parent_tweet_id}-{self.name}.{extension}"

    @property
    def thumb_url_localised(self) -> str:
        extension = self.url_original[-3:]
        return f"{thumbs_dir_name}/{self.parent_tweet_id}-{self.name}-thumb.{extension}"

    def as_tag(self, doc: Document, relative_depth: int = 1):
        url = self.url_localised
        url_thumb = self.thumb_url_localised
        for _ in range(relative_depth - 1):
            url = "../" + url
            url_thumb = "../" + url_thumb
        img = doc.createElement("img")
        img.setAttribute("src", url_thumb)
        img.setAttribute("class", "thumb")
        a = doc.createElement("a")
        a.setAttribute("href", url)
        a.appendChild(img)
        container = doc.createElement("div")
        container.setAttribute("class", "media-container")
        container.appendChild(a)
        return container

    def replace_in_string(self, s: str) -> str:
        # Cut it out
        return s[:self.indices[0]] +  s[self.indices[1]:]

    def replace_in_string_as_html(self, s: str, doc: Document):
        return self.replace_in_string(s)

    @classmethod
    def _get_name(cls, from_url: str) -> str:
        return Path(from_url).stem

    @classmethod
    def _get_extension(cls, from_url: str):
        return Path(from_url).suffix
