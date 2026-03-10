"""
FastAPI маршруты
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime

from .schemas import (
    TaskCreateRequest, TaskExecuteRequest, TaskResponse,
    TaskListResponse, ExecutionResponse, StatisticsResponse,
    LearningStatsResponse, ErrorResponse
)
from ..core.agent_manager import AgentManager
from ..storage.prompt_store import PromptStore
from ..ai.model_provider import ModelFactory


# Роутер для задач
tasks_router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Глобальные зависимости (будут инициализированы в main.py)
_agent_manager: Optional[AgentManager] = None
_prompt_store: Optional[PromptStore] = None


def init_routes(agent_manager: AgentManager, prompt_store: PromptStore):
    """Инициализация роутов с зависимостями"""
    global _agent_manager, _prompt_store
    _agent_manager = agent_manager
    _prompt_store = prompt_store


@tasks_router.post("/create", response_model=TaskResponse)
async def create_task(request: TaskCreateRequest):
    """Создать новую задачу"""
    try:
        task = await _agent_manager.create_task(
            mini_prompt=request.mini_prompt,
            metadata=request.metadata
        )
        
        return TaskResponse(
            task_id=task.task_id,
            mini_prompt=task.mini_prompt,
            status=task.status,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            executions_count=len(task.executions),
            system_prompt=task.system_prompt.model_dump() if task.system_prompt else None,
            last_execution=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tasks_router.post("/{task_id}/run", response_model=ExecutionResponse)
async def run_task(
    task_id: str,
    request: TaskExecuteRequest,
    background_tasks: BackgroundTasks
):
    """Запустить выполнение задачи"""
    try:
        # Запускаем выполнение в фоне
        execution = await _agent_manager.execute_task(
            task_id=task_id,
            force_new_prompt=request.force_new_prompt
        )
        
        return ExecutionResponse(
            execution_id=execution.execution_id,
            task_id=task_id,
            timestamp=execution.timestamp.isoformat(),
            status=execution.status,
            success=execution.success,
            error=execution.error,
            duration_ms=execution.duration_ms,
            steps_count=len(execution.steps),
            screenshots=execution.screenshots,
            result=execution.result
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tasks_router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Получить информацию о задаче"""
    try:
        task_info = await _agent_manager.get_task_status(task_id)
        
        if not task_info:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        return TaskResponse(**task_info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tasks_router.get("/", response_model=TaskListResponse)
async def list_tasks(
    limit: int = 20,
    offset: int = 0
):
    """Получить список всех задач"""
    try:
        tasks = await _prompt_store.get_all_tasks(limit=limit, offset=offset)
        
        task_responses = []
        for task in tasks:
            task_responses.append(TaskResponse(
                task_id=task.task_id,
                mini_prompt=task.mini_prompt,
                status=task.status,
                created_at=task.created_at.isoformat(),
                updated_at=task.updated_at.isoformat(),
                executions_count=len(task.executions),
                system_prompt=task.system_prompt.model_dump() if task.system_prompt else None,
                last_execution=task.executions[-1].model_dump() if task.executions else None
            ))
        
        return TaskListResponse(
            tasks=task_responses,
            total=len(task_responses),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tasks_router.get("/{task_id}/executions", response_model=List[ExecutionResponse])
async def get_task_executions(task_id: str):
    """Получить все выполнения задачи"""
    try:
        executions = await _prompt_store.get_task_executions(task_id)
        
        return [
            ExecutionResponse(
                execution_id=exec.execution_id,
                task_id=task_id,
                timestamp=exec.timestamp.isoformat(),
                status=exec.status,
                success=exec.success,
                error=exec.error,
                duration_ms=exec.duration_ms,
                steps_count=len(exec.steps),
                screenshots=exec.screenshots,
                result=exec.result
            )
            for exec in executions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Роутер для статистики
stats_router = APIRouter(prefix="/api/stats", tags=["statistics"])


@stats_router.get("/general", response_model=StatisticsResponse)
async def get_statistics():
    """Получить общую статистику"""
    try:
        stats = await _prompt_store.get_statistics()
        return StatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@stats_router.get("/learning", response_model=LearningStatsResponse)
async def get_learning_statistics():
    """Получить статистику обучения"""
    try:
        from ..core.learning_engine import LearningEngine
        learning_engine = LearningEngine(_prompt_store)
        stats = await learning_engine.get_learning_statistics()
        return LearningStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Роутер для промптов
prompts_router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@prompts_router.get("/{task_id}")
async def get_task_prompt(task_id: str):
    """Получить системный промпт задачи"""
    try:
        task = await _prompt_store.load_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        if not task.system_prompt:
            raise HTTPException(status_code=404, detail="У задачи нет системного промпта")
        
        return task.system_prompt.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@prompts_router.put("/{task_id}")
async def update_task_prompt(task_id: str, prompt_content: dict):
    """Обновить системный промпт задачи вручную"""
    try:
        task = await _prompt_store.load_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        if task.system_prompt:
            task.system_prompt.content = prompt_content.get("content", task.system_prompt.content)
            task.system_prompt.updated_at = datetime.now()
            task.system_prompt.version += 1
        
        await _prompt_store.save_task(task)
        
        return {"success": True, "message": "Промпт обновлен"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Роутер для checkpoint
checkpoint_router = APIRouter(prefix="/api/checkpoints", tags=["checkpoints"])


@checkpoint_router.get("/{task_id}")
async def get_checkpoint(task_id: str):
    """Получить checkpoint задачи"""
    try:
        checkpoint = await _agent_manager.checkpoint_manager.load_checkpoint(task_id)

        if not checkpoint:
            raise HTTPException(status_code=404, detail="Checkpoint не найден")

        return checkpoint.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@checkpoint_router.get("/{task_id}/summary")
async def get_checkpoint_summary(task_id: str):
    """Получить краткую информацию о checkpoint"""
    try:
        summary = await _agent_manager.checkpoint_manager.get_checkpoint_summary(task_id)

        if not summary:
            raise HTTPException(status_code=404, detail="Checkpoint не найден")

        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@checkpoint_router.delete("/{task_id}")
async def delete_checkpoint(task_id: str):
    """Удалить checkpoint задачи (сбросить прогресс)"""
    try:
        success = await _agent_manager.checkpoint_manager.delete_checkpoint(task_id)

        if not success:
            raise HTTPException(status_code=404, detail="Checkpoint не найден")

        return {"success": True, "message": "Checkpoint удален"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@checkpoint_router.post("/{task_id}/continue")
async def continue_from_checkpoint(task_id: str, background_tasks: BackgroundTasks):
    """Продолжить выполнение задачи с checkpoint"""
    try:
        # Проверяем наличие checkpoint
        checkpoint = await _agent_manager.checkpoint_manager.load_checkpoint(task_id)

        if not checkpoint:
            raise HTTPException(status_code=404, detail="Checkpoint не найден. Запустите задачу с помощью /tasks/{task_id}/run")

        # Запускаем выполнение в фоне
        background_tasks.add_task(_agent_manager.execute_task, task_id)

        return {
            "success": True,
            "message": f"Продолжение выполнения с попытки #{checkpoint.attempt_number + 1}",
            "current_progress": checkpoint.goal_progress
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Объединяем все роутеры
def get_all_routers():
    """Получить все роутеры приложения"""
    return [tasks_router, stats_router, prompts_router, checkpoint_router]
