"""pyparsing grammar for one (extended) GIFT block."""

from pyparsing import (
    Combine,
    DelimitedList,
    FollowedBy,
    Group,
    LineEnd,
    Literal,
    OneOrMore,
    Optional,
    Regex,
    SkipTo,
    StringEnd,
    Suppress,
    Word,
    alphanums,
    nums,
    restOfLine,
)


def build_grammar():
    LBRACE, RBRACE = Suppress("{"), Suppress("}")

    params = (
        Suppress("[")
        + DelimitedList(
            Word(alphanums + "_-")("format") ^ (Literal("points=") + Word(nums)("points"))
        )("params")
        + Suppress("]")
    )

    text_line = Combine(
        OneOrMore(Word(alphanums + " *_-\\.:?!+=<>(),@\"'/;[]#<>") | Word("`", exact=1))
    )
    code_block = Combine(Literal("```") + SkipTo("```") + Literal("```"))
    # code blocks are consumed whole so their { } never reach the answer parser
    text = OneOrMore(code_block | text_line).set_parse_action(lambda t: "\n".join(t))(
        "text"
    )

    category = Group(Suppress("$CATEGORY:") + restOfLine("name"))("category")

    tf_answer = (Literal("T") | Literal("F") | Literal("TRUE") | Literal("FALSE"))(
        "tf_value"
    )
    fraction = Optional(
        Suppress("%") + Regex(r"-?\d+(\.\d+)?")("fraction") + Suppress("%"), None
    )
    choice = Group(
        (Literal("~") | Literal("="))("is_correct")
        + fraction
        + SkipTo(LineEnd() | RBRACE)("choice_text")
    )
    answer_block = (
        LBRACE
        + (tf_answer | OneOrMore(choice)("choices"))
        + RBRACE
        + Optional(SkipTo(StringEnd()), None)("after_text")
    )
    essay_block = (Literal("{") + Literal("}") + StringEnd())("essay_answer")

    question = Group(params + text + (essay_block | answer_block))("question")
    return OneOrMore(category ^ question)


GRAMMAR = build_grammar()
