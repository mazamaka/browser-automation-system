"""
Абстракция для работы с различными AI моделями
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AIModelProvider(ABC):
    """Базовый класс для AI провайдеров"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None
    
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Генерация ответа от модели"""
        pass
    
    @abstractmethod
    async def analyze_dom(
        self,
        dom_structure: Dict[str, Any],
        task_description: str
    ) -> Dict[str, Any]:
        """Анализ DOM структуры для генерации промпта"""
        pass
    
    @abstractmethod
    async def generate_detailed_prompt(
        self,
        mini_prompt: str,
        page_context: Dict[str, Any]
    ) -> str:
        """Генерация детального промпта из мини-промпта"""
        pass
    
    @abstractmethod
    def get_langchain_model(self, callbacks=None):
        """Получить LangChain модель для browser-use"""
        pass


class ModelFactory:
    """Фабрика для создания AI моделей"""
    
    _providers = {}
    
    @classmethod
    def register_provider(cls, model_type: str, provider_class):
        """Регистрация провайдера"""
        cls._providers[model_type] = provider_class
    
    @classmethod
    def create_provider(
        cls,
        model_type: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> AIModelProvider:
        """Создание провайдера"""
        if model_type not in cls._providers:
            raise ValueError(f"Неизвестный тип модели: {model_type}")
        
        provider_class = cls._providers[model_type]
        return provider_class(api_key=api_key, **kwargs)
    
    @classmethod
    def get_available_models(cls) -> list:
        """Получить список доступных моделей"""
        return list(cls._providers.keys())
