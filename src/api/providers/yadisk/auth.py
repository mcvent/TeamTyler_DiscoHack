import requests
from ...common.exceptions import CloudAuthError


class YandexOAuth:
    """Логика получения токенов."""

    @staticmethod
    def get_auth_url(client_id: str, redirect_uri: str) -> str:
        return (
            f"https://oauth.yandex.ru/authorize?response_type=code"
            f"&client_id={client_id}&redirect_uri={redirect_uri}"
        )

    @staticmethod
    def exchange_code(code: str, client_id: str, client_secret: str) -> dict:
        url = "https://oauth.yandex.ru/token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        response = requests.post(url, data=data)
        if response.status_code != 200:
            raise CloudAuthError(f"Ошибка обмена кода: {response.text}")
        return response.json()