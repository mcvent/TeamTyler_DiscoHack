import keyring

class AuthManager:
    @staticmethod
    def save_token(token):
        keyring.set_password("DiscoHack", "yandex_token", token)

    @staticmethod
    def load_token():
        return keyring.get_password("DiscoHack", "yandex_token")
