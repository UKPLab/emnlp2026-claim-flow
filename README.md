# HypoFlow

HypoFlow is a pipeline for building a hypothesis-centric view of NLP literature. It ingests ACL Anthology papers, extracts structured sections, uses an LLM to pull out hypotheses with supporting evidence, builds a citation graph (with contexts), and optionally links hypotheses across citing/cited papers.

## What it does
- Downloads ACL Anthology metadata into DuckDB.
- Fetches PDFs and stores them on disk.
- Parses PDFs (Docling) to capture abstract/introduction/conclusion text.
- Extracts hypotheses and evidence contexts with Azure OpenAI.
- Builds a citation graph from Semantic Scholar (contexts + intents).
- Links hypotheses across citations with LLM classification.

## Requirements
- Python 3.10+
- DuckDB, Docling, and the dependencies in `pyproject.toml`
- Azure OpenAI credentials for hypothesis extraction and linking
- Semantic Scholar API key for citation graph building

## Install
Use `uv` (recommended) or `pip`.

```bash
uv sync
```

```bash
pip install -e .
```

## Configuration
Create a `.env` file in the repo root (or export these vars):

```bash
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-10-21
S2_API_KEY=...
```

Only `S2_API_KEY` is required for citation crawling; the Azure settings are required for hypothesis extraction/linking.

## Pipeline usage
The CLI entry points are defined in `pyproject.toml`. The examples below use `uv run`, but the equivalent is `python -m scripts.<name>`.

1) Download ACL metadata (writes to `db/aclanthology.duckdb`):

```bash
uv run get_meta --max-papers 1000 --venues "acl,emnlp"
```

2) Download PDFs (writes to `data/aclanthology/...` and updates `papers` table):

```bash
uv run get_papers --start 2018 --end 2024 --max-papers 200 --workers 8
```

3) Parse PDFs with Docling (writes to `processed` table):

```bash
uv run parse_papers --workers 4 --docling-threads 2 --mode patch
```

4) Extract hypotheses with Azure OpenAI (writes to `hypotheses` table):

```bash
uv run get_hypotheses
```

5) Build citation graph with Semantic Scholar (writes to `citations` table):

```bash
uv run get_citations
```

6) (Optional) Link hypotheses across citations:

```bash
python -m hypoflow.link_hypotheses
```

## Data layout
- `db/aclanthology.duckdb`: primary datastore.
- `data/aclanthology/`: PDF archive (organized by year/venue).

Key tables in DuckDB:
- `meta`: ACL metadata (title, authors, year, pdf_url, venue, etc.).
- `papers`: downloaded PDF records (status, sha1, save_path).
- `processed`: extracted sections per paper.
- `hypotheses`: LLM-extracted hypotheses + evidence.
- `citations` and `citation_status`: citation graph + crawl state.
- `hypotheses_links`: LLM-labeled relations between citing/cited hypotheses.

## Analysis
The `analysis/` folder contains scripts used for research questions and summary stats. Example:

```bash
python analysis/rqs/q1_hypotheses_per_paper_over_time.py --input path/to/hypotheses.jsonl --out analysis/plots/q1_hypotheses_over_time.pdf
```

## Notes
- `parse_papers` defaults to patch mode and only processes papers missing from `processed`.
- The citation crawler is rate-limited to respect Semantic Scholar limits.
- If you hit LLM content filters during extraction/linking, the offending paper is skipped.
