from newspaper import Article, Source
from markdownify import markdownify as md

from typing import Union

from fastapi import FastAPI
from typing import Literal
from pydantic import HttpUrl
from bs4 import BeautifulSoup

from .lib.transform import BlockTransform
from mangum import Mangum

app = FastAPI(title="Article Import API", version="0.1.0")


@app.get("/")
async def index():
    return {"msg": "gm"}


@app.get("/import")
def process_url(url: HttpUrl, doc_type: Literal['blocks', 'markdown'] = 'blocks'):
    article = Article(url, keep_article_html=True)
    article.download()
    article.parse()
    data = {
        "title": article.title,
        "authors": article.authors,
        "header_image": article.top_image,
        "images": article.images,
        "videos": article.movies,
    }
    if doc_type == "blocks":
        html_doc = BeautifulSoup(article.article_html)
        transformer = BlockTransform(html_doc)
        data["blocks"] = transformer.convert_prime(blocks=[])
    elif doc_type == "markdown":
        data["markdown"] = md(article.article_html, newline_styles='backslash')
    return data


handler = Mangum(app, lifespan="off")
