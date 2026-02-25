import xml.etree.ElementTree as ET
import os
from pathlib import Path
from lxml import etree
import markdown
import re

from pyparsing import (
    SkipTo,
    nested_expr,
    Literal,
    OneOrMore,
    Optional,
    Suppress,
    Group,
    alphanums,
    alphas,
    Word,
    DelimitedList,
    LineStart,
    LineEnd,
    StringEnd,
    restOfLine,
    CharsNotIn,
    FollowedBy,
    Regex,
    nums,
    ZeroOrMore,
    Combine,
    Or,
)
import markdown


def get_parsing_grammar():
    # Basic characters and symbols
    # Created using https://gemini.google.com/share/3d1e0e8a7779
    LBRACE = Suppress("{")
    RBRACE = Suppress("}")
    LSQBRACKET = Suppress("[")
    RSQBRACKET = Suppress("]")
    TILDE = Literal("~")
    EQUAL = Literal("=")

    q_format_expr = (
        LSQBRACKET
        + DelimitedList(
            Word(alphanums + "_-")("format")
            ^ (Literal("points=") + Word(nums)("points"))
        )("params")
        + RSQBRACKET
    )

    question_text_format = Combine(
        OneOrMore(Word(alphanums + " *_-\\.:?!+=<>(),@\"'/;") | Word("`", exact=1))
    )

    CODE_BLOCK = Combine(Literal("```") + SkipTo("```") + Literal("```"))

    # 3. Question Text is now a mix of plain text and code blocks
    # This explicitly consumes code blocks so the { } inside them aren't seen by the answer parser
    question_content = (
        OneOrMore(CODE_BLOCK | question_text_format)
        .setResultsName("text")
        .setParseAction(lambda t: " ".join(t))
    )

    category = Group(Suppress("$CATEGORY:") + restOfLine("name"))("category")

    answer_start_marker = FollowedBy(
        Literal("{") + (Literal("~") | Literal("=") | Regex(r"[TF]") | Literal("}"))
    )
    question_text = question_content("text")

    tf_answer = (Literal("T") | Literal("F") | Literal("TRUE") | Literal("FALSE"))(
        "tf_value"
    )
    fraction = Optional(
        Suppress("%") + Regex(r"-?\d+(\.\d+)?")("fraction") + Suppress("%"), None
    )
    # Multiple Choice / Multiple Response
    # Handles ~Incorrect and =Correct
    choice = Group(
        (TILDE | EQUAL)("is_correct")
        + fraction
        + SkipTo(LineEnd() | RBRACE)("choice_text")
    )
    mc_answer = OneOrMore(choice)("choices")

    # Combined Answer Block
    answer_block = (
        LBRACE
        + (tf_answer | mc_answer)
        + RBRACE
        + Optional(SkipTo(StringEnd()), None)("after_text")
    )
    essay_block = (Literal("{") + Literal("}") + StringEnd())("essay_answer")

    question = category ^ Group(
        q_format_expr + question_text + answer_block | essay_block
    )("question")
    essay_question = category ^ Group(q_format_expr + question_text + essay_block)(
        "question"
    )
    gift_parser = OneOrMore(question)
    gift_parser_essay = OneOrMore(essay_question)
    return gift_parser, gift_parser_essay


def parse_question_block(question_block: str):
    gift_parser, gift_parser_essay = get_parsing_grammar()
    try:
        parsed_question = gift_parser.parseString(question_block)
        return parsed_question
    except Exception as e:
        print(f"Error parsing question: {e}")
        print("Trying essay parser...")
        try:
            parsed_question = gift_parser_essay.parseString(question_block)
            return parsed_question
        except Exception as e2:
            print(f"Error parsing essay question: {e2}")
            print(f"Question content:\n{question_block}\n")
            return None


def parse_all_questions(gift_content: str):
    gift_parser, gift_parser_essay = get_parsing_grammar()
    # Split the content into question blocks based on blank lines
    all_question_strs = gift_content.strip().split("\n\n")

    all_questions = []
    for question_str in all_question_strs:
        parsed_question = parse_question_block(question_str)
        if parsed_question is not None:
            all_questions.append(parsed_question)
    return all_questions


def generate_xml_from_parsed_gift(
    parsed_questions: list[dict], output_file: str | None = "quiz.xml"
):
    quiz = etree.Element("quiz")
    last_category = None

    def add_category(cat_name: str):
        cat_q = etree.Element("question")
        cat_q.set("type", "category")
        cat_q_text = etree.Element("category")
        cat_q_text_text = etree.Element("text")
        cat_q_text_text.text = f"$course$/top/{cat_name.strip()}"
        cat_q_text.append(cat_q_text_text)
        cat_q.append(cat_q_text)
        quiz.append(cat_q)

    for pq in parsed_questions:
        pq_d = pq.as_dict()
        if "category" in pq_d:
            last_category = pq_d["category"]["name"]
            add_category(last_category)
            continue

        question = etree.Element("question")
        if "question" not in pq_d:
            continue
        format = (
            pq_d["question"]["format"] if "format" in pq_d["question"] else "markdown"
        )
        if "params" in pq_d["question"] and "disable" in pq_d["question"]["params"]:
            continue
        q_cat = "essay"
        q_text: str = pq_d["question"]["text"]
        inferred_points = 1
        single_choice = False
        if "choices" in pq_d["question"]:
            q_cat = "multichoice"
            choices = pq_d["question"]["choices"]
            inferred_points = 2
            if len(choices) == 0:
                q_cat = "essay"
                inferred_points = 3
            elif all(c["is_correct"] == "=" for c in choices):
                q_cat = "shortanswer"
                if (
                    pq_d["question"]["after_text"] is not None
                    and len(pq_d["question"]["after_text"].strip()) > 0
                ):
                    q_text += " `________` " + pq_d["question"]["after_text"]
                    inferred_points = 2
            for choice in choices:
                answer = etree.Element("answer")
                answer.set("format", format)
                if choice["is_correct"] == "=":
                    answer.set("fraction", "100")
                    single_choice = True
                else:
                    if "fraction" in choice and choice["fraction"] is not None:
                        answer.set("fraction", choice["fraction"])
                    else:
                        answer.set("fraction", "-50")

                answer_text = etree.Element("text")
                answer_text.text = choice["choice_text"].strip()
                answer.append(answer_text)
                question.append(answer)
        elif "tf_value" in pq_d["question"]:
            q_cat = "multichoice"
            inferred_points = 1
            mult = 1 if pq_d["question"]["tf_value"] in ["T", "TRUE"] else -1
            single_choice = True
            for opt, frac in (("True", 100), ("False", -100)):
                answer = etree.Element("answer")
                answer.set("format", format)
                answer_text = etree.Element("text")
                answer_text.text = opt
                answer.set("fraction", str(frac * mult))
                answer.append(answer_text)
                question.append(answer)
        else:
            inferred_points = 3
        question.set("type", q_cat)

        q_text_el = etree.Element("name")
        q_text_name = etree.Element("text")

        q_text_name.text = q_text.split("\n")[0][:50]
        q_text_el.append(q_text_name)
        question.append(q_text_el)
        q_text = re.sub(
            r"(```(\w+)?)", lambda m: f"\n{m.group(0)}\n", q_text, flags=re.DOTALL
        )
        q_text_el = etree.Element("questiontext")
        if format == "markdown":
            q_text = markdown.markdown(q_text, extensions=["extra"])
            format = "html"
        if q_cat == "multichoice" and not single_choice:
            q_singlechoice = etree.Element("single")
            q_singlechoice.text = "false"
            question.append(q_singlechoice)
        q_text_el.set("format", format)
        q_text_text = etree.Element("text")
        # set correct CDATA section
        q_text_text.text = etree.CDATA(q_text)
        q_text_el.append(q_text_text)
        question.append(q_text_el)

        quiz_points = etree.Element("defaultgrade")
        if "points" in pq_d["question"]:
            inferred_points = int(pq_d["question"]["points"])
        quiz_points.text = str(inferred_points)

        question.append(quiz_points)
        tags = [f"cat={q_cat}", "points=" + str(inferred_points)]
        q_tags = etree.Element("tags")
        for tag in tags:
            q_tag = etree.Element("tag")
            q_tag_text = etree.Element("text")
            q_tag_text.text = tag
            q_tag.append(q_tag_text)
            q_tags.append(q_tag)
        question.append(q_tags)
        use_case = etree.Element("usecase")
        use_case.text = "0"
        question.append(use_case)
        add_category(f"{last_category}/{q_cat}")
        quiz.append(question)
    tree = etree.ElementTree(quiz)
    etree.indent(tree, space="  ", level=0)
    if output_file is not None:
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
    return tree


def generate_xml_from_gift(gift_content: str, output_file: str | None = "quiz.xml"):
    parsed_questions = parse_all_questions(gift_content)
    return generate_xml_from_parsed_gift(parsed_questions, output_file)


def generate_xml_from_questions(
    gift_questions: list[str], output_file: str | None = "quiz.xml"
):
    parsed_questions = []
    for q in gift_questions:
        parsed_q = parse_question_block(q)
        if parsed_q is not None:
            parsed_questions.append(parsed_q)

    return generate_xml_from_parsed_gift(parsed_questions, output_file)
