from __future__ import print_function, unicode_literals

import bottle
from threading import Thread, Event
import webbrowser
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server

from boxsdk import OAuth2, Client
import os

import config_oauth


CLIENT_ID = config_oauth.client_id # Insert Box client ID here
CLIENT_SECRET = config_oauth.client_secret # Insert Box client secret here


def authenticate(oauth_class=OAuth2):
    class StoppableWSGIServer(bottle.ServerAdapter):
        def __init__(self, *args, **kwargs):
            super(StoppableWSGIServer, self).__init__(*args, **kwargs)
            self._server = None

        def run(self, app):
            server_cls = self.options.get('server_class', WSGIServer)
            handler_cls = self.options.get('handler_class', WSGIRequestHandler)
            self._server = make_server(self.host, self.port, app, server_cls, handler_cls)
            self._server.serve_forever()

        def stop(self):
            self._server.shutdown()

    auth_code = {}
    auth_code_is_available = Event()

    local_oauth_redirect = bottle.Bottle()

    @local_oauth_redirect.get('/')
    def get_token():
        auth_code['auth_code'] = bottle.request.query.code
        auth_code['state'] = bottle.request.query.state
        auth_code_is_available.set()

    local_server = StoppableWSGIServer(host='localhost', port=8080)
    server_thread = Thread(target=lambda: local_oauth_redirect.run(server=local_server))

    oauth = oauth_class(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            store_tokens=save_tokens,
    )
    
    try:
        access_token, refresh_token = read_tokens_from_file()
        oauth = oauth_class(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            store_tokens=save_tokens,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        print('User: {0}'.format(Client(oauth).user().get()))
    except:
        server_thread.start()

        auth_url, csrf_token = oauth.get_authorization_url('http://localhost:8080')
        webbrowser.open(auth_url)
    
        auth_code_is_available.wait()
        local_server.stop()
        assert auth_code['state'] == csrf_token
        access_token, refresh_token = oauth.authenticate(auth_code['auth_code'])
        print('User: {0}'.format(Client(oauth).user().get()))
    print('access_token: ' + oauth._access_token)
    print('refresh_token: ' + oauth._refresh_token)

    return oauth, oauth._access_token, oauth._refresh_token

def save_tokens(access_token, refresh_token):
    print("Refreshing tokens...")
    target = open(os.path.join(os.path.expanduser("~"), 'box_dedupe_oauth_token.txt'), 'w')
    target.truncate()
    tokens = access_token+'#'+refresh_token
    target.write(tokens)
    target.close()
    
def read_tokens_from_file():
    try:
        with open(os.path.join(os.path.expanduser("~"), 'box_dedupe_oauth_token.txt'), 'r') as f:
            tokens=f.readline()
        return tokens.split('#')
    except:
        raise Exception('Failed to read from file')
    
if __name__ == '__main__':
    test,_,_ = authenticate()
   # os._exit(0)