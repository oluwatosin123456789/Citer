import argparse
import sys

from app.core.logger import logger
from app.db.session import SessionLocal
from app.ingestion.pipeline import index_repo


def main() -> None:
    parser = argparse.ArgumentParser(description="Index a GitHub repository")
    parser.add_argument("repo_url", help="Public GitHub repo URL")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        repo = index_repo(db, args.repo_url)
        logger.info("Indexed %s (%s) -> repo_id=%s", repo.name, repo.commit_hash, repo.id)
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())