from pathlib import Path
from claimflow import build_citation_graph

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARR_DB_PATH = PROJECT_ROOT / "db" / "aclanthology.duckdb"

def main():
    batch_size = 50
    build_citation_graph.run(db_path=ARR_DB_PATH, batch_size=batch_size)


if __name__ == "__main__":
    main()
