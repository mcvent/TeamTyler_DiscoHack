# api/manager.py
from typing import Dict, List
from .common.base_provider import BaseCloudProvider

class CloudManager:
    def __init__(self):
        self._providers: Dict[str, BaseCloudProvider] = {}

    def register_provider(self, name: str, provider: BaseCloudProvider):
        """Регистрирует провайдера."""
        self._providers[name] = provider

    def get_provider(self, name: str) -> BaseCloudProvider:
        """Возвращает провайдера по имени."""
        provider = self._providers.get(name)
        if not provider:
            raise ValueError(f"Провайдер '{name}' не найден!")
        return provider

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())