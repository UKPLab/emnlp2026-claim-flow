import argparse
# from pathlib import Path

from claimflow import download_papers

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=1800, help="earliest year (inclusive)")
    # ap.add_argument("--start", type=int, default=None, help="earliest year (inclusive)")
    ap.add_argument("--end", type=int, default=2100, help="latest year (inclusive)")
    # ap.add_argument("--end", type=int, default=None, help="latest year (inclusive)")
    ap.add_argument("--out", type=str, default="data/aclanthology", help="output root folder")
    # ap.add_argument("--max-papers", type=int, default=50, help="maximum number of papers to download")
    ap.add_argument("--max-papers", type=int, default=50, help="maximum number of papers to download")
    ap.add_argument("--workers", type=int, default=8, help="number of concurrent download workers")
    args = ap.parse_args()

    download_papers.download_papers(
        start=args.start,
        end=args.end,
        out=args.out,
        max_papers=args.max_papers,
        workers=args.workers,
    )
    print("Download complete.")


if __name__ == "__main__":
    main()