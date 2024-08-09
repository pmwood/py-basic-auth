import http.server
import socketserver
import requests
import urllib.parse
import os

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000/callback'
AUTHORITY = 'https://login.microsoftonline.com/71d131b2-724f-408e-abf2-2d409f267260'
AUTHORIZE_URL = f'{AUTHORITY}/oauth2/v2.0/authorize'
TOKEN_URL = f'{AUTHORITY}/oauth2/v2.0/token'
SCOPE = ['openid', 'profile', 'email']

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(302)
            self.send_header('Location', self.get_authorization_url())
            self.end_headers()
        elif self.path.startswith('/callback'):
            self.handle_callback()
        else:
            self.send_response(404)
            self.end_headers()

    def get_authorization_url(self):
        params = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'response_mode': 'query',
            'scope': ' '.join(SCOPE),
            'state': '12345'
        }
        return f'{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}'

    def handle_callback(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        code = params.get('code', [None])[0]

        if code:
            token = self.get_token(code)
            user_info = self.get_user_info(token)
            self.display_user_info(user_info)
        else:
            self.send_response(400)
            self.end_headers()

    def get_token(self, code):
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        response = requests.post(TOKEN_URL, data=data)
        return response.json().get('access_token')

    def get_user_info(self, token):
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
        return response.json()

    def display_user_info(self, user_info):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(f"<html><body><h1>Hello, {user_info['displayName']}!</h1></body></html>".encode())

PORT = 8000
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
