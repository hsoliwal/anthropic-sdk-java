"""Regression tests for the Steady health probe (stdlib only)."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import run
from threading import Thread


SCRIPT = Path(__file__).resolve().parents[1] / "steady-health"


class HealthHandler(BaseHTTPRequestHandler):
    status = 200

    def do_GET(self):
        self.send_response(self.status if self.path == "/_x-steady/health" else 404)
        self.end_headers()

    def log_message(self, *args):
        pass


def main():
    with ThreadingHTTPServer(("127.0.0.1", 0), HealthHandler) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        url = f"http://127.0.0.1:{server.server_port}/_x-steady/health"
        for status in (200, 204, 302, 404, 500, 503):
            HealthHandler.status = status
            result = run(["bash", str(SCRIPT), url], capture_output=True, check=False)
            assert (result.returncode == 0) == (200 <= status < 300), (
                f"health status {status}: unexpected exit {result.returncode}"
            )
        result = run(["bash", str(SCRIPT)], capture_output=True, check=False)
        assert result.returncode == 2, "missing URL should return usage error"
        server.shutdown()
    print("Steady health probe: 7 cases passed")


if __name__ == "__main__":
    main()
