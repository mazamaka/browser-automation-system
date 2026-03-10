"""
Pydantic схемы для API
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    """Запрос на создание задачи"""
    mini_prompt: str = Field(..., description="Короткий промпт от пользователя")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Дополнительные метаданные")


class TaskExecuteRequest(BaseModel):
    """Запрос на выполнение задачи"""
    force_new_prompt: bool = Field(False, description="Принудительно создать новый промпт")


class TaskResponse(BaseModel):
    """Ответ с информацией о задаче"""
    task_id: str
    mini_prompt: str
    status: str
    created_at: str
    updated_at: str
    executions_count: int
    system_prompt: Optional[Dict[str, Any]] = None
    last_execution: Optional[Dict[str, Any]] = None


class TaskListResponse(BaseModel):
    """Список задач"""
    tasks: List[TaskResponse]
    total: int
    limit: int
    offset: int


class ExecutionResponse(BaseModel):
    """Ответ с результатом выполнения"""
    execution_id: str
    task_id: str
    timestamp: str
    status: str
    success: bool
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    steps_count: int
    screenshots: List[str] = []
    result: Optional[Dict[str, Any]] = None


class StepResponse(BaseModel):
    """Информация о шаге выполнения"""
    step_number: int
    description: str
    success: bool
    timestamp: str
    duration_ms: Optional[int] = None
    screenshot_path: Optional[str] = None
    error: Optional[str] = None


class StatisticsResponse(BaseModel):
    """Статистика системы"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    total_executions: int
    patterns_count: int
    websites_count: int


class LearningStatsResponse(BaseModel):
    """Статистика обучения"""
    total_patterns: int
    patterns_by_type: Dict[str, int]
    total_tasks: int
    avg_success_rate: float
    tasks_with_prompts: int


class PromptOptimizeRequest(BaseModel):
    """Запрос на оптимизацию промпта"""
    task_id: str
    execution_ids: List[str] = Field(default_factory=list)


class WebSocketMessage(BaseModel):
    """Сообщение WebSocket"""
    type: str = Field(..., description="Тип сообщения: task_update, step_complete, error")
    task_id: str
    event: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    error: str
    detail: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
