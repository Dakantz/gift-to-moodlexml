"""Model objects -> Moodle XML."""

import re

import markdown
from lxml import etree

from .md_img_enc import ImgBase64EncodeExtension
from .models import (
    Category,
    Item,
    MultipleChoiceQuestion,
    Question,
    ShortAnswerQuestion,
    TrueFalseQuestion,
)


def _sub(parent, tag: str, text=None, **attrs):
    el = etree.SubElement(parent, tag, **attrs)
    if text is not None:
        el.text = text
    return el


def _category(quiz, name: str):
    q = _sub(quiz, "question", type="category")
    _sub(_sub(q, "category"), "text", f"$course$/top/{name}")


def _answers(q: Question) -> list[tuple[str, str]]:
    """(fraction, text) pairs."""
    match q:
        case TrueFalseQuestion():
            sign = 1 if q.answer else -1
            return [(str(100 * sign), "True"), (str(-100 * sign), "False")]
        case MultipleChoiceQuestion():
            return [(c.moodle_fraction, c.text) for c in q.choices]
        case ShortAnswerQuestion():
            return [("100", a) for a in q.answers]
    return []


def _question_html(q: Question) -> tuple[str, str]:
    text = q.text
    if isinstance(q, ShortAnswerQuestion):
        text += " `________` " + q.after_text
    text = re.sub(r"(```(\w+)?)", lambda m: f"\n{m.group(0)}\n", text)
    if q.format != "markdown":
        return text, q.format
    return markdown.markdown(text, extensions=["extra", ImgBase64EncodeExtension()]), "html"


def question_to_xml(q: Question) -> etree._Element:
    el = etree.Element("question", type=q.moodle_type)
    for fraction, text in _answers(q):
        _sub(_sub(el, "answer", format=q.format, fraction=fraction), "text", text)
    _sub(_sub(el, "name"), "text", q.title)
    if isinstance(q, MultipleChoiceQuestion) and not q.single:
        _sub(el, "single", "false")
    text, fmt = _question_html(q)
    _sub(_sub(el, "questiontext", format=fmt), "text", etree.CDATA(text))
    _sub(el, "defaultgrade", str(q.score))
    tags = _sub(el, "tags")
    for tag in (f"cat={q.moodle_type}", f"points={q.score}"):
        _sub(_sub(tags, "tag"), "text", tag)
    _sub(el, "usecase", "0")
    return el


def to_moodle_xml(items: list[Item], output_file: str | None = "quiz.xml"):
    quiz = etree.Element("quiz")
    category = "Uncategorized"
    for item in items:
        if isinstance(item, Category):
            category = item.name
            _category(quiz, category)
        elif not item.disabled:
            _category(quiz, f"{category}/{item.moodle_type}")
            quiz.append(question_to_xml(item))
    tree = etree.ElementTree(quiz)
    etree.indent(tree, space="  ")
    if output_file is not None:
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
    return tree
