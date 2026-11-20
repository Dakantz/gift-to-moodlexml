"""Model objects -> LaTeX snippets (via pandoc)."""

import pypandoc

from .models import (
    MultipleChoiceQuestion,
    Question,
    ShortAnswerQuestion,
    TrueFalseQuestion,
)

ANSWER_SPACE = "\\vspace*{8em}\n"


def md_to_tex(text: str, format: str = "markdown") -> str:
    return pypandoc.convert_text(text, "latex", format=format)


def _checkboxes(options: list[str]) -> str:
    items = "".join(f"\\item[$\\square$] {o}\n" for o in options)
    return f"\\begin{{itemize}}\n{items}\\end{{itemize}}\n"


def question_tex(q: Question) -> str:
    fmt = q.format if q.format in ("markdown", "html", "latex") else "markdown"
    return md_to_tex(q.text, fmt)


def answer_tex(q: Question) -> str:
    """What follows the question on paper: checkboxes, a blank or free space."""
    match q:
        case TrueFalseQuestion():
            return _checkboxes(["True", "False"])
        case MultipleChoiceQuestion():
            return _checkboxes([md_to_tex(c.text).strip() for c in q.choices])
        case ShortAnswerQuestion():
            return " {\\Large\\underline{\\hspace{5cm}}} " + md_to_tex(q.after_text).strip()
    return ANSWER_SPACE
