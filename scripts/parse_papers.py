import argparse
from pathlib import Path
from claimflow import process_papers

ARR_DB_PATH = Path("db/aclanthology.duckdb")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--workers",
        type=int,
        default=1,
        help="number of concurrent process workers",
    )

    ap.add_argument(
        "--docling-threads",
        type=int,
        default=1,
        help="number of threads per DocLing converter; defaults to (CPU cores / workers)",
    )

    ap.add_argument(
        "--mode",
        type=str,
        choices=["patch", "full"],
        default="patch",
        help="whether to process only unprocessed papers (patch) or all papers (full)",
    )

    args = ap.parse_args()

    process_papers.ingest_papers(
        db_path=ARR_DB_PATH,
        max_workers=args.workers,
        max_docling_threads=args.docling_threads,
        mode=args.mode,
    )


    # ap.add_argument(
    #     "--batch-size",
    #     type=int,
    #     default=None,
    #     help="(deprecated) kept for compatibility; ignored now that PyMuPDF extraction is used",
    # )
    # ap.add_argument("--workers", type=int, default=8, help="number of concurrent process workers")
    # args = ap.parse_args()

    # if args.batch_size is not None:
    #     print("Note: --batch-size is ignored when using PyMuPDF extraction.")

    # process_papers.ingest_papers(
    #     db_path=ARR_DB_PATH,
    #     max_workers=args.workers,
    # )


if __name__ == "__main__":
    main()
