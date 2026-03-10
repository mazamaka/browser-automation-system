"""
Движок для генерации и оптимизации промптов
"""
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..storage.models import SystemPrompt, Task
from ..storage.prompt_store import PromptStore
from ..ai.model_provider import AIModelProvider


class PromptEngine:
    """Движок для работы с промптами"""
    
    def __init__(
        self,
        ai_provider: AIModelProvider,
        store: PromptStore
    ):
        self.ai_provider = ai_provider
        self.store = store
    
    async def generate_system_prompt(
        self,
        mini_prompt: str,
        page_context: Dict[str, Any],
        similar_tasks: Optional[List[Task]] = None
    ) -> SystemPrompt:
        """
        Генерация детального системного промпта из мини-промпта
        
        Args:
            mini_prompt: Короткий промпт от пользователя
            page_context: Контекст страницы (DOM, URL, etc)
            similar_tasks: Похожие задачи из истории
        
        Returns:
            SystemPrompt: Сгенерированный системный промпт
        """
        
        # Обогащаем контекст информацией из похожих задач
        enriched_context = self._enrich_context(page_context, similar_tasks)
        
        # Генерируем детальный промпт через AI
        detailed_prompt = await self.ai_provider.generate_detailed_prompt(
            mini_prompt=mini_prompt,
            page_context=enriched_context
        )
        
        # Анализируем сгенерированный промпт
        analysis = self._analyze_prompt(detailed_prompt, page_context)
        
        # Создаем объект SystemPrompt
        system_prompt = SystemPrompt(
            prompt_id=str(uuid.uuid4()),
            content=detailed_prompt,
            steps_count=analysis.get('steps_count', 0),
            selectors=analysis.get('selectors', []),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=1,
            success_rate=0.0,
            executions_count=0
        )
        
        return system_prompt
    
    def _enrich_context(
        self,
        page_context: Dict[str, Any],
        similar_tasks: Optional[List[Task]]
    ) -> Dict[str, Any]:
        """Обогащение контекста информацией из похожих задач"""
        
        enriched = page_context.copy()
        
        if similar_tasks:
            # Собираем успешные паттерны из похожих задач
            successful_patterns = []
            common_selectors = []
            
            for task in similar_tasks:
                if task.system_prompt and task.system_prompt.success_rate > 0.5:
                    successful_patterns.append({
                        "mini_prompt": task.mini_prompt,
                        "system_prompt": task.system_prompt.content,
                        "selectors": task.system_prompt.selectors,
                        "success_rate": task.system_prompt.success_rate
                    })
                    common_selectors.extend(task.system_prompt.selectors)
            
            enriched['similar_successful_patterns'] = successful_patterns
            enriched['common_selectors'] = list(set(common_selectors))
        
        return enriched
    
    def _analyze_prompt(
        self,
        prompt: str,
        page_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Анализ промпта для извлечения метаданных"""
        
        # Подсчет шагов (простая эвристика)
        steps_keywords = [
            'шаг', 'step', 'затем', 'then', 'после', 'after',
            'далее', 'next', 'потом', 'finally'
        ]
        steps_count = sum(
            prompt.lower().count(keyword) 
            for keyword in steps_keywords
        )
        
        # Извлечение селекторов
        selectors = self._extract_selectors(prompt)
        
        return {
            'steps_count': max(steps_count, 1),
            'selectors': selectors,
            'length': len(prompt),
            'has_error_handling': any(
                keyword in prompt.lower() 
                for keyword in ['ошибка', 'error', 'exception', 'fallback']
            )
        }
    
    def _extract_selectors(self, prompt: str) -> List[str]:
        """Извлечение CSS селекторов из промпта"""
        import re
        
        selectors = []
        
        # Паттерны для поиска селекторов
        patterns = [
            r'#[\w-]+',  # ID селекторы
            r'\.[\w-]+',  # Class селекторы
            r'\[[\w-]+[=\'"]+[^\]]+\]',  # Attribute селекторы
            r'button[\w\s\[\]="\':.-]*',  # Button селекторы
            r'input[\w\s\[\]="\':.-]*',  # Input селекторы
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, prompt)
            selectors.extend(matches)
        
        # Убираем дубликаты
        return list(set(selectors))
    
    async def optimize_prompt(
        self,
        original_prompt: SystemPrompt,
        execution_results: List[Dict[str, Any]],
        errors: List[str]
    ) -> SystemPrompt:
        """
        Оптимизация промпта на основе результатов выполнения
        
        Args:
            original_prompt: Оригинальный промпт
            execution_results: Результаты выполнения
            errors: Ошибки при выполнении
        
        Returns:
            SystemPrompt: Оптимизированный промпт
        """
        
        # Подготавливаем данные для оптимизации
        optimization_context = {
            "original_prompt": original_prompt.content,
            "success_rate": original_prompt.success_rate,
            "errors": errors,
            "failed_steps": self._extract_failed_steps(execution_results)
        }
        
        # Используем AI для оптимизации
        from ..ai.anthropic_provider import AnthropicProvider
        if hasattr(self.ai_provider, 'optimize_prompt'):
            optimized_content = await self.ai_provider.optimize_prompt(
                original_prompt.content,
                optimization_context,
                errors
            )
        else:
            # Fallback если метод не реализован
            optimized_content = original_prompt.content
        
        # Создаем новую версию промпта
        optimized_prompt = SystemPrompt(
            prompt_id=str(uuid.uuid4()),
            content=optimized_content,
            steps_count=original_prompt.steps_count,
            selectors=self._extract_selectors(optimized_content),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=original_prompt.version + 1,
            success_rate=0.0,
            executions_count=0
        )
        
        return optimized_prompt
    
    def _extract_failed_steps(
        self,
        execution_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Извлечение неудачных шагов из результатов"""
        
        failed_steps = []
        
        for result in execution_results:
            if not result.get('success', True):
                steps = result.get('steps', [])
                for step in steps:
                    if not step.get('success', True):
                        failed_steps.append({
                            "step_number": step.get('step_number'),
                            "description": step.get('description'),
                            "error": step.get('error'),
                            "selector": step.get('actions', [{}])[0].get('selector') if step.get('actions') else None
                        })
        
        return failed_steps
    
    async def validate_prompt(
        self,
        prompt: SystemPrompt,
        page_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Валидация промпта перед выполнением
        
        Returns:
            Dict с результатами валидации
        """
        
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Проверка наличия селекторов
        if not prompt.selectors:
            validation_result["warnings"].append(
                "Промпт не содержит явных CSS селекторов"
            )
        
        # Проверка длины промпта
        if len(prompt.content) < 50:
            validation_result["errors"].append(
                "Промпт слишком короткий для детального выполнения"
            )
            validation_result["valid"] = False
        
        # Проверка наличия URL в контексте
        if not page_context.get('url'):
            validation_result["warnings"].append(
                "Не указан начальный URL для выполнения задачи"
            )
        
        # Проверка наличия шагов
        if prompt.steps_count == 0:
            validation_result["warnings"].append(
                "Не удалось определить количество шагов в промпте"
            )
        
        return validation_result
    
    async def merge_prompts(
        self,
        prompts: List[SystemPrompt],
        strategy: str = "best_practices"
    ) -> SystemPrompt:
        """
        Объединение нескольких промптов в один
        
        Args:
            prompts: Список промптов для объединения
            strategy: Стратегия объединения (best_practices, combine_all, etc)
        
        Returns:
            SystemPrompt: Объединенный промпт
        """
        
        if not prompts:
            raise ValueError("Нет промптов для объединения")
        
        if len(prompts) == 1:
            return prompts[0]
        
        # Выбираем лучшие части из каждого промпта
        best_selectors = []
        combined_content = []
        
        for prompt in prompts:
            if prompt.success_rate > 0.7:
                best_selectors.extend(prompt.selectors)
                combined_content.append(prompt.content)
        
        # Генерируем объединенный промпт через AI
        merge_context = {
            "prompts": combined_content,
            "selectors": list(set(best_selectors)),
            "strategy": strategy
        }
        
        merged_content = await self.ai_provider.generate_response(
            prompt=f"Объедини следующие промпты в один оптимальный: {combined_content}",
            system_prompt="Ты эксперт по оптимизации промптов для автоматизации браузера."
        )
        
        return SystemPrompt(
            prompt_id=str(uuid.uuid4()),
            content=merged_content,
            steps_count=max(p.steps_count for p in prompts),
            selectors=list(set(best_selectors)),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=1,
            success_rate=0.0,
            executions_count=0
        )
