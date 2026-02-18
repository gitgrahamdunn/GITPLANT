from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlmodel import Session

from app.db import engine, init_db
from app.seed import seed_demo_data, wipe_all_data


def main() -> None:
    init_db()
    with Session(engine) as session:
        wipe_all_data(session)
        result = seed_demo_data(session)
    print(result.model_dump())


if __name__ == "__main__":
    main()
