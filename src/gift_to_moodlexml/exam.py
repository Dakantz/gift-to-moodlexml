"""Sample questions per section and render a paper exam from a chevron template.

Templates use `[[ ]]` delimiters and get:
  id, points, categories: [{name, points, questions: [{text, points, tex_text, choice_text}]}]
"""

import random
from dataclasses import dataclass, field

import chevron

from .models import Question
from .tex import answer_tex, question_tex


@dataclass
class Section:
    """An exam section drawing `n_questions` from the pooled GIFT `categories`."""

    name: str
    categories: list[str] = field(default_factory=list)
    n_questions: int = 1


@dataclass
class SampledSection:
    name: str
    questions: list[Question]

    @property
    def points(self) -> int:
        return sum(q.score for q in self.questions)


def sample_exam(
    groups: dict[str, list[Question]], sections: list[Section], seed: int = 42
) -> list[SampledSection]:
    rand = random.Random(seed)
    sampled = []
    for s in sections:
        pool = [q for c in s.categories for q in groups.get(c, [])]
        sampled.append(
            SampledSection(s.name, rand.sample(pool, min(s.n_questions, len(pool))))
        )
    return sampled


def _context(name: str, questions: list[Question]) -> dict:
    return {
        "name": name,
        "points": sum(q.score for q in questions),
        "questions": [
            {
                "text": q.text,
                "points": q.score,
                "tex_text": question_tex(q),
                "choice_text": answer_tex(q),
            }
            for q in questions
        ],
    }


def render_exam(template: str, sections: list[SampledSection], exam_id=0) -> str:
    cats = [_context(s.name, s.questions) for s in sections]
    return chevron.render(
        template,
        {"categories": cats, "id": exam_id, "points": sum(c["points"] for c in cats)},
        def_ldel="[[",
        def_rdel="]]",
    )


def render_catalogue(template: str, groups: dict[str, list[Question]]) -> str:
    """Render every question, grouped by GIFT category (no sampling)."""
    return render_exam(
        template, [SampledSection(n, qs) for n, qs in groups.items()], exam_id=""
    )
