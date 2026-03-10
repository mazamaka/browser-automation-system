"""
Провайдер для Anthropic Claude моделей
"""
import json
from typing import Dict, Any, Optional
from anthropic import AsyncAnthropic
from langchain_anthropic import ChatAnthropic
from .model_provider import AIModelProvider, ModelFactory


class AnthropicProvider(AIModelProvider):
    """Провайдер для Claude моделей"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "claude-sonnet-4-20250514",
        **kwargs
    ):
        super().__init__(api_key, model_name)
        self._client = AsyncAnthropic(api_key=api_key)
        self.max_tokens = kwargs.get('max_tokens', 4096)
        self.temperature = kwargs.get('temperature', 0.7)
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Генерация ответа от Claude"""
        messages = [{"role": "user", "content": prompt}]
        
        params = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            "temperature": kwargs.get('temperature', self.temperature)
        }
        
        if system_prompt:
            params["system"] = system_prompt
        
        response = await self._client.messages.create(**params)
        return response.content[0].text
    
    async def analyze_dom(
        self,
        dom_structure: Dict[str, Any],
        task_description: str
    ) -> Dict[str, Any]:
        """Анализ DOM структуры для определения элементов"""
        
        system_prompt = """Ты эксперт по анализу веб-страниц и автоматизации браузера.
Твоя задача - проанализировать структуру DOM и определить какие элементы нужно использовать 
для выполнения задачи.

Верни ответ в формате JSON со следующими полями:
- elements: список элементов с их селекторами и назначением
- actions: список действий которые нужно выполнить
- order: порядок выполнения действий"""
        
        prompt = f"""Задача: {task_description}

DOM структура:
{json.dumps(dom_structure, indent=2, ensure_ascii=False)}

Проанализируй структуру и определи:
1. Какие элементы нужны для выполнения задачи
2. В каком порядке с ними взаимодействовать
3. Какие действия выполнять (клик, ввод текста, навигация)

Верни детальный анализ в JSON формате."""
        
        response = await self.generate_response(prompt, system_prompt)
        
        try:
            # Пытаемся извлечь JSON из ответа
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Если не удалось распарсить JSON, возвращаем текстовый ответ
        return {"analysis": response, "elements": [], "actions": []}
    
    async def generate_detailed_prompt(
        self,
        mini_prompt: str,
        page_context: Dict[str, Any]
    ) -> str:
        """Генерация детального системного промпта"""
        
        system_prompt = """Ты эксперт по автоматизации браузера через browser-use.
Твоя задача - превратить короткий промпт пользователя в детальную пошаговую инструкцию
для автоматизации браузера.

Инструкция должна включать:
1. URL куда нужно перейти
2. Детальные шаги с селекторами элементов
3. Что вводить в поля
4. Проверки успешности выполнения

Используй информацию о структуре страницы для точных селекторов."""
        
        prompt = f"""Короткий промпт: {mini_prompt}

Контекст страницы:
{json.dumps(page_context, indent=2, ensure_ascii=False)}

Создай детальный системный промпт для browser-use агента, который:
1. Четко описывает каждый шаг
2. Указывает точные селекторы элементов
3. Объясняет что нужно проверить после каждого действия
4. Включает обработку возможных ошибок

Промпт должен быть готов к прямому использованию в browser-use."""
        
        response = await self.generate_response(prompt, system_prompt)
        return response
    
    async def optimize_prompt(
        self,
        original_prompt: str,
        execution_results: Dict[str, Any],
        errors: list
    ) -> str:
        """Оптимизация промпта на основе результатов выполнения"""
        
        system_prompt = """Ты эксперт по оптимизации промптов для browser-use.
Проанализируй результаты выполнения и улучши промпт чтобы избежать ошибок."""
        
        prompt = f"""Оригинальный промпт:
{original_prompt}

Результаты выполнения:
{json.dumps(execution_results, indent=2, ensure_ascii=False)}

Ошибки:
{json.dumps(errors, indent=2, ensure_ascii=False)}

Оптимизируй промпт чтобы:
1. Исправить проблемы которые вызвали ошибки
2. Добавить дополнительные проверки
3. Улучшить селекторы элементов если они не сработали
4. Добавить fallback варианты

Верни улучшенный промпт."""
        
        response = await self.generate_response(prompt, system_prompt)
        return response
    
    def get_langchain_model(self, callbacks=None):
        """Получить LangChain модель (не используется для browser-use)"""
        # Этот провайдер используется только для анализа, не для browser-use
        # browser_use.ChatAnthropic не поддерживает callbacks
        return ChatAnthropic(
            model=self.model_name,
            api_key=self.api_key,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=60,
            max_retries=3
        )


# Регистрируем провайдер
ModelFactory.register_provider("claude", AnthropicProvider)
ModelFactory.register_provider("anthropic", AnthropicProvider)
