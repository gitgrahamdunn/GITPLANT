import signal
import subprocess
import sys

processes = []


def shutdown(*_):
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    backend = subprocess.Popen(
        [
            "bash",
            "-lc",
            "cd backend && APP_ENV=dev ENABLE_DEMO_ENDPOINTS=true uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
        ]
    )
    frontend = subprocess.Popen(["bash", "-lc", "cd frontend && npm run dev -- --host 0.0.0.0 --port 5173"])
    processes.extend([backend, frontend])

    while True:
        for proc in processes:
            code = proc.poll()
            if code is not None:
                shutdown()
        signal.pause()


if __name__ == "__main__":
    main()
