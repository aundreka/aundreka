from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit

from generate_banner import render_banner


def first_value(values: list[str], default: str) -> str:
    if not values:
        return default
    value = values[0].strip()
    return value or default


def parse_bool(values: list[str], default: bool) -> bool:
    if not values:
        return default
    value = values[0].strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlsplit(self.path).query)
        theme = first_value(query.get("theme", []), "dark").lower()
        mode = first_value(query.get("mode", []), "weighted").lower()
        animate = first_value(query.get("animate", []), "off").lower()
        github = parse_bool(query.get("github", []), True)
        visits = first_value(query.get("visits", []), "").strip() or None

        if theme not in {"dark", "light"}:
            self.send_error(400, "Invalid theme. Use dark or light.")
            return

        if mode not in {"random", "weighted", "chronological"}:
            self.send_error(400, "Invalid mode.")
            return

        if animate not in {"off", "once", "loop"}:
            self.send_error(400, "Invalid animate mode. Use off, once, or loop.")
            return

        try:
            svg = render_banner(
                theme=theme,
                mode=mode,
                github=github,
                visits_override=visits,
                animate_mode=animate,
            )
        except Exception as exc:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"Banner generation failed: {exc}".encode("utf-8"))
            return

        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, max-age=0, must-revalidate")
        self.end_headers()
        self.wfile.write(svg.encode("utf-8"))
