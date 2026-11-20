import gift_to_moodlexml as g

TEMPLATE = "[[#categories]]\\section{[[name]] ([[points]])}\n[[#questions]][[&tex_text]][[&choice_text]]\n[[/questions]][[/categories]]"


def test_question_tex(items):
    assert "\\subsection{UMAP}" in g.question_tex(items[5])
    assert "\\texttt{varargs}" in g.question_tex(items[2])


def test_answer_tex(items):
    assert "\\underline" in g.answer_tex(items[1])
    assert g.answer_tex(items[3]).count("\\item[$\\square$]") == 3
    assert "True" in g.answer_tex(items[2])
    assert g.answer_tex(items[5]) == g.tex.ANSWER_SPACE


def test_sample_and_render(items):
    groups = g.group_by_category(items)
    sections = [g.Section("Facts", ["Facts"], 2), g.Section("Open", ["Open/Images"])]
    sampled = g.sample_exam(groups, sections, seed=1)
    assert [len(s.questions) for s in sampled] == [2, 1]
    assert g.sample_exam(groups, sections, seed=1) == sampled
    tex = g.render_exam(TEMPLATE, sampled, exam_id=1)
    assert "\\section{Facts (" in tex and "\\section{Open (3)}" in tex


def test_render_catalogue(items):
    tex = g.render_catalogue(TEMPLATE, g.group_by_category(items))
    assert "\\section{Facts (7)}" in tex
