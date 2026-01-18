import argparse
from pathlib import Path

from claimflow import download_meta

def main():
    ap = argparse.ArgumentParser()
    
    ap.add_argument(
        "--max-papers",
        type=int,
        default=None,
        help="Maximum number of papers to download metadata for.",
    )

    ap.add_argument(
        "--db-path",
        type=Path,
        default=download_meta.DEFAULT_DB_PATH,
        help="Path to the DuckDB database file.",
    )

    ap.add_argument(
        "--venues",
        type=str,
        default=None,
        help='Comma-separated venue slugs, e.g. "acl,emnlp" (None=all venues)',
    )


    args = ap.parse_args()

    venues_list = [v.strip() for v in args.venues.split(",")] if args.venues else download_meta.DEFAULT_VENUES

    download_meta.store_acl_metadata(max_papers=args.max_papers, venues=venues_list, db_path=args.db_path)
    
    print("Metadata download complete.")

if __name__ == "__main__":
    main()