"""Extended GIFT -> Moodle XML / LaTeX exams."""

from .exam import SampledSection, Section, render_catalogue, render_exam, sample_exam
from .models import (
    Category,
    Choice,
    EssayQuestion,
    MultipleChoiceQuestion,
    Question,
    ShortAnswerQuestion,
    TrueFalseQuestion,
)
from .moodle import question_to_xml, to_moodle_xml
from .parse import group_by_category, load_gift_files, parse_block, parse_gift, split_blocks
from .tex import answer_tex, question_tex


def generate_xml_from_gift(
    gift_content: str, output_file: str | None = "quiz.xml", recombine: bool = False
):
    return to_moodle_xml(parse_gift(gift_content, recombine), output_file)


def generate_xml_from_questions(
    gift_questions: list[str], output_file: str | None = "quiz.xml"
):
    return to_moodle_xml([i for q in gift_questions for i in parse_block(q)], output_file)
