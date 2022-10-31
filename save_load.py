import json
from pathlib import Path
from xml.dom.minidom import getDOMImplementation, Document

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


def _get_dom() -> Document:
    impl = getDOMImplementation()
    dt = impl.createDocumentType(
        "html",
        "-//W3C//DTD XHTML 1.0 Strict//EN",
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd",
    )
    return impl.createDocument("http://www.w3.org/1999/xhtml", "html", dt)


def save_tweets_as_html_list(tweets: list[Tweet], to_path: Path) -> None:
    doc: Document = _get_dom()

    lst = doc.createElement("ul")
    for tweet in tweets:
        li = doc.createElement("li")
        li.appendChild(tweet.to_div(doc))
        lst.appendChild(li)
    tweets_div = doc.createElement("div")
    tweets_div.appendChild(lst)

    html = doc.documentElement
    html.appendChild(tweets_div)
    with to_path.open("w") as out_file:
        out_file.write(doc.toxml())


def save_tweets_as_html_individual(tweets: list[Tweet], to_path: Path) -> None:
    to_path.mkdir(parents=False, exist_ok=True)

    doc: Document
    for tweet in tweets:
        doc = _get_dom()
        html = doc.documentElement
        html.appendChild(tweet.to_div(doc))
        with Path(to_path, f"{tweet.id}.html").open("w") as out_file:
            out_file.write(doc.toxml())
