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
        # Красивая HTML страница с центрированием
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Успешная авторизация</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin: 0;
                    padding: 20px;
                }

                .container {
                    text-align: center;
                    background: white;
                    padding: 50px 60px;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    animation: fadeIn 0.5s ease-in;
                }

                @keyframes fadeIn {
                    from {
                        opacity: 0;
                        transform: translateY(-20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .success-icon {
                    font-size: 80px;
                    margin-bottom: 20px;
                    animation: bounce 0.6s ease-out;
                }

                @keyframes bounce {
                    0% {
                        transform: scale(0);
                    }
                    50% {
                        transform: scale(1.2);
                    }
                    100% {
                        transform: scale(1);
                    }
                }

                h1 {
                    color: #333;
                    font-size: 32px;
                    margin-bottom: 15px;
                    font-weight: 600;
                }

                .message {
                    color: #666;
                    font-size: 18px;
                    margin-bottom: 30px;
                    line-height: 1.5;
                }

                .close-info {
                    color: #999;
                    font-size: 14px;
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                }

                .loader {
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border: 3px solid #f3f3f3;
                    border-top: 3px solid #764ba2;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-left: 10px;
                    vertical-align: middle;
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                .button {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    font-size: 16px;
                    border-radius: 50px;
                    cursor: pointer;
                    margin-top: 20px;
                    transition: transform 0.2s, box-shadow 0.2s;
                }

                .button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✓</div>
                <h1>Успешно!</h1>
                <div class="message">
                    Вы успешно авторизовались<br>
                    Возвращайтесь в приложение
                </div>
                <div class="close-info">
                    Это окно закроется автоматически через <span id="counter">15</span> секунд
                    <div class="loader"></div>
                </div>
                <button class="button" onclick="window.close()">Закрыть сейчас</button>
            </div>

            <script>
                let seconds = 15;
                const counter = document.getElementById('counter');
                const interval = setInterval(() => {
                    seconds--;
                    counter.textContent = seconds;
                    if (seconds <= 0) {
                        clearInterval(interval);
                        window.close();
                    }
                }, 1000);
            </script>
        </body>
        </html>
        """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Ошибка авторизации</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 0;
                padding: 20px;
            }

            .container {
                text-align: center;
                background: white;
                padding: 50px 60px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                animation: shake 0.5s ease-in-out;
            }

            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-10px); }
                75% { transform: translateX(10px); }
            }

            .error-icon {
                font-size: 80px;
                margin-bottom: 20px;
            }

            h1 {
                color: #333;
                font-size: 32px;
                margin-bottom: 15px;
                font-weight: 600;
            }

            .message {
                color: #666;
                font-size: 18px;
                line-height: 1.5;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error-icon">✗</div>
            <h1>Ошибка</h1>
            <div class="message">
                Не удалось получить код авторизации<br>
                Попробуйте еще раз
            </div>
        </div>
    </body>
    </html>
    """


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