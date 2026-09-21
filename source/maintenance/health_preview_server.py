"""Serve only the isolated QA entry and its existing book assets on loopback."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote,urlsplit
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--entry',type=Path,required=True);ap.add_argument('--assets',type=Path,required=True);ap.add_argument('--port',type=int,default=41829);args=ap.parse_args()
entry=args.entry.resolve();assets=args.assets.resolve();assert entry.is_file() and assets.is_dir()
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        route=unquote(urlsplit(path).path)
        if route in ['/','/index.html']:return str(entry)
        target=(assets/route.lstrip('/')).resolve()
        if not target.is_relative_to(assets):return str(assets/'__not_found__')
        return str(target)
    def end_headers(self):
        self.send_header('Cache-Control','no-store');super().end_headers()
    def log_message(self,*args):pass
ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
