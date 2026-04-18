class CloudError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class CloudAuthError(CloudError):
    pass

class CloudNotFoundError(CloudError):
    pass

class CloudQuotaError(CloudError):
    pass

class CloudRateLimitError(CloudError):
    pass

class CloudAPIError(CloudError):
    pass