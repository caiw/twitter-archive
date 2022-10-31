import sys
from pathlib import Path

from paths import tweet_dir_name
from tweets import Tweet
from save_load import load_tweets_from_twitterjs, save_tweets_as_text, \
    save_tweets_as_html_list, save_tweets_as_html_individual


def main(dirs: list[str]):
    output_dir: Path = Path(Path(__file__).parent, "out")
    data_paths = [Path(d, "data") for d in dirs]
    tweets: set[Tweet] = set()
    # Collate tweets
    for data_path in data_paths:
        tw_js_path = Path(data_path, "tweets.js")
        new_tweets: list[Tweet] = load_tweets_from_twitterjs(tw_js_path)
        tweets.update(new_tweets)
    sorted_tweets: list[Tweet] = sorted(tweets, key=lambda t: t.timestamp, reverse=True)
    filtered_tweets: list[Tweet] = [
        t for t in sorted_tweets
        if not t.is_retweet
        and not t.is_quotetweet
        and not t.is_at_message
    ]
    save_tweets_as_text(filtered_tweets, to_path=Path(output_dir, "tweets.txt"))
    save_tweets_as_html_list(filtered_tweets, to_path=Path(output_dir, "tweets.html"))
    save_tweets_as_html_individual(sorted_tweets, to_path=Path(output_dir, tweet_dir_name))


if __name__ == "__main__":
    main(list(sys.argv[1:]))
