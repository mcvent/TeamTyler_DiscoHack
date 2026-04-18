import webbrowser
import requests
import threading
import time
from flask import Flask, request
import logging

app = Flask(__name__)
auth_state = {"code": None}

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        auth_state["code"] = code
        return "<h1>Успешно! Возвращайтесь в приложение.</h1>"
    return "<h1>Ошибка</h1>"


def get_token_via_oauth(client_id, client_secret):
    global auth_state
    auth_state["code"] = None

    def run_server():
        try:
            app.run(port=8080, use_reloader=False, threaded=True)
        except:
            pass

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    time.sleep(1)
    webbrowser.open(f"https://oauth.yandex.ru/authorize?response_type=code&client_id={client_id}")

    # Ждем код
    while auth_state["code"] is None:
        time.sleep(0.5)

    # Обмен на токен
    token_url = "https://oauth.yandex.ru/token"
    data = {
        'grant_type': 'authorization_code',
        'code': auth_state["code"],
        'client_id': client_id,
        'client_secret': client_secret
    }

    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        token = response.json().get('access_token')
        time.sleep(1)
        return token
    return None
