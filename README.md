<!-- <p align="center">
  <img src='logo.png' width='200'>
</p> -->

# Claimflow

> <span style="color: red"><strong>Under development:</strong></span> This repository is still under active development.
<!-- [![Arxiv](https://img.shields.io/badge/Arxiv-YYMM.NNNNN-red?style=flat-square&logo=arxiv&logoColor=white)](https://put-here-your-paper.com)
[![License](https://img.shields.io/github/license/OWNER/claimflow)](https://opensource.org/licenses/Apache-2.0)
[![Python Versions](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://github.com/UKPLab/arxiv2026-claim-flow/actions/workflows/main.yml/badge.svg)](https://github.com/UKPLab/arxiv2026-claim-flow/actions/workflows/main.yml) -->

ClaimFlow is a pipeline for building a claim-centric view of NLP literature. It ingests ACL Anthology papers, extracts sections, uses an LLM-based framework to extract claims with evidence, builds a citation graph, and can link claims across citing/cited papers.

> **Abstract:** Scientific papers do more than report results -- they advance _claims_ that later work supports, extends, or sometimes refutes. Yet existing methods for citation and claim analysis capture only fragments of this dialogue, obscuring how scientific claims interact over time. In this work, we make these interactions explicit at the level of individual scientific claims. We introduce `ClaimFlow`, a claim-centric view of the NLP literature, built from $304$ ACL Anthology papers (1979--2025) that are manually annotated with $1{,}084$ claims and $832$ cross-paper claim relations, indicating whether a citing paper _supports_, _extends_, _qualifies_, _refutes_, or references a claim as _background_. Using `ClaimFlow`, we define a new task -- _Claim Relation Classification_ -- which requires models to infer the scientific stance toward a cited claim from its text and citation context. 
We present our experimental results for this task and apply our model to $\sim$$13k$ NLP papers to analyze how claims evolve across decades of NLP research. Our analysis reveals that $63.5\%$ claims are never reused; only $11.1\%$ are ever challenged, and such challenges are typically short-lived, and widely propagated claims are more often _reshaped_ through qualification and extension than confirmed or refuted. Overall `ClaimFlow` offers a lens for examining how ideas shift and mature within NLP, and a foundation for assessing whether models can interpret scientific argumentation.

Contact person: [Aniket Pramanick](mailto:aniketpramanick26@gmail.com)

<!-- [Project page](https://REPLACE_ME.com) | [Organization](https://REPLACE_ME.com) -->

Don't hesitate to send us an e-mail or report an issue if something is broken (and it shouldn't be) or if you have further questions.


## Getting Started

1. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Or with `uv`:
```bash
uv sync
```

2. Configure required environment variables (create a `.env` file or export them):
```bash
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=...
AZURE_OPENAI_API_VERSION=...
S2_API_KEY=...
```

3. Run the pipeline end-to-end (example):
```bash
uv run get_meta --max-papers 1000 --venues "acl,emnlp"
uv run get_papers --start 2018 --end 2024 --max-papers 200 --workers 8
uv run parse_papers --workers 4 --docling-threads 2 --mode patch
uv run get_claims
uv run get_citations
python -m claimflow.link_claimstheses
```

## Usage

### Using the classes

To import classes/methods of `claimflow` from inside the package itself you can use relative imports:

```py
from .process_papers import ingest_papers

ingest_papers()
```

To import classes/methods from outside the package (e.g. when you want to use the package in some other project) you can instead refer to the package name:

```py
from claimflow.process_papers import ingest_papers

ingest_papers()
```

### Using scripts

This is how you can use `claimflow` from the command line:

```bash
uv run get_meta
uv run get_papers
uv run parse_papers
uv run get_claims
uv run get_citations
```

### Expected results

After running the pipeline, you should expect:
- A DuckDB database at `db/aclanthology.duckdb` with `meta`, `papers`, `processed`, `claims`, `citations`, and `claim_links` tables.
- Downloaded PDFs under `data/aclanthology/<year>/<venue>/<paper_id>.pdf`.
- Processed section text stored in `processed.processed` as JSON.

### Parameter description

* `--max-papers`: Limit the number of records downloaded or processed.
* `--start`, `--end`: Filter paper years for PDF downloads.
* `--workers`: Number of concurrent workers for PDF downloads or parsing.
* `--docling-threads`: Threads per Docling converter worker.
* `--mode`: `patch` to process only missing papers, `full` to reprocess all.
* `--venues`: Comma-separated ACL venue slugs (e.g., `acl,emnlp`).
* `--db-path`: Path to the DuckDB database file.

## Development

Install dev dependencies and run your tooling of choice (ruff/mypy/pytest):

```bash
uv sync --dev
```

<!-- ## Cite

Please use the following citation:

```
@InProceedings{smith:20xx:CONFERENCE_TITLE,
  author    = {Smith, John},
  title     = {My Paper Title},
  booktitle = {Proceedings of the 20XX Conference on XXXX},
  month     = mmm,
  year      = {20xx},
  address   = {Gotham City, USA},
  publisher = {Association for XXX},
  pages     = {XXXX--XXXX},
  url       = {http://xxxx.xxx}
}
``` -->

## Disclaimer

> This repository contains experimental software and is published for the sole purpose of giving additional background details on the respective publication.
