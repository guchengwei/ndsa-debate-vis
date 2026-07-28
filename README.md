# NDSA Debate Visualization

![NDSA Debate Visualization — See the reasoning inside the debate](docs/og.png)

NDSA Debate Visualization is a research prototype for exploring conflicting claims as structured arguments. It is based on Chengwei Gu’s 2021 JAIST master’s thesis, [*An Argumentation-Based Framework for Practical Reasoning*](https://dspace.jaist.ac.jp/dspace/bitstream/10119/17162/11/paper.pdf).

The proposed system turns a propositional-logic knowledge base into several complementary explanations:

- an **argument relation graph** showing arguments and attack relations;
- a **dialogical explanation** represented as a dispute tree;
- a **logical explanation** that derives a claim from its premises using natural deduction;
- a **natural-language explanation** of the proof.

[View the project introduction](https://guchengwei.github.io/ndsa-debate-vis/) · [Read the thesis](https://dspace.jaist.ac.jp/dspace/bitstream/10119/17162/11/paper.pdf)

## Prototype status

This repository contains research-prototype code, not a verified production application. The historical deployment is no longer available, and the current runtime and legacy deployment configuration have not been independently validated. Expect defects, outdated assumptions, and environment-specific paths.

The landing page under [`docs/`](docs/) is a static introduction to the research. It does not run or validate the Python application.

## Research use case

The thesis evaluates the method with a fragment of the second 2020 U.S. presidential debate. Statements from Donald Trump and Joe Biden are annotated as propositions, rules, and conclusions in [`data/debate_kb.csv`](data/debate_kb.csv). The example demonstrates how an inconsistent knowledge base can preserve disagreement while still supporting explicit reasoning.

## Repository structure

```text
.
├── app.py                  Dash interface and callbacks
├── argument_engine/
│   ├── argument.py         Argument construction, attacks, and extensions
│   ├── natural_deduction.py
│   ├── nd_formula.py
│   ├── nd_lookups.py
│   ├── nd_rules.py
│   └── tableaux.py
├── assets/                 Dash styles and client-side helpers
├── data/                   Debate knowledge base and cached intermediate data
└── docs/                   Static GitHub Pages introduction
```

## Technology

- Python 3.10
- Dash and Flask
- Plotly
- NetworkX and igraph
- pandas

Pinned package versions are listed in [`requirements.txt`](requirements.txt).

## Local exploration

The following is the repository’s intended local setup, not a verified installation recipe:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Before relying on the output, review the source for machine-specific paths and test the reasoning engine against known cases. In particular, deployment files and cached-data paths may require repair for a new environment.

## GitHub Pages

The landing page is exported to [`docs/`](docs/). To host it through GitHub Pages:

1. Open the repository’s **Settings → Pages**.
2. Choose **Deploy from a branch**.
3. Select the default branch and the `/docs` folder.

The static page is independent of the Python runtime.

## License

This project is available under the [MIT License](LICENSE).
