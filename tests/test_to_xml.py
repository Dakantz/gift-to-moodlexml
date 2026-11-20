import gift_to_moodlexml as g


def test_xml(items, tmp_path):
    out = tmp_path / "quiz.xml"
    root = g.to_moodle_xml(items, str(out)).getroot()
    assert out.exists()
    qs = root.findall("question")
    types = [q.get("type") for q in qs]
    assert types.count("multichoice") == 2
    assert "shortanswer" in types and "essay" in types
    assert "$course$/top/Facts/shortanswer" in [c.text for c in root.iter("text")]


def test_multichoice_xml(items):
    el = g.question_to_xml(items[3])
    assert [a.get("fraction") for a in el.findall("answer")] == ["-50", "100", "-25"]
    assert el.find("single") is None
    assert el.findtext("defaultgrade") == "2"
    assert "<code>" in el.findtext("questiontext/text")


def test_true_false_xml(items):
    el = g.question_to_xml(items[2])
    assert [(a.findtext("text"), a.get("fraction")) for a in el.findall("answer")] == [
        ("True", "100"),
        ("False", "-100"),
    ]


def test_image_inlined(items, monkeypatch):
    monkeypatch.chdir(__import__("pathlib").Path(__file__).parent.parent)
    html = g.question_to_xml(items[5]).findtext("questiontext/text")
    assert "data:image/png;base64," in html


def test_legacy_api():
    tree = g.generate_xml_from_questions(["$CATEGORY: X", "[markdown]\nQ? {F}"], None)
    assert len(tree.getroot().findall("question")) == 3
