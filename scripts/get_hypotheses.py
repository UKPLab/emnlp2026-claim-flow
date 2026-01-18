from pathlib import Path
from claimflow import extract_hypotheses

ARR_DB_PATH = Path("db/aclanthology.duckdb")

def main():
    extract_hypotheses.run(db_path=ARR_DB_PATH)


if __name__ == "__main__":
    main()