"""GIFT text/files -> model objects."""

import logging
from pathlib import Path

from pyparsing import ParseException, ParseResults

from .grammar import GRAMMAR
from .models import (
    Category,
    Choice,
    EssayQuestion,
    Item,
    MultipleChoiceQuestion,
    Question,
    ShortAnswerQuestion,
    TrueFalseQuestion,
)

log = logging.getLogger(__name__)


def split_blocks(content: str, recombine: bool = False) -> list[str]:
    """Split GIFT content into one block per category/question.

    Plain mode splits on blank lines. With `recombine`, a question only starts at
    a `[params]` line, so blank lines inside a question (images, paragraphs) are kept.
    """
    raw = [b.strip() for b in content.strip().split("\n\n")]
    if not recombine:
        return [b for b in raw if b]

    blocks: list[str] = []
    running = ""
    for b in raw:
        if not b:
            continue
        if b.startswith("$CATEGORY:"):
            head, _, rest = b.partition("\n")
            if running:
                blocks.append(running)
            blocks.append(head)
            running = rest.strip()
        elif b.startswith("[") or not running:
            if running:
                blocks.append(running)
            running = b
        else:
            running += "\n\n" + b
    if running:
        blocks.append(running)
    return blocks


def _to_question(q: ParseResults) -> Question:
    words = [p for p in q.get("params", []) if p != "points=" and not p.isdigit()]
    common = dict(
        text=q["text"],
        format=next((w for w in words if w != "disable"), "markdown"),
        points=int(q["points"]) if "points" in q else None,
        disabled="disable" in words,
    )
    if "tf_value" in q:
        return TrueFalseQuestion(answer=q["tf_value"] in ("T", "TRUE"), **common)
    if "choices" not in q:
        return EssayQuestion(**common)

    choices = [
        Choice(c["choice_text"].strip(), c["is_correct"] == "=", c.get("fraction"))
        for c in q["choices"]
    ]
    if not all(c.correct for c in choices):
        return MultipleChoiceQuestion(choices=choices, **common)
    after = (q.get("after_text") or "").strip()
    if after:
        return ShortAnswerQuestion(
            answers=[c.text for c in choices], after_text=after, **common
        )
    return EssayQuestion(**common)


def parse_block(block: str) -> list[Item]:
    """Parse one block; returns [] (and logs) if it is not valid GIFT."""
    try:
        result = GRAMMAR.parse_string(block, parse_all=True)
    except ParseException as e:
        log.warning("Could not parse question: %s\n%s", e, block)
        return []
    return [
        Category(g["name"].strip()) if "name" in g else _to_question(g) for g in result
    ]


def parse_gift(content: str, recombine: bool = False) -> list[Item]:
    return [item for b in split_blocks(content, recombine) for item in parse_block(b)]


def load_gift_files(paths, recombine: bool = True) -> list[Item]:
    """Parse several .gift files; recombination is on by default for files."""
    return [
        item for p in paths for item in parse_gift(Path(p).read_text(), recombine)
    ]


def group_by_category(items: list[Item]) -> dict[str, list[Question]]:
    """Enabled questions keyed by their (most recent) category name."""
    groups: dict[str, list[Question]] = {}
    current = "Uncategorized"
    for item in items:
        if isinstance(item, Category):
            current = item.name
        elif not item.disabled:
            groups.setdefault(current, []).append(item)
    return groups
