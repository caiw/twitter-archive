import json
from pathlib import Path
from shutil import copy
from xml.dom.minidom import getDOMImplementation, Document, Element

from entities import User
from paths import tweet_data_filename, account_data_filename, tweet_dir_name, \
    saved_text_file_name, saved_html_file_name
from tweets import Tweet


def _json_from_js_file(js_file) -> list[dict]:
    js_lines: list[str] = js_file.readlines()
    js_lines = ["[\n"] + js_lines[1:]  # Convert js var assignment to opening list
    return json.loads("\n".join(js_lines))


def load_tweets_from_data_dir(data_dir: Path) -> list[Tweet]:
    """Load a list of tweets from a twitter.js file."""
    with Path(data_dir, tweet_data_filename).open("r") as tw_js_file:
        tweets: list[dict] = _json_from_js_file(tw_js_file)
    return [Tweet(d) for d in tweets]


def load_user(data_dir: Path) -> User:
    with Path(data_dir, account_data_filename).open("r") as account_js_file:
        user_dict: dict = _json_from_js_file(account_js_file)[0]['account']
    return User(
        id=int(user_dict['accountId']),
        name=user_dict['username'],
    )


def save_tweets_as_text(tweets: list[Tweet], user: User, to_dir: Path) -> None:
    s = "\n\n".join(t.to_str() for t in tweets) + "\n"
    save_dir = Path(to_dir, user.name)
    save_dir.mkdir(parents=False, exist_ok=True)
    with Path(save_dir, saved_text_file_name).open("w") as out_file:
        out_file.write(s)


def _get_dom() -> Document:
    impl = getDOMImplementation()
    dt = impl.createDocumentType(
        "html",
        "-//W3C//DTD XHTML 1.0 Strict//EN",
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd",
    )
    return impl.createDocument("http://www.w3.org/1999/xhtml", "html", dt)


def save_tweets_as_html_list(tweets: list[Tweet], user: User, to_dir: Path) -> None:
    if len(tweets) == 0:
        return

    doc: Document = _get_dom()

    tweets_list_div = doc.createElement("div")
    for tweet in tweets:
        t_div = doc.createElement("div")
        t_div.appendChild(tweet.to_div(doc))
        tweets_list_div.appendChild(t_div)

    body = _get_body(doc, title="Tweets", relative_depth_from_stylesheet=1)
    body.appendChild(tweets_list_div)
    save_dir = Path(to_dir, user.name)
    with Path(save_dir, saved_html_file_name).open("w") as out_file:
        out_file.write(doc.toxml())


def save_tweets_as_html_individual(tweets: list[Tweet], user: User, to_dir: Path) -> None:
    to_dir.mkdir(parents=False, exist_ok=True)

    save_dir = Path(to_dir, user.name, tweet_dir_name)
    save_dir.mkdir(parents=False, exist_ok=True)

    doc: Document
    for tweet in tweets:
        doc = _get_dom()
        body = _get_body(doc, title="Tweet", relative_depth_from_stylesheet=2)
        body.appendChild(tweet.to_div(doc))
        with Path(save_dir, f"{tweet.id}.html").open("w") as out_file:
            out_file.write(doc.toxml())


def _get_body(doc: Document, title: str, relative_depth_from_stylesheet: int) -> Element:
        html = doc.documentElement
        head = doc.createElement("head")
        # Title
        title_element: Element = doc.createElement("title")
        title_element.appendChild(doc.createTextNode(title))
        head.appendChild(title_element)
        # Stylesheet
        link = doc.createElement("link")
        link.setAttribute("rel", "stylesheet")
        relative_path_to_stylesheet = "tweet.css"
        for _ in range(relative_depth_from_stylesheet):
            relative_path_to_stylesheet = "../" + relative_path_to_stylesheet
        link.setAttribute("href", relative_path_to_stylesheet)
        head.appendChild(link)
        html.appendChild(head)
        # Body
        body = doc.createElement("body")
        html.appendChild(body)
        return body


def copy_media(tweets: list[Tweet], user: User, from_dir: Path, to_dir: Path) -> None:
    for tweet in tweets:
        if tweet.is_retweet:
            continue
        for media in tweet.media:
            archive_media = Path(from_dir, "tweets_media", f"{media.parent_tweet_id}-{media.name}{media.extension}")
            target_media_dir = Path(to_dir, user.name, "media")
            target_media_dir.mkdir(parents=False, exist_ok=True)
            if not Path(target_media_dir, archive_media.name).exists():
                copy(archive_media, target_media_dir)
