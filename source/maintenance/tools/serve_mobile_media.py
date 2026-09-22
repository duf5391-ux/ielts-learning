"""Read-only loopback preview of the candidate with unchanged formal dependencies."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from prepare_mobile_media import BOOK, STAGE


class Preview(SimpleHTTPRequestHandler):
    preview_root = STAGE

    def translate_path(self, path):
        relative = unquote(urlsplit(path).path).lstrip('/')
        if not relative:
            relative = 'index.html' if (self.preview_root / 'index.html').exists() else '开始学习.html'
        for root in (self.preview_root, STAGE, BOOK):
            target = (root / relative).resolve()
            if target.is_relative_to(root.resolve()) and target.is_file():
                return str(target)
        return str(STAGE / '__missing__')

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, default=STAGE)
    parser.add_argument('--port', type=int, default=8879)
    args = parser.parse_args()
    Preview.preview_root = args.stage.resolve()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Preview)
    print('http://127.0.0.1:' + str(args.port) + '/', flush=True)
    server.serve_forever()
