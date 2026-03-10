"""
Менеджер Checkpoint - управление сохранением и загрузкой прогресса выполнения задач
"""
import uuid
import json
import aiofiles
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from loguru import logger

from ..storage.models import (
    Checkpoint, DetailedAction, PageState, ExecutionStep,
    Task, TaskExecution, GoalEvaluation
)


class CheckpointManager:
    """Управление checkpoint'ами для инкрементального выполнения задач"""

    def __init__(self, checkpoints_dir: str = "data/checkpoints"):
        self.checkpoints_dir = Path(checkpoints_dir)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    async def save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """
        Сохранить checkpoint

        Args:
            checkpoint: Checkpoint для сохранения
        """
        logger.info(f"💾 Сохранение checkpoint {checkpoint.checkpoint_id} для задачи {checkpoint.task_id}")

        file_path = self.checkpoints_dir / f"{checkpoint.task_id}_checkpoint.json"

        try:
            checkpoint_data = checkpoint.model_dump(mode='json')

            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(checkpoint_data, indent=2, ensure_ascii=False, default=str))

            logger.info(f"✅ Checkpoint сохранен: {file_path}")
            logger.info(f"   Попытка: {checkpoint.attempt_number}, Прогресс: {checkpoint.goal_progress:.1%}")

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения checkpoint: {e}", exc_info=True)
            raise

    async def load_checkpoint(self, task_id: str) -> Optional[Checkpoint]:
        """
        Загрузить последний checkpoint для задачи

        Args:
            task_id: ID задачи

        Returns:
            Checkpoint или None если не найден
        """
        logger.info(f"📂 Загрузка checkpoint для задачи {task_id}")

        file_path = self.checkpoints_dir / f"{task_id}_checkpoint.json"

        if not file_path.exists():
            logger.info(f"ℹ️  Checkpoint не найден для задачи {task_id}")
            return None

        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                checkpoint_data = json.loads(content)

            checkpoint = Checkpoint(**checkpoint_data)

            logger.info(f"✅ Checkpoint загружен: попытка {checkpoint.attempt_number}, прогресс {checkpoint.goal_progress:.1%}")
            return checkpoint

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки checkpoint: {e}", exc_info=True)
            return None

    async def create_checkpoint_from_execution(
        self,
        task: Task,
        execution: TaskExecution,
        goal_evaluation: GoalEvaluation,
        attempt_number: int
    ) -> Checkpoint:
        """
        Создать checkpoint на основе результатов выполнения

        Args:
            task: Задача
            execution: Результат выполнения
            goal_evaluation: Оценка достижения цели
            attempt_number: Номер попытки

        Returns:
            Созданный checkpoint
        """
        logger.info(f"🔨 Создание checkpoint из execution {execution.execution_id}")

        # Извлекаем успешные и неуспешные действия из шагов
        successful_actions: List[DetailedAction] = []
        failed_actions: List[DetailedAction] = []

        for step in execution.steps:
            for action in step.actions:
                # Создаем DetailedAction из StepAction
                detailed_action = DetailedAction(
                    action_type=action.action_type,
                    selector=action.selector,
                    input_value=action.value,
                    page_url=action.url,
                    success=action.success,
                    error=action.error,
                    timestamp=action.timestamp
                )

                if action.success:
                    successful_actions.append(detailed_action)
                else:
                    failed_actions.append(detailed_action)

        # Создаем PageState (упрощенный, т.к. browser-use не всегда дает детали)
        current_page_state = None
        if execution.steps:
            last_step = execution.steps[-1]
            if last_step.page_url:
                current_page_state = PageState(
                    url=last_step.page_url,
                    screenshot_path=last_step.screenshot_path
                )

        checkpoint = Checkpoint(
            checkpoint_id=str(uuid.uuid4()),
            task_id=task.task_id,
            attempt_number=attempt_number,
            completed_steps=execution.steps,
            successful_actions=successful_actions,
            failed_actions=failed_actions,
            current_page_state=current_page_state,
            goal_progress=goal_evaluation.progress_percent,
            success_signals_found=goal_evaluation.success_signals_found,
            last_error=execution.error,
            notes=f"Attempt {attempt_number}: {'Success' if execution.success else 'Failed'}"
        )

        logger.info(f"✅ Checkpoint создан: {len(successful_actions)} успешных действий, "
                   f"{len(failed_actions)} проваленных, прогресс {goal_evaluation.progress_percent:.1%}")

        return checkpoint

    async def delete_checkpoint(self, task_id: str) -> bool:
        """
        Удалить checkpoint задачи

        Args:
            task_id: ID задачи

        Returns:
            True если удален, False если не найден
        """
        logger.info(f"🗑️  Удаление checkpoint для задачи {task_id}")

        file_path = self.checkpoints_dir / f"{task_id}_checkpoint.json"

        if not file_path.exists():
            logger.warning(f"⚠️  Checkpoint не найден для удаления: {task_id}")
            return False

        try:
            file_path.unlink()
            logger.info(f"✅ Checkpoint удален: {task_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления checkpoint: {e}", exc_info=True)
            return False

    async def get_checkpoint_summary(self, task_id: str) -> Optional[dict]:
        """
        Получить краткую информацию о checkpoint

        Args:
            task_id: ID задачи

        Returns:
            Словарь с информацией или None
        """
        checkpoint = await self.load_checkpoint(task_id)

        if not checkpoint:
            return None

        return {
            "checkpoint_id": checkpoint.checkpoint_id,
            "attempt_number": checkpoint.attempt_number,
            "goal_progress": checkpoint.goal_progress,
            "successful_actions_count": len(checkpoint.successful_actions),
            "failed_actions_count": len(checkpoint.failed_actions),
            "success_signals_found": checkpoint.success_signals_found,
            "last_error": checkpoint.last_error,
            "updated_at": checkpoint.updated_at.isoformat()
        }

    def format_checkpoint_context(self, checkpoint: Checkpoint) -> str:
        """
        Форматировать checkpoint в текстовый контекст для browser-use

        Args:
            checkpoint: Checkpoint

        Returns:
            Форматированный текст контекста
        """
        context_parts = []

        # Заголовок
        context_parts.append(f"=== Продолжение попытки #{checkpoint.attempt_number} ===")
        context_parts.append(f"Прогресс: {checkpoint.goal_progress:.0%}")
        context_parts.append("")

        # Успешные действия (последние 5)
        if checkpoint.successful_actions:
            context_parts.append("✅ Уже выполнено:")
            recent_successes = checkpoint.successful_actions[-5:]
            for i, action in enumerate(recent_successes, 1):
                context_parts.append(f"  {i}. {action.action_type}")
                if action.selector:
                    context_parts.append(f"     Селектор: {action.selector}")
                if action.input_value:
                    context_parts.append(f"     Значение: {action.input_value}")
                if action.page_url:
                    context_parts.append(f"     URL: {action.page_url}")
            context_parts.append("")

        # Проваленные действия (избегать)
        if checkpoint.failed_actions:
            context_parts.append("⚠️  НЕ РАБОТАЕТ (избегай):")
            recent_failures = checkpoint.failed_actions[-3:]
            for i, action in enumerate(recent_failures, 1):
                context_parts.append(f"  {i}. {action.action_type}")
                if action.selector:
                    context_parts.append(f"     Селектор: {action.selector}")
                if action.error:
                    context_parts.append(f"     Ошибка: {action.error}")
            context_parts.append("")

        # Найденные сигналы успеха
        if checkpoint.success_signals_found:
            context_parts.append("🎯 Найденные сигналы успеха:")
            for signal in checkpoint.success_signals_found:
                context_parts.append(f"  ✓ {signal}")
            context_parts.append("")

        # Текущее состояние
        if checkpoint.current_page_state:
            context_parts.append(f"📍 Текущая страница: {checkpoint.current_page_state.url}")
            context_parts.append("")

        context_parts.append("Продолжай выполнение с этого места.")

        return "\n".join(context_parts)
