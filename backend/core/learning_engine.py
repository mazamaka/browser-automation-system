"""
Движок самообучения на основе истории выполнения
"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from ..storage.models import (
    Task, TaskExecution, LearningPattern,
    ExecutionStep, SystemPrompt
)
from ..storage.prompt_store import PromptStore


class LearningEngine:
    """Движок самообучения системы"""
    
    def __init__(self, store: PromptStore):
        self.store = store
    
    async def analyze_execution(
        self,
        task: Task,
        execution: TaskExecution
    ) -> Dict[str, Any]:
        """
        Анализ результатов выполнения для обучения

        Returns:
            Словарь с результатами анализа и рекомендациями
        """
        logger.info("🧠 Начало анализа выполнения для обучения...")
        logger.info(f"📊 Выполнение: success={execution.success}, steps={len(execution.steps)}")

        analysis = {
            "success": execution.success,
            "patterns_found": [],
            "improvements": [],
            "errors_analyzed": [],
            "recommendations": []
        }

        # Анализируем успешные шаги
        if execution.success:
            logger.info("✅ Выполнение успешное - извлекаем паттерны...")
            patterns = await self._extract_success_patterns(task, execution)
            analysis["patterns_found"] = patterns
            logger.info(f"🎯 Найдено {len(patterns)} паттернов")

            # Сохраняем паттерны
            for idx, pattern in enumerate(patterns):
                logger.info(f"💾 Сохранение паттерна {idx+1}/{len(patterns)}: {pattern.task_type}")
                await self.store.save_learning_pattern(pattern)
            logger.info(f"✅ Сохранено {len(patterns)} паттернов")
        else:
            logger.info("⚠️  Выполнение неуспешное - пропускаем извлечение паттернов")

        # Анализируем ошибки
        if not execution.success or execution.error:
            logger.info("🔍 Анализ ошибок...")
            error_analysis = self._analyze_errors(execution)
            analysis["errors_analyzed"] = error_analysis
            logger.info(f"📋 Проанализировано {len(error_analysis)} ошибок")

            # Генерируем рекомендации по улучшению
            logger.info("💡 Генерация рекомендаций по улучшению...")
            improvements = await self._generate_improvements(
                task, execution, error_analysis
            )
            analysis["improvements"] = improvements
            logger.info(f"✅ Сгенерировано {len(improvements)} рекомендаций")

        # Обновляем статистику промпта
        if task.system_prompt:
            logger.info("📈 Обновление статистики системного промпта...")
            await self._update_prompt_statistics(task, execution)
            logger.info(f"✅ Статистика обновлена: success_rate={task.system_prompt.success_rate:.2%}, executions={task.system_prompt.executions_count}")
        else:
            logger.info("ℹ️  Системного промпта нет - статистика не обновляется")

        logger.info(f"🎉 Анализ завершен: {len(analysis['patterns_found'])} паттернов, {len(analysis['improvements'])} рекомендаций")
        return analysis
    
    async def _extract_success_patterns(
        self,
        task: Task,
        execution: TaskExecution
    ) -> List[LearningPattern]:
        """Извлечение успешных паттернов из выполнения"""
        logger.info("🔍 Извлечение успешных паттернов...")

        patterns = []

        # Определяем тип задачи
        task_type = self._classify_task(task.mini_prompt)
        logger.info(f"📝 Тип задачи: {task_type}")

        # Извлекаем успешные шаги
        successful_steps = [
            step for step in execution.steps
            if step.success
        ]
        logger.info(f"✅ Успешных шагов: {len(successful_steps)}/{len(execution.steps)}")

        if len(successful_steps) >= 2:  # Минимум 2 шага для паттерна
            # Извлекаем общие селекторы
            common_selectors = self._extract_common_selectors(successful_steps)
            logger.info(f"🎯 Извлечено селекторов: {len(common_selectors)}")

            # Определяем сайты
            websites = self._extract_websites(successful_steps)
            logger.info(f"🌐 Сайты в паттерне: {websites}")

            pattern = LearningPattern(
                pattern_id=str(uuid.uuid4()),
                task_type=task_type,
                description=f"Успешный паттерн для: {task.mini_prompt[:100]}",
                successful_steps=successful_steps,
                common_selectors=common_selectors,
                success_count=1,
                last_used=datetime.now(),
                websites=websites
            )

            patterns.append(pattern)
            logger.info(f"✅ Создан паттерн: {pattern.pattern_id}")
        else:
            logger.warning(f"⚠️  Недостаточно успешных шагов для создания паттерна (нужно минимум 2, есть {len(successful_steps)})")

        logger.info(f"🎉 Извлечение завершено: {len(patterns)} паттернов")
        return patterns
    
    def _classify_task(self, mini_prompt: str) -> str:
        """Классификация типа задачи"""
        
        prompt_lower = mini_prompt.lower()
        
        # Простая классификация по ключевым словам
        if any(word in prompt_lower for word in ['войти', 'login', 'sign in', 'вход']):
            return 'login'
        elif any(word in prompt_lower for word in ['заполнить', 'форма', 'fill', 'form']):
            return 'form_fill'
        elif any(word in prompt_lower for word in ['найти', 'поиск', 'search', 'find']):
            return 'search'
        elif any(word in prompt_lower for word in ['купить', 'заказ', 'buy', 'order', 'корзина', 'cart']):
            return 'ecommerce'
        elif any(word in prompt_lower for word in ['реклама', 'ads', 'campaign']):
            return 'advertising'
        else:
            return 'general'
    
    def _extract_common_selectors(
        self,
        steps: List[ExecutionStep]
    ) -> List[str]:
        """Извлечение общих селекторов из шагов"""
        
        selectors = []
        
        for step in steps:
            for action in step.actions:
                if action.selector:
                    selectors.append(action.selector)
        
        return list(set(selectors))
    
    def _extract_websites(
        self,
        steps: List[ExecutionStep]
    ) -> List[str]:
        """Извлечение доменов сайтов из шагов"""
        
        from urllib.parse import urlparse
        
        websites = set()
        
        for step in steps:
            if step.page_url:
                try:
                    parsed = urlparse(step.page_url)
                    if parsed.netloc:
                        websites.add(parsed.netloc)
                except (ValueError, AttributeError):
                    pass
        
        return list(websites)
    
    def _analyze_errors(
        self,
        execution: TaskExecution
    ) -> List[Dict[str, Any]]:
        """Анализ ошибок при выполнении"""
        
        errors = []
        
        # Общая ошибка выполнения
        if execution.error:
            errors.append({
                "type": "execution_error",
                "message": execution.error,
                "severity": "high"
            })
        
        # Ошибки в шагах
        for step in execution.steps:
            if not step.success and step.error:
                errors.append({
                    "type": "step_error",
                    "step_number": step.step_number,
                    "description": step.description,
                    "message": step.error,
                    "severity": "medium"
                })
            
            # Ошибки в действиях
            for action in step.actions:
                if not action.success and action.error:
                    errors.append({
                        "type": "action_error",
                        "step_number": step.step_number,
                        "action_type": action.action_type,
                        "selector": action.selector,
                        "message": action.error,
                        "severity": "low"
                    })
        
        return errors
    
    async def _generate_improvements(
        self,
        task: Task,
        execution: TaskExecution,
        errors: List[Dict[str, Any]]
    ) -> List[str]:
        """Генерация рекомендаций по улучшению"""
        
        improvements = []
        
        # Анализируем типы ошибок
        error_types = [e["type"] for e in errors]
        
        if "action_error" in error_types:
            selector_errors = [
                e for e in errors 
                if e["type"] == "action_error" and e.get("selector")
            ]
            
            if selector_errors:
                improvements.append(
                    "Обновить селекторы элементов - некоторые не были найдены на странице"
                )
        
        if "step_error" in error_types:
            improvements.append(
                "Добавить дополнительные проверки между шагами"
            )
        
        if "execution_error" in error_types:
            improvements.append(
                "Пересмотреть общую логику выполнения задачи"
            )
        
        # Проверяем успешные паттерны для этого типа задачи
        task_type = self._classify_task(task.mini_prompt)
        patterns = await self.store.get_patterns_by_type(task_type)
        
        if patterns:
            improvements.append(
                f"Использовать проверенные паттерны для задач типа '{task_type}'"
            )
        
        return improvements
    
    async def _update_prompt_statistics(
        self,
        task: Task,
        execution: TaskExecution
    ):
        """Обновление статистики системного промпта"""
        
        if not task.system_prompt:
            return
        
        # Обновляем счетчики
        task.system_prompt.executions_count += 1
        
        # Пересчитываем success_rate
        successful_executions = sum(
            1 for e in task.executions
            if e.success
        )
        task.system_prompt.success_rate = (
            successful_executions / len(task.executions) if task.executions else 0.0
        )
        
        task.system_prompt.updated_at = datetime.now()
        
        # Сохраняем обновленную задачу
        await self.store.save_task(task)
    
    async def find_best_pattern(
        self,
        task_type: str,
        website: Optional[str] = None
    ) -> Optional[LearningPattern]:
        """
        Поиск лучшего паттерна для типа задачи
        
        Args:
            task_type: Тип задачи
            website: Домен сайта (опционально)
        
        Returns:
            Лучший паттерн или None
        """
        
        patterns = await self.store.get_patterns_by_type(task_type)
        
        if not patterns:
            return None
        
        # Фильтруем по сайту если указан
        if website:
            website_patterns = [
                p for p in patterns 
                if website in p.websites
            ]
            if website_patterns:
                patterns = website_patterns
        
        # Возвращаем паттерн с наибольшим success_count
        return max(patterns, key=lambda p: p.success_count)
    
    async def suggest_similar_tasks(
        self,
        mini_prompt: str,
        limit: int = 5
    ) -> List[Task]:
        """
        Предложить похожие задачи из истории
        
        Args:
            mini_prompt: Промпт для поиска похожих задач
            limit: Максимальное количество результатов
        
        Returns:
            Список похожих задач
        """
        
        similar_tasks = await self.store.find_similar_tasks(
            mini_prompt, 
            limit=limit
        )
        
        # Фильтруем только успешные задачи
        successful_tasks = [
            task for task in similar_tasks
            if task.system_prompt and task.system_prompt.success_rate > 0.5
        ]
        
        return successful_tasks[:limit]
    
    async def get_learning_statistics(self) -> Dict[str, Any]:
        """Получить статистику обучения системы"""
        
        all_tasks = await self.store.get_all_tasks(limit=10000)
        
        # Подсчет паттернов по типам
        pattern_files = list(self.store.patterns_dir.glob("*.json"))
        patterns_by_type = {}
        
        for file_path in pattern_files:
            import aiofiles
            import json
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                pattern_data = json.loads(content)
                task_type = pattern_data.get('task_type', 'unknown')
                patterns_by_type[task_type] = patterns_by_type.get(task_type, 0) + 1
        
        # Средний success_rate
        prompts_with_executions = [
            t.system_prompt for t in all_tasks 
            if t.system_prompt and t.system_prompt.executions_count > 0
        ]
        
        avg_success_rate = 0.0
        if prompts_with_executions:
            avg_success_rate = sum(
                p.success_rate for p in prompts_with_executions
            ) / len(prompts_with_executions)
        
        return {
            "total_patterns": len(pattern_files),
            "patterns_by_type": patterns_by_type,
            "total_tasks": len(all_tasks),
            "avg_success_rate": avg_success_rate,
            "tasks_with_prompts": sum(1 for t in all_tasks if t.system_prompt)
        }
