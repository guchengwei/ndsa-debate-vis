# NDSA Debate Visualization

![NDSA Debate Visualization — See the reasoning inside the debate](docs/og.png)

NDSA Debate Visualization is a research prototype for exploring conflicting claims as structured arguments. It is based on Chengwei Gu’s 2021 JAIST master’s thesis, [*An Argumentation-Based Framework for Practical Reasoning*](https://dspace.jaist.ac.jp/dspace/bitstream/10119/17162/11/paper.pdf).

The project presents several complementary explanations:

- an **argument relation graph** showing arguments and attack relations;
- a **dialogical explanation** represented as a dispute tree;
- a **logical explanation** based on stored premise sets;
- a **natural-language outline** of the selected derivation.

[Open the interactive GitHub Pages demo](https://guchengwei.github.io/ndsa-debate-vis/) · [Read the thesis](https://dspace.jaist.ac.jp/dspace/bitstream/10119/17162/11/paper.pdf)

## Static GitHub Pages demo

The browser demo under [`docs/`](docs/) is a dependency-free static application. It uses plain HTML, CSS, JavaScript, and SVG, so it can run directly on GitHub Pages without Dash, Flask, or another server.

The first vertical slice exports the original default contested claim (`~a>~d`) from the cached research data. Selecting an argument updates its dispute tree, premise alternatives, and readable derivation outline.

The deployment boundary is intentionally small:

```text
cached Python research output
            │
            ▼
scripts/export_static.py
            │
            ▼
       docs/data.json
            │
            ▼
HTML + CSS + JavaScript + SVG
```

Regenerate the static data after changing the cache or knowledge base:

```bash
python scripts/export_static.py
```

To publish it, configure **Settings → Pages** to deploy the default branch from the `/docs` directory. Relative asset paths make the site work under the repository subpath.

## Prototype status

This repository contains research-prototype code, not a verified production application. The historical Dash deployment is no longer available, and the current `app.py` is incomplete. The Python argumentation and natural-deduction code remains the source of truth for formal reasoning; the Pages demo presents a precomputed, inspectable slice of that output.

## Repository structure

```text
.
├── app.py                  Legacy Dash interface
├── argument_engine/        Argument and natural-deduction engine
├── data/                   Knowledge base and cached intermediate data
├── docs/
│   ├── index.html          GitHub Pages application
│   ├── styles.css
│   ├── app.js
│   └── data.json           Precomputed browser data
└── scripts/
    └── export_static.py    Cache-to-JSON compiler
```

## Legacy local runtime

The legacy Python application targets Python 3.10 and the pinned dependencies in [`requirements.txt`](requirements.txt):

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

That runtime is preserved for research reference but is not required by the GitHub Pages demo.

## License

This project is available under the [MIT License](LICENSE).
