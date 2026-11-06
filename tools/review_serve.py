import http.server,functools,json,os,sys
ROOT=os.path.expanduser('~/.cache/maze-dataset')
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control','no-store');super().end_headers()
    def do_POST(self):
        if self.path!='/verdicts':
            return self.send_error(404)
        body=self.rfile.read(min(int(self.headers.get('Content-Length',0)),1_000_000))
        try:
            data=json.loads(body)
            assert isinstance(data,dict)
        except Exception:
            return self.send_error(400)
        tmp=os.path.join(ROOT,'verdicts.json.tmp')
        with open(tmp,'w') as f: json.dump(data,f,indent=1,ensure_ascii=False)
        os.replace(tmp,os.path.join(ROOT,'verdicts.json'))
        self.send_response(204);self.end_headers()
http.server.ThreadingHTTPServer(('0.0.0.0',int(sys.argv[1])),functools.partial(H,directory=ROOT)).serve_forever()
