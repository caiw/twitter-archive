import json
from pathlib import Path

from tweets import Tweet


def load_tweets_from_twitterjs(tw_js_path: Path) -> list[Tweet]:
    """Load a list of tweets from a twitter.js file."""
    with tw_js_path.open("r") as tw_js_file:
        tweets_txt: list[str] = tw_js_file.readlines()
        tweets_txt = ["[\n"] + tweets_txt[1:]  # Convert js to json
        tweets_js: list[dict] = json.loads("\n".join(tweets_txt))
        return [Tweet(d) for d in tweets_js]


def save_tweets_as_text(tweets: list[Tweet], to_path: Path) -> None:
    s = "\n\n".join(t.to_str() for t in tweets) + "\n"
    with to_path.open("w") as out_file:
        out_file.write(s)
