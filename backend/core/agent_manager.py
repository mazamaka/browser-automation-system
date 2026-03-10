"""
Главный менеджер агентов - оркестрирует всю систему
"""
import uuid
import asyncio
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from loguru import logger
from .browser_controller import BrowserController
from .prompt_engine import PromptEngine
from .learning_engine import LearningEngine
from .checkpoint_manager import CheckpointManager
from .goal_detector import GoalDetector
from ..storage.models import (
    Task, TaskExecution, ExecutionStep, StepAction,
    TaskStatus, SystemPrompt, Checkpoint, GoalEvaluation
)
from ..storage.prompt_store import PromptStore
from ..ai.model_provider import AIModelProvider, ModelFactory


class AgentManager:
    """Главный менеджер для управления всем процессом"""
    
    def __init__(
        self,
        store: PromptStore,
        analysis_provider: AIModelProvider,
        execution_provider: AIModelProvider,
        headless: bool = False
    ):
        self.store = store
        self.analysis_provider = analysis_provider
        self.execution_provider = execution_provider
        
        self.browser_controller = BrowserController(headless=headless)
        self.prompt_engine = PromptEngine(analysis_provider, store)
        self.learning_engine = LearningEngine(store)
        self.checkpoint_manager = CheckpointManager()
        self.goal_detector = GoalDetector(analysis_provider)

        # Колбэки для событий
        self._on_task_update: Optional[Callable] = None
        self._on_step_complete: Optional[Callable] = None
    
    async def create_task(
        self,
        mini_prompt: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Создать новую задачу
        
        Args:
            mini_prompt: Короткий промпт от пользователя
            metadata: Дополнительные метаданные
        
        Returns:
            Task: Созданная задача
        """
        
        task = Task(
            task_id=str(uuid.uuid4()),
            mini_prompt=mini_prompt,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata or {}
        )
        
        await self.store.save_task(task)
        await self._emit_task_update(task, "created")
        
        return task
    
    async def execute_task(
        self,
        task_id: str,
        force_new_prompt: bool = False
    ) -> TaskExecution:
        """
        Выполнить задачу с checkpoint flow

        Args:
            task_id: ID задачи
            force_new_prompt: Принудительно создать новый промпт (игнорируется в новой логике)

        Returns:
            TaskExecution: Результат выполнения
        """
        logger.info(f"🎬 Начало выполнения задачи {task_id}")

        # Загружаем задачу
        logger.info(f"📂 Загрузка задачи {task_id}...")
        task = await self.store.load_task(task_id)
        if not task:
            logger.error(f"❌ Задача {task_id} не найдена")
            raise ValueError(f"Задача {task_id} не найдена")
        logger.info(f"✅ Задача загружена: '{task.mini_prompt}'")

        # Загружаем checkpoint (если есть)
        checkpoint = await self.checkpoint_manager.load_checkpoint(task_id)
        attempt_number = (checkpoint.attempt_number + 1) if checkpoint else 1

        logger.info(f"🔄 Попытка #{attempt_number}" + (f" (продолжение с прогресса {checkpoint.goal_progress:.1%})" if checkpoint else " (первый запуск)"))

        # Обновляем статус
        logger.info("📝 Обновление статуса задачи на IN_PROGRESS...")
        task.status = TaskStatus.IN_PROGRESS
        await self.store.save_task(task)
        await self._emit_task_update(task, "started")
        logger.info("✅ Статус обновлен")

        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        logger.info(f"🆔 ID выполнения: {execution_id}")

        try:
            # Инициализируем браузер
            logger.info("🌐 Инициализация браузера...")
            await self.browser_controller.initialize()
            logger.info("✅ Браузер инициализирован")

            # Подготавливаем контекст задачи
            task_context = self._prepare_task_context(task, checkpoint)

            # Выполнение через browser-use с checkpoint контекстом
            logger.info("🤖 Запуск выполнения через browser-use...")
            execution_result = await self._execute_with_browser_use_checkpoint(
                task,
                task_context,
                execution_id
            )
            logger.info(f"✅ Выполнение завершено: success={execution_result.get('success')}")

            # Финализация результатов
            logger.info("💾 Финализация и сохранение результатов...")
            execution = await self._finalize_execution(
                task,
                execution_id,
                execution_result,
                start_time
            )
            logger.info("✅ Результаты сохранены")

            # Оценка достижения цели
            logger.info("🎯 Оценка достижения цели...")
            goal_evaluation = await self.goal_detector.evaluate_goal(task, execution)
            logger.info(f"📊 Прогресс: {goal_evaluation.progress_percent:.1%}, Цель достигнута: {goal_evaluation.goal_achieved}")

            # Создаем и сохраняем checkpoint
            logger.info("💾 Создание checkpoint...")
            new_checkpoint = await self.checkpoint_manager.create_checkpoint_from_execution(
                task, execution, goal_evaluation, attempt_number
            )
            await self.checkpoint_manager.save_checkpoint(new_checkpoint)
            logger.info("✅ Checkpoint сохранен")

            # Обучение на основе результатов
            logger.info("🧠 Обучение на основе результатов...")
            await self._learn_from_execution(task, execution)
            logger.info("✅ Обучение завершено")

            # Обновляем статус задачи
            if goal_evaluation.goal_achieved:
                final_status = TaskStatus.COMPLETED
                logger.info("🎉 Цель достигнута! Задача завершена успешно!")
                # Удаляем checkpoint при успешном завершении
                await self.checkpoint_manager.delete_checkpoint(task_id)
            else:
                final_status = TaskStatus.FAILED
                logger.info(f"⚠️  Цель не достигнута. Прогресс: {goal_evaluation.progress_percent:.1%}")
                logger.info(f"💡 Следующие действия: {', '.join(goal_evaluation.next_suggested_actions[:2])}")

            task.status = final_status
            await self.store.save_task(task)
            await self._emit_task_update(task, "completed")

            return execution

        except Exception as e:
            # Обработка ошибок
            logger.error(f"❌ Ошибка при выполнении задачи {task_id}: {e}", exc_info=True)
            logger.info("🔧 Обработка ошибки...")
            execution = await self._handle_execution_error(
                task,
                execution_id,
                str(e),
                start_time
            )

            task.status = TaskStatus.FAILED
            await self.store.save_task(task)
            await self._emit_task_update(task, "failed")
            logger.info(f"⚠️  Задача {task_id} завершена с ошибкой")

            return execution

        finally:
            # Закрываем браузер
            logger.info("🔒 Закрытие браузера (finally блок)...")
            await self.browser_controller.close()
            logger.info("✅ Браузер закрыт, выполнение завершено")
    
    async def _prepare_system_prompt(self, task: Task) -> SystemPrompt:
        """Подготовка системного промпта"""
        logger.info("📋 Начало подготовки системного промпта")

        await self._emit_task_update(task, "preparing_prompt")

        # Ищем похожие задачи
        logger.info("🔍 Поиск похожих задач...")
        similar_tasks = await self.learning_engine.suggest_similar_tasks(
            task.mini_prompt,
            limit=3
        )
        logger.info(f"✅ Найдено {len(similar_tasks)} похожих задач")

        # Browser-use сам управляет браузером, поэтому не делаем предварительную навигацию
        # Определяем начальный URL (если есть в промпте)
        logger.info("🌐 Извлечение URL из промпта...")
        initial_url = self._extract_url_from_prompt(task.mini_prompt)
        logger.info(f"{'✅' if initial_url else 'ℹ️ '} URL: {initial_url or 'не найден'}")

        # Простой контекст без предварительного анализа DOM
        # Browser-use сам проанализирует страницу во время выполнения
        page_context = {"url": initial_url} if initial_url else {}

        # Генерируем системный промпт
        logger.info("✍️  Генерация системного промпта через AI...")
        system_prompt = await self.prompt_engine.generate_system_prompt(
            mini_prompt=task.mini_prompt,
            page_context=page_context,
            similar_tasks=similar_tasks
        )
        logger.info(f"✅ Системный промпт сгенерирован (длина: {len(system_prompt.content)} символов)")

        return system_prompt
    
    def _prepare_task_context(self, task: Task, checkpoint: Optional[Checkpoint]) -> str:
        """
        Подготовить контекст задачи для browser-use

        Args:
            task: Задача
            checkpoint: Checkpoint (если есть)

        Returns:
            Форматированный контекст
        """
        if not checkpoint:
            # Первый запуск - только мини-промпт
            return task.mini_prompt

        # Продолжение - добавляем контекст из checkpoint
        checkpoint_context = self.checkpoint_manager.format_checkpoint_context(checkpoint)

        context = f"""{task.mini_prompt}

{checkpoint_context}"""

        return context

    async def _execute_with_browser_use_checkpoint(
        self,
        task: Task,
        task_context: str,
        execution_id: str
    ) -> Dict[str, Any]:
        """
        Выполнение задачи через browser-use с checkpoint контекстом

        Args:
            task: Задача
            task_context: Контекст задачи (mini_prompt + checkpoint)
            execution_id: ID выполнения

        Returns:
            Результаты выполнения
        """
        await self._emit_task_update(task, "executing")

        # Получаем LangChain модель для выполнения
        llm_model = self.execution_provider.get_langchain_model()
        logger.info("🤖 LLM модель создана")

        # Проверка наличия API ключа
        if self.execution_provider.api_key:
            logger.info("🔑 API ключ присутствует")
        else:
            logger.warning("⚠️  API ключ отсутствует!")

        logger.info(f"🔧 Провайдер: {self.execution_provider.__class__.__name__}")
        logger.info(f"🔧 Модель: {self.execution_provider.model_name if hasattr(self.execution_provider, 'model_name') else 'unknown'}")

        logger.info(f"📝 Контекст задачи (длина: {len(task_context)} символов)")
        logger.debug(f"Контекст:\n{task_context}")

        # Выполняем через browser-use с контекстом
        # Подсчёт стоимости работает через calculate_cost=True в Agent
        result = await self.browser_controller.execute_with_browser_use(
            task=task_context,  # Короткий промпт + checkpoint контекст
            llm_model=llm_model,
            max_steps=50
        )

        return result

    async def _execute_with_browser_use(
        self,
        task: Task,
        execution_id: str
    ) -> Dict[str, Any]:
        """Выполнение задачи через browser-use (старый метод, оставлен для совместимости)"""

        await self._emit_task_update(task, "executing")

        # Получаем LangChain модель для выполнения
        llm_model = self.execution_provider.get_langchain_model()

        # Используем системный промпт или мини-промпт
        task_prompt = task.system_prompt.content if task.system_prompt else task.mini_prompt

        # Выполняем через browser-use
        result = await self.browser_controller.execute_with_browser_use(
            task=task_prompt,
            llm_model=llm_model,
            max_steps=50
        )

        return result
    
    async def _finalize_execution(
        self,
        task: Task,
        execution_id: str,
        result: Dict[str, Any],
        start_time: datetime
    ) -> TaskExecution:
        """Финализация выполнения и сохранение результатов"""
        
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Преобразуем шаги
        steps = self._convert_steps(result.get('steps', []))

        # Скриншоты берем из результата browser-use (он делает их сам)
        screenshots = result.get('screenshots', [])

        # Обработка result - может быть строка или dict
        final_result = result.get('final_result')
        if isinstance(final_result, str):
            # Оборачиваем строку в словарь для соответствия Pydantic модели
            result_dict = {
                "final_result": final_result,
                "success": result['success'],
                "has_errors": result.get('has_errors', False),
                "actions": result.get('actions', []),
                "urls": result.get('urls', [])
            }
        else:
            # Если уже словарь, используем как есть
            result_dict = final_result if final_result else {}

        execution = TaskExecution(
            execution_id=execution_id,
            timestamp=start_time,
            status=TaskStatus.COMPLETED if result['success'] else TaskStatus.FAILED,
            steps=steps,
            result=result_dict,
            success=result['success'],
            error=result.get('error'),
            duration_ms=duration_ms,
            screenshots=screenshots,
            extracted_data=result.get('extracted_data')
        )
        
        # Сохраняем выполнение
        await self.store.add_execution_to_task(task.task_id, execution)
        
        return execution
    
    def _convert_steps(self, browser_use_steps: List[Dict]) -> List[ExecutionStep]:
        """
        Преобразование шагов browser-use в нашу модель с извлечением реальных actions

        Args:
            browser_use_steps: Список шагов из browser-use с action_details

        Returns:
            Список ExecutionStep с заполненными actions
        """

        steps = []

        for idx, step_data in enumerate(browser_use_steps):
            # Извлекаем детали действия
            action_details = step_data.get('action_details', {})

            # Создаем StepAction из деталей
            actions = []
            if action_details:
                action = StepAction(
                    action_type=action_details.get('action_type', 'unknown'),
                    selector=action_details.get('selector'),
                    value=action_details.get('input_value'),
                    url=action_details.get('url'),
                    timestamp=datetime.now(),
                    success=True  # Если действие выполнилось, считаем успешным
                )
                actions.append(action)

            step = ExecutionStep(
                step_number=idx + 1,
                description=step_data.get('thought', step_data.get('action', '')),
                actions=actions,  # Теперь actions заполнен!
                timestamp=datetime.now(),
                success=True
            )

            steps.append(step)

        logger.info(f"✅ Преобразовано {len(steps)} шагов с {sum(len(s.actions) for s in steps)} действиями")

        return steps
    
    async def _learn_from_execution(
        self,
        task: Task,
        execution: TaskExecution
    ):
        """Обучение на основе результатов выполнения"""
        
        await self._emit_task_update(task, "learning")
        
        # Анализируем выполнение
        analysis = await self.learning_engine.analyze_execution(task, execution)
        
        # Если выполнение неуспешно и есть рекомендации по улучшению
        if not execution.success and task.system_prompt:
            # Оптимизируем промпт
            errors = [execution.error] if execution.error else []
            optimized_prompt = await self.prompt_engine.optimize_prompt(
                task.system_prompt,
                [execution.model_dump()],
                errors
            )
            
            # Сохраняем оптимизированный промпт для следующей попытки
            task.system_prompt = optimized_prompt
            await self.store.save_task(task)
    
    async def _handle_execution_error(
        self,
        task: Task,
        execution_id: str,
        error: str,
        start_time: datetime
    ) -> TaskExecution:
        """Обработка ошибки выполнения"""
        
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        execution = TaskExecution(
            execution_id=execution_id,
            timestamp=start_time,
            status=TaskStatus.FAILED,
            steps=[],
            result=None,
            success=False,
            error=error,
            duration_ms=duration_ms,
            screenshots=[],
            extracted_data=None
        )
        
        await self.store.add_execution_to_task(task.task_id, execution)
        
        return execution
    
    def _extract_url_from_prompt(self, prompt: str) -> Optional[str]:
        """Извлечение URL из промпта"""
        import re
        
        # Ищем URL в промпте
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        matches = re.findall(url_pattern, prompt)
        
        if matches:
            return matches[0]
        
        # Пытаемся определить по ключевым словам
        prompt_lower = prompt.lower()
        
        if 'google' in prompt_lower or 'гугл' in prompt_lower:
            if 'ads' in prompt_lower or 'реклам' in prompt_lower:
                return "https://ads.google.com"
            return "https://www.google.com"
        
        return None
    
    def set_on_task_update(self, callback: Callable):
        """Установить колбэк для обновлений задачи"""
        self._on_task_update = callback
    
    def set_on_step_complete(self, callback: Callable):
        """Установить колбэк для завершения шага"""
        self._on_step_complete = callback
    
    async def _emit_task_update(self, task: Task, event: str):
        """Отправить событие обновления задачи"""
        if self._on_task_update:
            try:
                if asyncio.iscoroutinefunction(self._on_task_update):
                    await self._on_task_update(task.task_id, event, task)
                else:
                    self._on_task_update(task.task_id, event, task)
            except Exception as e:
                logger.warning(f"Ошибка в колбэке task_update: {e}")
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Получить статус задачи"""
        task = await self.store.load_task(task_id)
        
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "mini_prompt": task.mini_prompt,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "executions_count": len(task.executions),
            "last_execution": task.executions[-1].model_dump() if task.executions else None,
            "system_prompt": task.system_prompt.model_dump() if task.system_prompt else None
        }
