import subprocess
import sys


def main() -> int:
    return subprocess.call(["npm", "run", "desktop:dev"])


if __name__ == "__main__":
    raise SystemExit(main())
