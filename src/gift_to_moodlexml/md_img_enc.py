import logging
from pathlib import Path

from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension
import xml.etree.ElementTree as etree
import base64
from io import BytesIO
from PIL import Image

log = logging.getLogger(__name__)


class ImgBase64Encode(Treeprocessor):

    def process(self, t: etree.Element) -> None:
        children: list[str | etree.Element] = list(t) + list(t.itertext())
        for c in children:
            if not isinstance(c, etree.Element):
                continue
            if c.tag != "img":
                self.process(c)
                continue
            src = c.get("src")
            try:
                img_path = Path(src)
                if not img_path.is_file():
                    log.warning("Image file not found: %s", src)
                    continue
                with Image.open(img_path) as image:
                    buffered = BytesIO()
                    image.save(buffered, format=image.format)
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    img_src_base64 = (
                        f"data:image/{image.format.lower()};base64,{img_str}"
                    )

                    old_text = c.text
                    old_tail = c.tail

                    img_tag = etree.Element("img")
                    img_tag.set("src", img_src_base64)
                    img_tag.set("width", "512px")
                    c.tag = "p"
                    c.clear()  # Remove existing attributes and children
                    c.append(img_tag)  # Add the new img tag as a child

                    c.text = old_text  # Restore original text if needed
                    tail_p = etree.Element("p")
                    tail_p.text = old_tail  # Restore original tail if needed
                    c.append(tail_p)  # Add the tail as a new paragraph

            except Exception as e:
                log.warning("Error processing image %s: %s", src, e)

    def run(self, root) -> None:
        self.process(root)


class ImgBase64EncodeExtension(Extension):
    """Inline local images as base64 data URIs."""

    def extendMarkdown(self, md):

        md.treeprocessors.register(ImgBase64Encode(md.parser), "img_base64", -10)
