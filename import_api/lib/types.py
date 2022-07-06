from pydantic import HttpUrl


class SitemapUrl(HttpUrl):

    @classmethod
    def __get_validators__(cls):
        yield super().validate
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if "sitemap.xml" not in v:
            raise TypeError("Not a valid sitemap")
        return v
