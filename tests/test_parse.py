import gift_to_moodlexml as g
from gift_to_moodlexml.models import (
    Category,
    EssayQuestion,
    MultipleChoiceQuestion,
    ShortAnswerQuestion,
    TrueFalseQuestion,
)


def test_types(items):
    assert [type(i) for i in items] == [
        Category,
        ShortAnswerQuestion,
        TrueFalseQuestion,
        MultipleChoiceQuestion,
        Category,
        EssayQuestion,
        TrueFalseQuestion,
    ]
    assert items[0].name == "Facts"


def test_short_answer(items):
    q = items[1]
    assert q.answers == ["Alexander Van der Bellen"]
    assert q.after_text == "."
    assert q.score == 4


def test_choices(items):
    q = items[3]
    assert [(c.text, c.correct, c.moodle_fraction) for c in q.choices] == [
        ("Factory", False, "-50"),
        ("Singleton", True, "100"),
        ("Builder", False, "-25"),
    ]
    assert q.single and q.score == 2


def test_inferred_points_and_disable(items):
    assert items[2].score == 1 and items[2].answer is True
    assert items[6].disabled


def test_recombine_keeps_blank_lines_in_question():
    text = "[markdown]\nIntro\n\n![img](x.png)\n\n{}"
    assert g.split_blocks(text) == ["[markdown]\nIntro", "![img](x.png)", "{}"]
    assert g.split_blocks(text, recombine=True) == [text]
    assert isinstance(g.parse_gift(text, recombine=True)[0], EssayQuestion)


def test_category_with_question_in_same_block():
    blocks = g.split_blocks("$CATEGORY: A\n[markdown]\nQ {T}", recombine=True)
    assert blocks == ["$CATEGORY: A", "[markdown]\nQ {T}"]


def test_invalid_block_is_skipped():
    assert g.parse_block("not gift at all {") == []


def test_group_by_category(items):
    groups = g.group_by_category(items)
    assert list(groups) == ["Facts", "Open/Images"]
    assert len(groups["Facts"]) == 3 and len(groups["Open/Images"]) == 1
