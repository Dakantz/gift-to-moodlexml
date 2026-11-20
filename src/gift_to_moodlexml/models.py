"""Question object hierarchy produced by the parser and consumed by the writers."""

import re
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Category:
    name: str


@dataclass(kw_only=True)
class Question:
    """Base question; on its own it is an open (essay) question."""

    text: str
    format: str = "markdown"
    points: int | None = None  # explicit `points=` param, else `default_points`
    disabled: bool = False

    moodle_type: ClassVar[str] = "essay"
    default_points: ClassVar[int] = 3

    @property
    def score(self) -> int:
        return self.points if self.points is not None else self.default_points

    @property
    def title(self) -> str:
        return re.sub(r"[#<>]", "", self.text.split("\n")[0]).strip()[:50]


class EssayQuestion(Question):
    pass


@dataclass(kw_only=True)
class TrueFalseQuestion(Question):
    answer: bool
    moodle_type: ClassVar[str] = "multichoice"
    default_points: ClassVar[int] = 1


@dataclass
class Choice:
    text: str
    correct: bool
    fraction: str | None = None  # `%n%` override for wrong answers

    @property
    def moodle_fraction(self) -> str:
        if self.correct:
            return "100"
        return self.fraction if self.fraction is not None else "-50"


@dataclass(kw_only=True)
class MultipleChoiceQuestion(Question):
    choices: list[Choice] = field(default_factory=list)
    moodle_type: ClassVar[str] = "multichoice"
    default_points: ClassVar[int] = 2

    @property
    def single(self) -> bool:
        return any(c.correct for c in self.choices)


@dataclass(kw_only=True)
class ShortAnswerQuestion(Question):
    """Fill-the-blank: `text {=answer} after_text`."""

    answers: list[str] = field(default_factory=list)
    after_text: str = ""
    moodle_type: ClassVar[str] = "shortanswer"
    default_points: ClassVar[int] = 2


Item = Category | Question
