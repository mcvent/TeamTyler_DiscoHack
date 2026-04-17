class CloudError(Exception):
    """Базовое исключение для всех облачных операций."""
    def __init__(self, message: str):
        super().__init__(message)

class CloudAuthError(CloudError):
    """Ошибка авторизации (401)."""

class CloudNotFoundError(CloudError):
    """Файл или папка не найдены (404)."""

class CloudQuotaError(CloudError):
    """Превышен лимит хранилища (507)."""

class CloudRateLimitError(CloudError):
    """Слишком много запросов (429)."""

class CloudAPIError(CloudError):
    """Общая ошибка API или сети."""