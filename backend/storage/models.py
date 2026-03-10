"""
Модели данных для системы автоматизации браузера
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Статус выполнения задачи"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AIModelType(str, Enum):
    """Типы AI моделей"""
    CLAUDE_SONNET = "claude-sonnet-4-20250514"
    CLAUDE_OPUS = "claude-3-opus-20240229"
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo"
    BROWSER_USE = "bu-1-0"


class StepAction(BaseModel):
    """Действие в рамках шага выполнения"""
    action_type: str = Field(..., description="Тип действия: click, fill, navigate, extract")
    selector: Optional[str] = Field(None, description="CSS селектор элемента")
    value: Optional[str] = Field(None, description="Значение для заполнения")
    url: Optional[str] = Field(None, description="URL для навигации")
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = Field(True, description="Успешность выполнения действия")
    error: Optional[str] = Field(None, description="Ошибка при выполнении")


class ExecutionStep(BaseModel):
    """Шаг выполнения задачи"""
    step_number: int
    description: str
    actions: List[StepAction] = Field(default_factory=list)
    screenshot_path: Optional[str] = None
    page_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_ms: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


class TaskExecution(BaseModel):
    """Выполнение задачи"""
    execution_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    status: TaskStatus
    steps: List[ExecutionStep] = Field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    success: bool = False
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    screenshots: List[str] = Field(default_factory=list)
    extracted_data: Optional[Dict[str, Any]] = None


class SystemPrompt(BaseModel):
    """Системный промпт с детальными инструкциями"""
    prompt_id: str
    content: str = Field(..., description="Полный текст системного промпта")
    steps_count: int = Field(0, description="Количество шагов в промпте")
    selectors: List[str] = Field(default_factory=list, description="Использованные селекторы")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: int = Field(1, description="Версия промпта")
    success_rate: float = Field(0.0, description="Процент успешных выполнений")
    executions_count: int = Field(0, description="Количество выполнений")


class Task(BaseModel):
    """Основная задача"""
    task_id: str
    mini_prompt: str = Field(..., description="Короткий промпт от пользователя")
    system_prompt: Optional[SystemPrompt] = None
    status: TaskStatus = Field(TaskStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    executions: List[TaskExecution] = Field(default_factory=list)
    ai_model_for_analysis: AIModelType = Field(AIModelType.CLAUDE_SONNET)
    ai_model_for_execution: AIModelType = Field(AIModelType.BROWSER_USE)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PromptOptimization(BaseModel):
    """Оптимизация промпта на основе результатов"""
    optimization_id: str
    original_prompt_id: str
    optimized_prompt: str
    reason: str = Field(..., description="Причина оптимизации")
    improvements: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    success_rate_before: float
    success_rate_after: Optional[float] = None


class LearningPattern(BaseModel):
    """Паттерн обучения - успешная последовательность действий"""
    pattern_id: str
    task_type: str = Field(..., description="Тип задачи (login, form_fill, navigation)")
    description: str
    successful_steps: List[ExecutionStep]
    common_selectors: List[str] = Field(default_factory=list)
    success_count: int = Field(1)
    last_used: datetime = Field(default_factory=datetime.now)
    websites: List[str] = Field(default_factory=list, description="Сайты где работает паттерн")


class TaskSimilarity(BaseModel):
    """Схожесть между задачами"""
    task_id_1: str
    task_id_2: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    common_keywords: List[str] = Field(default_factory=list)
    recommended_prompt: Optional[str] = None


class WebsiteContext(BaseModel):
    """Контекст сайта для улучшения выполнения"""
    website_url: str
    common_selectors: Dict[str, str] = Field(default_factory=dict)
    page_structure: Optional[Dict[str, Any]] = None
    last_analyzed: datetime = Field(default_factory=datetime.now)
    success_rate: float = Field(0.0)
    known_issues: List[str] = Field(default_factory=list)


class DetailedAction(BaseModel):
    """Детальное действие с всей информацией из browser-use"""
    action_type: str = Field(..., description="Тип действия: click, fill, navigate, wait, scroll, extract")
    selector: Optional[str] = Field(None, description="CSS селектор элемента")
    xpath: Optional[str] = Field(None, description="XPath элемента")
    coordinates: Optional[tuple[int, int]] = Field(None, description="Координаты клика (x, y)")
    input_value: Optional[str] = Field(None, description="Введенное значение (для fill)")
    element_text: Optional[str] = Field(None, description="Текст элемента")
    element_attributes: Optional[Dict[str, Any]] = Field(None, description="Атрибуты элемента")
    screenshot_path: Optional[str] = Field(None, description="Путь к скриншоту действия")
    success: bool = Field(True, description="Успешность выполнения")
    error: Optional[str] = Field(None, description="Ошибка при выполнении")
    page_url: Optional[str] = Field(None, description="URL страницы")
    page_title: Optional[str] = Field(None, description="Заголовок страницы")
    timestamp: datetime = Field(default_factory=datetime.now)
    thought: Optional[str] = Field(None, description="Рассуждение агента перед действием")
    result: Optional[str] = Field(None, description="Результат действия")


class PageState(BaseModel):
    """Состояние страницы в момент checkpoint"""
    url: str = Field(..., description="Текущий URL")
    title: Optional[str] = Field(None, description="Заголовок страницы")
    cookies: Optional[List[Dict[str, Any]]] = Field(None, description="Cookies")
    local_storage: Optional[Dict[str, str]] = Field(None, description="LocalStorage")
    session_storage: Optional[Dict[str, str]] = Field(None, description="SessionStorage")
    viewport: Optional[Dict[str, int]] = Field(None, description="Размер viewport")
    screenshot_path: Optional[str] = Field(None, description="Скриншот страницы")
    dom_snapshot: Optional[str] = Field(None, description="Упрощенный снимок DOM")


class Checkpoint(BaseModel):
    """Checkpoint выполнения задачи - точка сохранения прогресса"""
    checkpoint_id: str
    task_id: str
    attempt_number: int = Field(..., description="Номер попытки выполнения")
    completed_steps: List[ExecutionStep] = Field(default_factory=list, description="Завершенные шаги")
    successful_actions: List[DetailedAction] = Field(default_factory=list, description="Успешные действия")
    failed_actions: List[DetailedAction] = Field(default_factory=list, description="Проваленные действия")
    current_page_state: Optional[PageState] = Field(None, description="Текущее состояние страницы")
    goal_progress: float = Field(0.0, ge=0.0, le=1.0, description="Прогресс к цели (0.0-1.0)")
    success_signals_found: List[str] = Field(default_factory=list, description="Найденные сигналы успеха")
    last_error: Optional[str] = Field(None, description="Последняя ошибка")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = Field(None, description="Заметки о прогрессе")


class GoalEvaluation(BaseModel):
    """Оценка достижения конечной цели задачи"""
    goal_achieved: bool = Field(..., description="Достигнута ли цель полностью")
    progress_percent: float = Field(..., ge=0.0, le=1.0, description="Процент выполнения")
    success_signals_found: List[str] = Field(default_factory=list, description="Найденные сигналы успеха")
    missing_signals: List[str] = Field(default_factory=list, description="Отсутствующие сигналы")
    next_suggested_actions: List[str] = Field(default_factory=list, description="Предложенные следующие действия")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность в оценке")
    evaluation_reasoning: Optional[str] = Field(None, description="Объяснение оценки")
    evaluated_at: datetime = Field(default_factory=datetime.now)
