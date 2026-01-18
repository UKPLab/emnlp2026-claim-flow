import argparse
from pathlib import Path

from claimflow import download_bibtex


def main():
    parser = argparse.ArgumentParser(
        description="Download the ACL Anthology BibTeX metadata."
    )
    parser.add_argument(
        "--url",
        type=str,
        default=download_bibtex.DEFAULT_URL,
        help="Optional URL to download the BibTeX file from.",
    )
    parser.add_argument(
        "--save-path",
        type=Path,
        default=download_bibtex.DEFAULT_BIB_PATH,
        help="Optional path to save the downloaded BibTeX file.",
    )

    parser.add_argument(
        "--db-path",
        type=Path,
        default=download_bibtex.DEFAULT_DB_PATH,
        help="Optional path to save the DuckDB database file.",
    )

    args = parser.parse_args()
    download_bibtex.download_arr_bibtex(args.url, args.save_path)
    download_bibtex.bib_gz_to_duckdb(args.save_path, args.db_path)


if __name__ == "__main__":
    main()
