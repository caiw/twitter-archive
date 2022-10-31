import sys
from pathlib import Path

from tweets import Tweet
from save_load import load_tweets_from_twitterjs, save_tweets_as_text, \
    save_tweets_as_html


def is_self_reply(t: Tweet) -> bool:
    return t.is_reply and t.reply_to_username == "caiwingfield"


def main(dirs: list[str]):
    output_dir: Path = Path("/Users/cai/Desktop/")
    data_paths = [Path(d, "data") for d in dirs]
    tweets: set[Tweet] = set()
    # Collate tweets
    for data_path in data_paths:
        tw_js_path = Path(data_path, "tweets.js")
        new_tweets: list[Tweet] = load_tweets_from_twitterjs(tw_js_path)
        tweets.update(
            t for t in new_tweets
            if not t.is_retweet
            and not t.is_quotetweet
            and not t.is_at_message
        )
    sorted_tweets: list[Tweet] = sorted(tweets, key=lambda t: t.timestamp, reverse=True)
    save_tweets_as_text(sorted_tweets, to_path=Path(output_dir, "test.txt"))
    save_tweets_as_html(sorted_tweets, to_path=Path(output_dir, "test.html"))


if __name__ == "__main__":
    main(sys.argv[1:])
