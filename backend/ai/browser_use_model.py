"""
Провайдер для browser-use специализированной модели
"""
from typing import Dict, Any, Optional
from .model_provider import AIModelProvider, ModelFactory


class BrowserUseProvider(AIModelProvider):
    """Провайдер для bu-1-0 модели"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "bu-1-0",
        **kwargs
    ):
        super().__init__(api_key, model_name)
        self.fallback_provider = kwargs.get('fallback_provider', 'anthropic')
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Генерация ответа"""
        from .anthropic_provider import AnthropicProvider
        provider = AnthropicProvider(api_key=self.api_key)
        return await provider.generate_response(prompt, system_prompt, **kwargs)
    
    async def analyze_dom(
        self,
        dom_structure: Dict[str, Any],
        task_description: str
    ) -> Dict[str, Any]:
        """Анализ DOM"""
        from .anthropic_provider import AnthropicProvider
        provider = AnthropicProvider(api_key=self.api_key)
        return await provider.analyze_dom(dom_structure, task_description)
    
    async def generate_detailed_prompt(
        self,
        mini_prompt: str,
        page_context: Dict[str, Any]
    ) -> str:
        """Генерация детального промпта"""
        from .anthropic_provider import AnthropicProvider
        provider = AnthropicProvider(api_key=self.api_key)
        return await provider.generate_detailed_prompt(mini_prompt, page_context)
    
    def get_langchain_model(self, callbacks=None):
        """Получить модель для browser-use"""
        import os
        from browser_use import ChatBrowserUse, ChatAnthropic

        # Проверяем наличие BROWSER_USE_API_KEY
        browser_use_key = os.getenv('BROWSER_USE_API_KEY')

        if browser_use_key:
            # Используем ChatBrowserUse - оптимизированный сервис browser-use
            # Это быстрее и дешевле чем прямой Claude API
            from loguru import logger
            logger.info("🌐 Используем ChatBrowserUse (оптимизированный сервис)")
            logger.info(f"🔑 Browser-use API ключ присутствует")

            llm = ChatBrowserUse(
                api_key=browser_use_key
            )
        else:
            # Fallback на ChatAnthropic если нет BROWSER_USE_API_KEY
            from loguru import logger
            logger.info("🔧 Используем ChatAnthropic (прямой Anthropic API)")

            llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key=self.api_key
            )

        return llm


ModelFactory.register_provider("browser-use", BrowserUseProvider)
ModelFactory.register_provider("bu-1-0", BrowserUseProvider)
