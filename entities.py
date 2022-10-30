from abc import ABC, abstractmethod
from pathlib import Path


class Entity(ABC):
    def __init__(self, d: dict):
        indices: list[int] = list(int(i) for i in d["indices"])
        assert len(indices) == 2
        self.indices: tuple[int, int] = (indices[0], indices[1])

    @abstractmethod
    def replace_in_string(self, s: str) -> str:
        pass


class ShortenedURL(Entity):
    def __init__(self, d: dict):
        super().__init__(d)
        self.url: str = d["expanded_url"]
        self.shortened_url: str = d["url"]
        self.display_url: str = d["display_url"]

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
        return f"tweets_media/{self.parent_tweet_id}-{self.name}.{extension}"

    def replace_in_string(self, s: str) -> str:
        new_s = s[:self.indices[0]]
        new_s += self.url_localised
        new_s += s[self.indices[1]:]
        return new_s

    @classmethod
    def _get_name(cls, from_url: str) -> str:
        return Path(from_url).stem

    @classmethod
    def _get_extension(cls, from_url: str):
        return Path(from_url).suffix
