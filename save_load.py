import json
from pathlib import Path
from shutil import copy
from xml.dom.minidom import getDOMImplementation, Document, Element

from PIL import Image

from entities import User
from paths import tweet_data_filename, account_data_filename, tweet_dir_name, \
    saved_text_file_name, saved_html_file_name, media_dir_name, thumbs_dir_name
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
    relative_depth = 1  # media folder is sibling
    if len(tweets) == 0:
        return

    doc: Document = _get_dom()

    tweets_list_div = doc.createElement("div")
    tweets_list_div.setAttribute("class", "tweets")
    for tweet in tweets:
        t_div = doc.createElement("div")
        t_div.appendChild(tweet.to_div(doc, relative_depth=relative_depth))
        tweets_list_div.appendChild(t_div)

    body = _get_body(doc, title="Tweets", relative_depth=relative_depth)
    body.appendChild(tweets_list_div)
    save_dir = Path(to_dir, user.name)
    with Path(save_dir, saved_html_file_name).open("wb") as out_file:
        out_file.write(doc.toprettyxml(encoding="utf-8"))


def save_tweets_as_html_individual(tweets: list[Tweet], user: User, to_dir: Path) -> None:
    relative_depth = 2  # media dir is above status dir

    to_dir.mkdir(parents=False, exist_ok=True)

    save_dir = Path(to_dir, user.name, tweet_dir_name)
    save_dir.mkdir(parents=False, exist_ok=True)

    doc: Document
    for tweet in tweets:
        doc = _get_dom()
        body = _get_body(doc, title="Tweet", relative_depth=relative_depth)
        body.appendChild(tweet.to_div(doc, relative_depth=relative_depth))
        with Path(save_dir, f"{tweet.id}.html").open("wb") as out_file:
            out_file.write(doc.toprettyxml(encoding="utf-8"))


def _get_body(doc: Document, title: str, relative_depth: int) -> Element:
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
    for _ in range(relative_depth):
        relative_path_to_stylesheet = "../" + relative_path_to_stylesheet
    link.setAttribute("href", relative_path_to_stylesheet)
    head.appendChild(link)
    html.appendChild(head)
    # Body
    body = doc.createElement("body")
    html.appendChild(body)
    return body


def copy_media(tweets: list[Tweet], user: User, from_dir: Path, to_dir: Path, thumb_size_px: int) -> None:
    for tweet in tweets:
        if tweet.is_retweet:
            continue
        for media in tweet.media:
            archive_media = Path(from_dir, "tweets_media", f"{media.parent_tweet_id}-{media.name}{media.extension}")
            target_media_dir = Path(to_dir, user.name, media_dir_name)
            target_media_dir.mkdir(parents=False, exist_ok=True)
            if not Path(target_media_dir, archive_media.name).exists():
                copy(archive_media, target_media_dir)
            # Thumbnails
            target_media_thumb_dir = Path(to_dir, user.name, thumbs_dir_name)
            target_media_thumb_dir.mkdir(parents=False, exist_ok=True)
            _save_thumb(archive_media, target_media_thumb_dir, thumb_size=thumb_size_px)


def _save_thumb(archive_media, target_media_thumb_dir, thumb_size: int):
    image = Image.open(archive_media)
    im_w: int
    im_h: int
    im_w, im_h = image.size
    thumb_w, thumb_h = _get_thumb_dimensions(im_h, im_w, thumb_size)
    thumb = image.resize((thumb_w, thumb_h))
    thumb.save(Path(target_media_thumb_dir,
                    f"{archive_media.stem}-thumb{archive_media.suffix}"))


def _get_thumb_dimensions(im_h: int, im_w: int, thumb_size: int) -> tuple[int, int]:
    if max(im_w, im_h) <= thumb_size:
        thumb_w, thumb_h = im_w, im_h
    elif im_w > im_h:
        thumb_w = thumb_size
        factor = thumb_size / im_w
        thumb_h = im_h * factor
    else:
        thumb_h = thumb_size
        factor = thumb_size / im_h
        thumb_w = im_w * factor
    return int(thumb_w), int(thumb_h)
