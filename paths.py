from pathlib import Path

out_dir: Path = Path(Path(__file__).parent, "out")

tweet_dir_name: str = "status"
media_archive_dir_name: str = "tweets_media"
media_target_dir_name: str = "media"
thumbs_dir_name: str = "media_thumbs"

saved_text_file_name: str = "tweets.txt"
saved_html_file_name: str = "index.html"

tweet_data_filename_new: str = "tweets.js"
tweet_data_filename_old: str = "tweet.js"
account_data_filename: str = "account.js"
