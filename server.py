#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse
import colorama
import json
import time


MSG_OK = f"[ {colorama.Fore.GREEN}OK{colorama.Fore.RESET} ]"
MSG_ERROR = f"[ {colorama.Fore.RED}ERROR{colorama.Fore.RESET} ]"
MSG_WARN = f"[ {colorama.Fore.YELLOW}WARNING{colorama.Fore.RESET} ]"
MSG_INFO = f"[ {colorama.Fore.CYAN}INFO{colorama.Fore.RESET} ]"


class Server(HTTPServer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.messages = []
        self.connected_clients = {}


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _html(self):
        """HTML homepage."""
        return open('templates/index.html', 'r').read().encode('utf-8')

    def _favicon(self):
        """Return favicon."""
        return open('assets/favicon.ico', 'rb').read()

    def _set_headers_200(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def error_404(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def refresh_clients(self) -> int:
        clients: dict = {}
        for i in self.server.connected_clients:
            if time.time() - self.server.connected_clients[i] > 10:
                print(f"{MSG_INFO} Client disconnected: {i}")
            else:
                clients[i] = self.server.connected_clients[i]
        self.server.connected_clients = clients
        return len(self.server.connected_clients)

    def do_GET(self):
        self._set_headers_200()
        self.server.connected_clients[self.client_address[0]] = time.time()
        clients_num = self.refresh_clients()
        if self.path == "/":
            if self.client_address[0] not in self.server.connected_clients:
                print(f"{MSG_INFO} Client connected: {self.client_address[0]}")
            self.wfile.write(self._html())
        elif self.path == "/messages":
            self.wfile.write(json.dumps(
                {
                    "messages": self.server.messages,
                    "clients": clients_num
                }).encode())
        elif self.path == "/clear":
            # Clear all messages
            self.server.messages = []
            print(f"{MSG_INFO} Cleared messages")
            self.wfile.write(json.dumps(self.server.messages).encode())
        elif self.path == "/favicon.ico":
            self.wfile.write(self._favicon())
        else:
            self.error_404()

    def do_POST(self):
        """Send message."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        self._set_headers_200()
        self.server.messages.append(self._process_message(post_data))

    def do_HEAD(self):
        self._set_headers_200()

    def _process_message(self, msg: bytes) -> str:
        """Return decoded message and add a timestamp."""
        message = json.loads(msg.decode('utf-8'))
        message['timestamp'] = time.strftime(
            "%H:%M:%S", time.localtime(time.time()))
        return message


def run(handler_class=RequestHandler, addr="0.0.0.0", port=8000):
    server_address = (addr, port)
    httpd = Server(server_address, handler_class)
    try:
        with open(".data.json", "r") as f:
            httpd.messages = json.load(f)
            print(f"{MSG_OK} Read the data file")
    except FileNotFoundError:
        print(f"{MSG_WARN} No data file found")
    try:
        print(f"{MSG_OK} Started the server on {addr}:{port}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{MSG_ERROR} Stopped the server")
        with open(".data.json", "w") as f:
            json.dump(httpd.messages, f)
            print(f"{MSG_OK} Saved the data file")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simple HTTP Server')
    parser.add_argument('--port', action="store",
                        dest="port", type=int, default=8000)
    parser.add_argument('--address', action="store",
                        dest="address", default="0.0.0.0")
    given_args = parser.parse_args()
    run(port=given_args.port, addr=given_args.address)
