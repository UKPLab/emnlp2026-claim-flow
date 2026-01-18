import math
import json
import duckdb
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict

from typing import Dict, List, Any, Iterable, Tuple

try:
    from rich.console import Console
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )

    _RICH_AVAILABLE = True
except Exception:
    Console = None  # type: ignore[assignment,misc]
    Progress = None  # type: ignore[assignment,misc]
    _RICH_AVAILABLE = False

@dataclass
class ExportConfig:
    duckdb_path: Path
    out_dir: Path
    shard_size: int 
    compress: bool
    include_papers_with_no_links: bool
    sort_by: str
    indent: int | None = None

def _normalize_citation_contexts(value: Any) -> List[Any]:
    """
    citations.citation_contexts might be:
        - DuckDB LIST (already a Python list)
        - JSON string (e.g., '["...", "..."]')
        - plain string (single context)
        - NULL
    Return a list.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        # try JSON
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except Exception:
            return [value]
    # fallback
    return [value]

def _json_loads_maybe(s: str) -> Any:
    try:
        return json.loads(s)
    except Exception:
        return None

def _ensure_authors_list(authors: Any) -> List[str]:
    """
    Normalize `authors` to a JSON-serializable `List[str]`.

    The DB typically stores authors as a JSON array serialized to text. DuckDB
    may return that as `str`, so we parse when possible.
    """
    if authors is None:
        return []

    if isinstance(authors, list):
        return [str(a) for a in authors if a is not None and str(a).strip()]

    if isinstance(authors, str):
        s = authors.strip()
        if not s:
            return []

        parsed = _json_loads_maybe(s) if s[:1] in "[{" else None
        if isinstance(parsed, list):
            return [str(a) for a in parsed if a is not None and str(a).strip()]
        if isinstance(parsed, str):
            return [parsed] if parsed.strip() else []

        # Fallback: preserve the raw string as a single author entry.
        return [s]

    return [str(authors)] if str(authors).strip() else []

def _ensure_evidence_list_of_dicts(evidence: Any) -> List[Dict[str, Any]]:
    """
    Normalize hypothesis `evidence` to `List[Dict[str, Any]]`.

    Evidence is usually stored as a JSON array serialized to text. If a malformed
    value is encountered, we preserve it as a single dict with a `context` field.
    """
    if evidence is None:
        return []

    if isinstance(evidence, list):
        items = evidence
    elif isinstance(evidence, dict):
        items = [evidence]
    elif isinstance(evidence, str):
        s = evidence.strip()
        if not s:
            return []
        parsed = _json_loads_maybe(s) if s[:1] in "[{" else None
        if isinstance(parsed, list):
            items = parsed
        elif isinstance(parsed, dict):
            items = [parsed]
        else:
            items = [s]
    else:
        items = [evidence]

    out: List[Dict[str, Any]] = []
    for item in items:
        if item is None:
            continue
        if isinstance(item, dict):
            out.append(item)
        elif isinstance(item, str):
            txt = item.strip()
            if txt:
                out.append({"context": txt})
        else:
            txt = str(item).strip()
            if txt:
                out.append({"context": txt})
    return out

def _ensure_dir(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def _open_out(path: Path, compress: bool) -> Any:
    if compress:
        import gzip
        return gzip.open(path, "wt", encoding='utf-8')

    return open(path, "w", encoding='utf-8')

def _chinked(seq: List[str], n: int) -> Iterable[List[str]]:
    for i in range(0, len(seq), n):
        yield seq[i : i + n]

def _get_console() -> Any:
    if _RICH_AVAILABLE:
        return Console()
    return None

def _log(console: Any, msg: str) -> None:
    if console is not None:
        console.log(msg)
    else:
        print(msg)

def _make_progress(console: Any) -> Any:
    if not _RICH_AVAILABLE:
        return None

    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )

def export_jsonl_shards(cfg: ExportConfig) -> None:
    console = _get_console()

    _log(console, f"Exporting JSONL shards from {cfg.duckdb_path} to {cfg.out_dir}")
    _log(
        console,
        f"Shard size: {cfg.shard_size} | Compress: {cfg.compress} | Sort by: {cfg.sort_by} | Indent: {cfg.indent}",
    )
    _log(console, f"Include papers with no links: {cfg.include_papers_with_no_links}")
    # Placeholder for actual export logic

    """
    Creates sharded JSONL (optionally gzipped) where each record is one citing paper record.
    Note: if cfg.indent is set, each record will span multiple lines (more readable, but not strict JSONL).
    {
        "paper": {...},
        "hypotheses": [{"h_idx":..., "text":..., "evidence":...}, ...],
        "citations": [
        {
            "cited_paper_id": "...",
            "contexts": [{"id":0,"text":"..."}, ...],
            "links": [
            {
                "citing_h_idx": 0,
                "cited_hypothesis": {"paper_id":"...", "h_idx":2},
                "relation": "support",
                "evidence": {"context_ids":[0]}
            }, ...
            ]
        }, ...
        ]
    }
    """

    _ensure_dir(cfg.out_dir)

    conn = duckdb.connect(database=str(cfg.duckdb_path), read_only=True)

    if cfg.include_papers_with_no_links:
        paper_ids : List[str] = [
            r[0] for r in conn.execute(f"SELECT full_id FROM processed ORDER BY {cfg.sort_by}").fetchall()
        ]
    
    else:
        # paper_ids: List[str] = [
        #     r[0] for r in conn.execute("SELECT DISTINCT citing_paper_id FROM hypotheses_links ORDER BY citing_paper_id").fetchall()
        # ]
        paper_ids: List[str] = [
            r[0]
            for r in conn.execute(
                f"""
                SELECT DISTINCT p.full_id
                FROM hypotheses_links h
                JOIN processed p 
                ON h.citing_paper_id = p.full_id
                ORDER BY p.{cfg.sort_by}
                """
            ).fetchall()
        ]
    
    if not paper_ids:
        _log(console, "No papers found for export.")
        return

    num_shards = math.ceil(len(paper_ids) / cfg.shard_size)
    _log(
        console,
        f"Exporting {len(paper_ids)} papers into {num_shards} shard(s) (shard_size={cfg.shard_size}).",
    )

    progress = _make_progress(console)
    if progress is None:
        shard_iter = enumerate(_chinked(paper_ids, cfg.shard_size))
    else:
        progress.start()
        shard_task = progress.add_task("Shards", total=num_shards)
        shard_iter = enumerate(_chinked(paper_ids, cfg.shard_size))

    try:
        for shard_idx, ids_batch in shard_iter:
            shard_name = f"papers-{shard_idx:05d}.jsonl" + (".gz" if cfg.compress else "")
            out_path = cfg.out_dir / shard_name

            if progress is None:
                _log(console, f"Building shard {shard_idx+1}/{num_shards}: {out_path}")
            else:
                progress.update(shard_task, description=f"Shard {shard_idx+1}/{num_shards} ({shard_name})")

            status = None
            if console is not None:
                status = console.status(f"Loading data for {shard_name}…")
                status.start()

            papers_rows = conn.execute(
                """
                SELECT full_id, title, year, authors, booktitle, venue, volume
                FROM processed
                WHERE full_id IN (SELECT * FROM UNNEST(?))
                """,
                [ids_batch],
            ).fetchall()

            paper_meta: Dict[str, Dict[str, Any]] = {}
            for full_id, title, year, authors, booktitle, venue, volume in papers_rows:
                paper_meta[full_id] = {
                    "full_id": full_id,
                    "title": title,
                    "year": year,
                    "authors": _ensure_authors_list(authors),
                    "booktitle": booktitle,
                    "venue": venue,
                    "volume": volume,
                }

            hyp_rows = conn.execute(
                """
                SELECT full_id, h_idx, hypothesis, evidence
                FROM hypotheses
                WHERE full_id IN (SELECT * FROM UNNEST(?))
                """,
                [ids_batch],
            ).fetchall()

            hyps_by_paper: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            hyp_text: Dict[Tuple[str, int], str] = {}

            for full_id, h_idx, hypothesis, evidence in hyp_rows:
                hyps_by_paper[full_id].append(
                    {
                        "h_idx": h_idx,
                        "text": hypothesis,
                        "evidence": _ensure_evidence_list_of_dicts(evidence),
                    }
                )

                hyp_text[(str(full_id), str(h_idx))] = hypothesis

            for full_id in hyps_by_paper:
                hyps_by_paper[full_id].sort(key=lambda x: x["h_idx"])

            link_rows = conn.execute(
                """
                SELECT citing_paper_id, cited_paper_id, citing_h_idx, cited_h_idx, relation
                FROM hypotheses_links
                WHERE citing_paper_id IN (SELECT * FROM UNNEST(?))
                """,
                [ids_batch],
            ).fetchall()

            # Collect cited IDs for this shard
            cited_ids_batch = sorted({str(r[1]) for r in link_rows})

            cited_meta: Dict[str, Dict[str, Any]] = {}

            if cited_ids_batch:
                cited_papers_rows = conn.execute(
                    """
                    SELECT full_id, title, year, authors, booktitle, venue, volume
                    FROM papers
                    WHERE full_id IN (SELECT * FROM UNNEST(?))
                    """,
                    [cited_ids_batch],
                ).fetchall()

                for full_id, title, year, authors, booktitle, venue, volume in cited_papers_rows:
                    fid = str(full_id)
                    cited_meta[fid] = {
                        "full_id": fid,
                        "title": title,
                        "year": year,
                        "authors": _ensure_authors_list(authors),
                        "booktitle": booktitle,
                        "venue": venue,
                        "volume": volume,
                    }

                # ---- Fetch cited hypotheses text (for link-level cited_hypothesis.text)
                cited_hyp_rows = conn.execute(
                    """
                    SELECT full_id, h_idx, hypothesis
                    FROM hypotheses
                    WHERE full_id IN (SELECT * FROM UNNEST(?))
                    """,
                    [cited_ids_batch],
                ).fetchall()

                for full_id, h_idx, hypothesis in cited_hyp_rows:
                    hyp_text[(str(full_id), str(h_idx))] = hypothesis

            # ---- Fetch citation_contexts from citations table
            # citations schema differs across DB builds:
            # - newer:  citing_id / cited_id
            # - older:  citing_paper_id / cited_paper_id
            try:
                ctx_rows = conn.execute(
                    """
                    SELECT citing_id, cited_id, citation_contexts
                    FROM citations
                    WHERE citing_id IN (SELECT * FROM UNNEST(?))
                    """,
                    [ids_batch],
                ).fetchall()
            except duckdb.BinderException:
                ctx_rows = conn.execute(
                    """
                    SELECT citing_paper_id, cited_paper_id, citation_contexts
                    FROM citations
                    WHERE citing_paper_id IN (SELECT * FROM UNNEST(?))
                    """,
                    [ids_batch],
                ).fetchall()

            ctx_by_pair: Dict[Tuple[str, str], List[Any]] = {}
            for citing_id, cited_id, citation_contexts in ctx_rows:
                key = (str(citing_id), str(cited_id))
                ctx_by_pair[key] = _normalize_citation_contexts(citation_contexts)



            # link_rows = conn.execute(
            #     """
            #     SELECT citing_paper_id, cited_paper_id, citing_h_idx, cited_h_idx, relation, citation_context
            #     FROM hypotheses_links
            #     WHERE citing_paper_id IN (SELECT * FROM UNNEST(?))
            #     """,
            #     [ids_batch],
            # ).fetchall()

            # ctx_rows = conn.execute(
            #     """
            #     SELECT citing_paper_id, cited_paper_id, citation_contexts
            #     FROM citations
            #     WHERE citing_paper_id IN (SELECT * FROM UNNEST(?))
            #     """, [ids_batch],
            # ).fetchall()

            # ctx_by_pair = {}
            # for citing_id, cited_id, citation_contexts in ctx_rows:
            #     ctx_by_pair[(str(citing_id), str(cited_id))] = _json_loads_maybe(citation_contexts) or []


            citations_map: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)

            links_task = None
            if progress is not None:
                links_task = progress.add_task("Aggregate links", total=len(link_rows))

            advanced = 0
            for i, (citing_id, cited_id, citing_h_idx, cited_h_idx, relation) in enumerate(
                link_rows, start=1
            ):
                citing_id = str(citing_id)
                cited_id = str(cited_id)
                ch = str(citing_h_idx)
                dh = str(cited_h_idx)

                if cited_id not in citations_map[citing_id]:
                    citations_map[citing_id][cited_id] = {
                        "cited_paper": cited_meta.get(cited_id, {"full_id": cited_id}),
                        "links": [],
                        # "cited_paper_id": cited_id,
                        # "contexts": [],
                        # "_ctx_index": {},
                        # "links": [],
                    }

                entry = citations_map[citing_id][cited_id]

                entry["links"].append(
                {
                    "citing_hypothesis": {
                        "citing_h_idx": ch,
                        "text": hyp_text.get((citing_id, ch)),
                    },
                    "cited_hypothesis": {
                        "cited_h_idx": dh,
                        "text": hyp_text.get((cited_id, dh)),
                    },
                    "relation": relation,
                    "citation_contexts": ctx_by_pair.get((citing_id, cited_id), []),
                }
            )


                # ctx_text = citation_context
                # if ctx_text is None:
                #     ctx_text = ""

                # # Internal, per-(citing,cited) de-dupe index: ctx_text -> ctx_id.
                # # This is removed from the final JSON output.
                # ctx_index = entry.setdefault("_ctx_index", {})
                # if ctx_text in ctx_index:
                #     ctx_id = ctx_index[ctx_text]
                # else:
                #     ctx_id = len(entry["contexts"])
                #     ctx_index[ctx_text] = ctx_id
                #     entry["contexts"].append({"id": ctx_id, "text": ctx_text})

                # entry["links"].append(
                #     {
                #         "citing_h_idx": str(citing_h_idx),
                #         "cited_hypothesis": {"paper_id": cited_id, "h_idx": str(cited_h_idx)},
                #         "relation": relation,
                #         "evidence": {"context_ids": [ctx_id]},
                #     }
                # )

                if progress is not None and links_task is not None:
                    # Reduce overhead for very large link tables.
                    if i - advanced >= 1000:
                        progress.update(links_task, advance=(i - advanced))
                        advanced = i

            if progress is not None and links_task is not None and advanced < len(link_rows):
                progress.update(links_task, advance=(len(link_rows) - advanced))

            if progress is not None and links_task is not None:
                progress.remove_task(links_task)

            if status is not None:
                status.update(f"Writing {shard_name}…")

            write_task = None
            if progress is not None:
                write_task = progress.add_task("Write papers", total=len(ids_batch))

            # Write the shard once, after all links for this batch have been aggregated.
            with _open_out(out_path, cfg.compress) as out_f:
                for pid in ids_batch:
                    meta = paper_meta.get(pid)
                    if meta is None:
                        if progress is not None and write_task is not None:
                            progress.update(write_task, advance=1)
                        continue

                    cited_entries: List[Dict[str, Any]] = []
                    if pid in citations_map:
                        for cited_id in sorted(citations_map[pid].keys()):
                            ent = citations_map[pid][cited_id]
                            # Do not mutate the aggregation map; just omit the internal index.
                            ent_out = dict(ent)
                            ent_out.pop("_ctx_index", None)
                            cited_entries.append(ent_out)

                    record = {
                        "paper": meta,
                        "hypotheses": hyps_by_paper.get(pid, []),
                        "citations": cited_entries,
                    }

                    out_f.write(json.dumps(record, ensure_ascii=False, indent=cfg.indent) + "\n")

                    if progress is not None and write_task is not None:
                        progress.update(write_task, advance=1)

            if progress is not None and write_task is not None:
                progress.remove_task(write_task)

            if status is not None:
                status.stop()

            if progress is None:
                _log(console, f"Wrote shard {shard_idx+1}/{num_shards}: {out_path}")
            else:
                progress.update(shard_task, advance=1)
                progress.console.log(f"Wrote shard {shard_idx+1}/{num_shards}: {out_path}")
    finally:
        if progress is not None:
            progress.stop()

    conn.close()

if __name__ == "__main__":
    ARR_DB_PATH = Path("db/aclanthology.duckdb")
    OUTPUT_DIR = Path("data/hypoflow")
    shard_size = 1000
    compress = False
    include_papers_with_no_links = False  
    sort_by = "year" 
    indent = 6

    cfg = ExportConfig(
        duckdb_path=ARR_DB_PATH,
        out_dir=OUTPUT_DIR,
        shard_size=shard_size,
        compress=compress,
        include_papers_with_no_links=include_papers_with_no_links,
        sort_by=sort_by,
        indent=indent,
    )

    export_jsonl_shards(cfg)
