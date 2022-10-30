from abc import ABC, abstractmethod


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
