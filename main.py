from __future__ import annotations

import sys
from pathlib import Path

from entities import User
from paths import out_dir
from save_load import load_tweets_from_data_dir, save_tweets_as_text, save_tweets_as_html_list, \
    save_tweets_as_html_individual, load_user, copy_media_for_tweet, ArchiveMediaNotFoundError
from tweets import Tweet


def main(dirs: list[str]):
    if len(dirs) == 0:
        print("No paths supplied")
        return

    data_paths = [Path(d, "data") for d in dirs]
    tweets: set[Tweet] = set()
    # Collate tweets
    user: User | None = None
    missing_media_tweet_ids: set[int] = set()
    for data_path in data_paths:
        this_user: User = load_user(data_path)
        if user is None:
            user = this_user
        elif user.id != this_user.id:
            raise ValueError("Can't mix users")
        new_tweets: list[Tweet] = load_tweets_from_data_dir(data_path)
        tweets.update(new_tweets)
        for tweet in tweets:
            try:
                copy_media_for_tweet(tweet, user=user, from_dir=data_path, to_dir=out_dir, thumb_size_px=256)
            except ArchiveMediaNotFoundError as e:
                print(f"Media missing for tweet {tweet.id}: {e}")
                missing_media_tweet_ids.add(tweet.id)
                continue
    sorted_tweets: list[Tweet] = sorted(tweets, key=lambda t: t.timestamp, reverse=True)
    filtered_tweets: list[Tweet] = [
        t for t in sorted_tweets
        if not t.is_retweet
        and not t.is_quotetweet
        and not t.is_at_message
        and not t.id in missing_media_tweet_ids
    ]
    save_tweets_as_text(filtered_tweets, user=user, to_dir=out_dir)
    save_tweets_as_html_list(filtered_tweets, user=user, to_dir=out_dir)
    save_tweets_as_html_individual(sorted_tweets, user=user, to_dir=out_dir)


if __name__ == "__main__":
    main(list(sys.argv[1:]))
