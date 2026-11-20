# gift-to-moodlexml
Creating Moodle XML Questions from extended GIFT format

## Features

* Parse GIFT files more robustly compared to moodle
* Supports full markdown syntax (incl. Code highlighting!)
* Points are automatically inferred OR can be set!
  - Deducts -50% for single choice, -100% for T/F question
* Supports:
 - True/False Question (will be converted to Multichoice to allow point deduction)
 - Multichoice
 - Single Choice
 - Fill-the Blank



## Install

```
pip install gift-to-moodlexml
```

## Usage

Assume you have some (extended) GIFT file:

```md
$CATEGORY: OOP2/Intro

[markdown]Java supports use of `varargs` (variable arguments) for parameter passing {T}

[markdown] What pattern does this Code use?
`Logger logger=Logger.getInstance();`
{
    ~ Factory
    ~ Configurator
    = Singleton
    ~ Generics
    ~ Builder
    ~ Creator
    ~ Observer
}
```
Then you can parse it to an XML to upload to moodle:

```python
from pathlib import Path
import gift_to_moodlexml as g

# recombine=True (default for files): blank lines inside a question are kept,
# a new question only starts at a `[params]` line
items = g.load_gift_files(sorted(Path("./").glob("*.gift")))
g.to_moodle_xml(items, output_file="quiz_package.xml")
```

### Paper exams (LaTeX via pandoc)

```python
groups = g.group_by_category(items)
sections = [g.Section("Maps", ["VA/Maps"]), g.Section("Time Series", ["VA/Time Series/Hard"], n_questions=2)]
tex = g.render_exam(Path("exam_template.tex").read_text(), g.sample_exam(groups, sections, seed=0), exam_id=0)
```

Assumes you have a template like
```tex
% exam_template.tex
% ... some document
[[#categories]]
\section{Category: [[name]]}
% Total points: [[points]]
[[#questions]]
[[tex_text]]
[[choice_text]]
\par
\emph{Max. Points: [[points]]}
[[/questions]]
[[/categories]]
% ... some document
```

Code blocks are emitted with pandoc's `Shaded`/`Highlighting` macros, so the
template must define them (e.g. copy from `pandoc -D latex`).

## Development

```
uv sync
uv run pytest
```
