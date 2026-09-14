import subprocess
import sys
import time


def _stop(process: subprocess.Popen[object]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main() -> int:
    api = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ]
    )
    worker = subprocess.Popen([sys.executable, "-m", "app.workers.ingestion_worker"])
    processes = (api, worker)

    try:
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        return 0
    finally:
        for process in processes:
            _stop(process)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
