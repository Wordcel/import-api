import logging


class BlockTransform(object):

    def __init__(self, html):
        self.html = html

    def embed_tweet(self, html):
        links = html.find_all('a')
        if len(links):
            tweet = links[-1].attrs["href"]
            content = {"service": "twitter",
                       "source": tweet,
                       "embed": f"https://twitframe.com/show?url={tweet}",
                       "width": 600,
                       "height": 300,
                       "caption": ""
                       }
            return {"type": "embed", "data": content}

    def paragraph(self, node):
        content = "".join([str(c) for c in node.contents])
        return {"type": "paragraph", "data": {"text": content}}

    def header(self, node, level):
        return {"type": "header", "data": {
            "level": level, "text": node.text}}

    def html_list(self, node, list_type):
        block = {"type": "list", "data": {"style": "", "items": []}}
        if list_type == "ol":
            block["data"]["style"] = "ordered"
        elif list_type == "ul":
            block["data"]["style"] = "unordered"
        items = node.select("li")
        for item in items:
            content = "".join([str(c) for c in item.contents])
            block["data"]["items"].append(content)
        return block

    def convert_prime(self, blocks, html=None):
        if not html:
            html = self.html
        for i in html.children:
            name = i.name
            if not name:
                continue
            if name in ['html', 'body', 'div', 'a']:
                self.convert_prime(blocks, i)
            elif name == 'p':
                block = self.paragraph(i)
                blocks.append(block)
            elif len(name) == 2 and name.startswith("h"):
                level = name[-1]
                block = self.header(i, level)
                blocks.append(block)
            elif name in ['ol', 'ul']:
                block = self.html_list(i, name)
                blocks.append(block)
            elif name == 'blockquote':
                content = i.encode_contents()
                if b"twitter" in content:
                    block = self.embed_tweet(i)
                else:
                    block = {"type": "blockquote",
                             "data": {"text": str(content)}}
                blocks.append(block)
            elif name == "img":
                content = {"url": i.attrs["src"],
                           "caption": i.attrs["alt"]}
                block = {"type": "image", "data": content}
                blocks.append(block)
            else:
                logging.error(f"Missed: {name}")
                logging.error(i)
        return blocks
