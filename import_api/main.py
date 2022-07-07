from newspaper import Article, Source
from markdownify import markdownify as md

from typing import Optional

from fastapi import FastAPI, HTTPException

from typing import Literal, Optional
from bs4 import BeautifulSoup
import requests
import tldextract
import json
from readabilipy import simple_json_from_html_string

from .lib.transform import BlockTransform
from .lib.types import SitemapUrl, HttpUrl

app = FastAPI(title="Article Import API", version="0.1.0")


def guess_sitemap(blog: HttpUrl):
    blog_parsed = tldextract.extract(blog)
    guessed_sitemap = f"{blog}/sitemap.xml"

    if blog_parsed.domain == "medium":
        guessed_sitemap = f"{blog}/sitemap/sitemap.xml"
        if blog_parsed.subdomain is None:
            guessed_sitemap = f"{blog}/feed"
    return guessed_sitemap


@ app.get("/")
async def index():
    return {"msg": "gm"}


@ app.get("/import")
async def process_url(url: HttpUrl, doc_type: Literal['blocks', 'markdown'] = 'blocks'):
    article = Article(url)
    article.download()
    article.parse()

    article_json = simple_json_from_html_string(
        article.html, use_readability=True)

    # TODO: Author and Publish Date works only for certain sources
    data = {
        "title": article.title,
        "authors": article.authors,
        "header_image": article.top_image,
        "images": article.images,
        "videos": article.movies,
        "original_url": url,
        "published_date": article.publish_date
    }
    article_html = article_json["content"]
    if doc_type == "blocks":
        html_doc = BeautifulSoup(article_html)
        transformer = BlockTransform(html_doc)
        data["blocks"] = transformer.convert_prime(blocks=[])
    elif doc_type == "markdown":
        data["markdown"] = md(article_html, newline_styles='backslash')
    return data


@ app.get("/import/discover")
async def discover_urls(blog: HttpUrl, sitemap: Optional[SitemapUrl] = None):

    if sitemap:
        response = requests.get(sitemap)
        data = response.text
        soup = BeautifulSoup(data)
        urls = [url.loc.text for url in soup.find_all("url")]
        if not len(urls):
            raise HTTPException(detail="Given sitemap didn't return any urls."
                                " Please check the sitemap again",
                                status_code=404)
        return {
            "urls": urls
        }
    else:
        guessed_sitemap = guess_sitemap(blog)
        return await discover_urls(blog, guessed_sitemap)
