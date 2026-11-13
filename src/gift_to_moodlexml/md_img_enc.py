from pathlib import Path

from markdown.blockprocessors import BlockProcessor
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension
import xml.etree.ElementTree as etree
import re
import base64
from io import BytesIO
from PIL import Image


class ImgBase64Encode(Treeprocessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.img_counter = 0

    def process(self, t: etree.Element) -> None:
        children: list[str | etree.Element] = list(t) + list(t.itertext())
        print(
            f"Processing element: {t.tag}, children: {[c.tag if hasattr(c, 'tag') else str(c) for c in children]}"
        )
        for c in children:
            if not isinstance(c, etree.Element):
                continue
            if c.tag != "img":
                self.process(c)
                continue
            print(f"Processing tag: {c}")
            src = c.get("src")
            try:
                img_path = Path(src)
                if not img_path.is_file():
                    print(f"Image file not found: {src}")
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
                    img_tag.set("alt", c.get("alt"))
                    c.tag = "p"
                    c.clear()  # Remove existing attributes and children
                    c.append(img_tag)  # Add the new img tag as a child

                    c.text = old_text  # Restore original text if needed
                    tail_p = etree.Element("p")
                    tail_p.text = old_tail  # Restore original tail if needed
                    c.append(tail_p)  # Add the tail as a new paragraph

                    # <img class="img-fluid" src="@@PLUGINFILE@@/Screenshot%202026-06-09%20at%2009.40.40.png" alt="map
                    # " width="716" height="920"></p>]]></text>
                    # <file name="Screenshot 2026-06-09 at 09.40.40.png" path="/" encoding="base64">iVBORw0KGgoAAAANSUhEUgAAAswAAAOYCAYAAADBua
                    print(
                        f"Encoded image {src} to base64: {img_str[:30]}...",
                        "New children:",
                    )  # Print first 30 chars for verification
                    # del c.attrib["src"]
            except Exception as e:
                print(f"Error processing image {src}: {e}")

    def run(self, root) -> None:
        self.process(root)
        etree.dump(root)  # Print the entire tree for debugging


class ImgBase64EncodeExtension(Extension):
    """Add definition lists to Markdown."""

    def extendMarkdown(self, md):

        md.treeprocessors.register(ImgBase64Encode(md.parser), "img_base64", -10)
