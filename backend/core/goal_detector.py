"""
GoalDetector - определение достижения конечной цели задачи
"""
import re
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

from ..storage.models import (
    GoalEvaluation, Task, TaskExecution, DetailedAction
)
from ..ai.model_provider import AIModelProvider


class GoalDetector:
    """Определяет достигнута ли конечная цель задачи"""

    def __init__(self, ai_provider: AIModelProvider):
        """
        Args:
            ai_provider: AI провайдер для анализа результатов
        """
        self.ai_provider = ai_provider

    async def evaluate_goal(
        self,
        task: Task,
        execution: TaskExecution
    ) -> GoalEvaluation:
        """
        Оценить достижение цели на основе результатов выполнения

        Args:
            task: Задача с целью (mini_prompt)
            execution: Результаты выполнения

        Returns:
            GoalEvaluation с оценкой прогресса
        """
        logger.info(f"🎯 Оценка достижения цели для задачи: '{task.mini_prompt}'")

        # Определяем ожидаемые сигналы успеха на основе типа задачи
        expected_signals = self._define_success_signals(task.mini_prompt)
        logger.info(f"📋 Ожидаемые сигналы успеха: {expected_signals}")

        # Проверяем наличие сигналов в результатах
        found_signals = []
        missing_signals = []

        for signal_desc in expected_signals:
            if await self._check_signal_in_execution(signal_desc, execution):
                found_signals.append(signal_desc)
                logger.info(f"  ✅ Найден: {signal_desc}")
            else:
                missing_signals.append(signal_desc)
                logger.info(f"  ❌ Отсутствует: {signal_desc}")

        # Вычисляем прогресс
        progress_percent = len(found_signals) / len(expected_signals) if expected_signals else 0.0
        goal_achieved = progress_percent >= 1.0

        # Используем AI для анализа и предложения следующих действий
        next_actions = []
        evaluation_reasoning = ""

        if not goal_achieved:
            logger.info("🤖 Запрос AI для анализа и предложения следующих действий...")
            ai_analysis = await self._analyze_with_ai(
                task.mini_prompt,
                execution,
                found_signals,
                missing_signals
            )
            next_actions = ai_analysis.get("next_actions", [])
            evaluation_reasoning = ai_analysis.get("reasoning", "")
            logger.info(f"💡 AI предложил {len(next_actions)} следующих действий")

        # Оценка уверенности
        confidence = self._calculate_confidence(execution, found_signals, expected_signals)

        evaluation = GoalEvaluation(
            goal_achieved=goal_achieved,
            progress_percent=progress_percent,
            success_signals_found=found_signals,
            missing_signals=missing_signals,
            next_suggested_actions=next_actions,
            confidence=confidence,
            evaluation_reasoning=evaluation_reasoning
        )

        logger.info(f"📊 Оценка завершена: прогресс {progress_percent:.1%}, достигнута: {goal_achieved}")

        return evaluation

    def _define_success_signals(self, mini_prompt: str) -> List[str]:
        """
        Определить ожидаемые сигналы успеха на основе задачи

        Args:
            mini_prompt: Описание задачи

        Returns:
            Список ожидаемых сигналов
        """
        prompt_lower = mini_prompt.lower()
        signals = []

        # Регистрация / создание аккаунта
        if any(word in prompt_lower for word in ['создай', 'зарегистрируй', 'регистрация', 'sign up', 'create account']):
            if 'почт' in prompt_lower or 'email' in prompt_lower or 'mail' in prompt_lower:
                signals.extend([
                    "Найден созданный email адрес",
                    "Найден пароль для аккаунта",
                    "URL содержит 'inbox' или 'mail'",
                    "Страница показывает успешную регистрацию"
                ])
            else:
                signals.extend([
                    "Аккаунт создан",
                    "Найдены учетные данные (логин/пароль)",
                    "Страница подтверждения регистрации"
                ])

        # Вход в аккаунт
        if any(word in prompt_lower for word in ['войди', 'вход', 'login', 'sign in']):
            signals.extend([
                "Успешный вход в аккаунт",
                "URL изменился на панель управления",
                "Отображается имя пользователя"
            ])

        # Поиск информации
        if any(word in prompt_lower for word in ['найди', 'поиск', 'search', 'find']):
            signals.extend([
                "Найдены результаты поиска",
                "Извлечена нужная информация",
                "Страница с результатами отображается"
            ])

        # Заполнение формы
        if any(word in prompt_lower for word in ['заполни', 'форма', 'fill', 'form']):
            signals.extend([
                "Все поля формы заполнены",
                "Форма отправлена успешно",
                "Получено подтверждение"
            ])

        # Покупка / заказ
        if any(word in prompt_lower for word in ['купи', 'заказ', 'buy', 'order', 'корзина', 'cart']):
            signals.extend([
                "Товар добавлен в корзину",
                "Оформлен заказ",
                "Получено подтверждение заказа"
            ])

        # Реклама / кампания
        if any(word in prompt_lower for word in ['реклама', 'ads', 'campaign', 'кампания']):
            signals.extend([
                "Кампания создана",
                "Настройки рекламы сохранены",
                "Кампания запущена или в статусе черновика"
            ])

        # Если не определили тип - общие сигналы
        if not signals:
            signals.extend([
                "Задача выполнена без ошибок",
                "Достигнута конечная страница",
                "Получен ожидаемый результат"
            ])

        return signals

    async def _check_signal_in_execution(
        self,
        signal_description: str,
        execution: TaskExecution
    ) -> bool:
        """
        Проверить наличие сигнала в результатах выполнения

        Args:
            signal_description: Описание сигнала
            execution: Результаты выполнения

        Returns:
            True если сигнал найден
        """
        signal_lower = signal_description.lower()

        # Проверяем в extracted_data
        if execution.extracted_data:
            extracted_str = str(execution.extracted_data).lower()

            if 'email' in signal_lower and ('@' in extracted_str or 'email' in extracted_str):
                return True
            if 'пароль' in signal_lower or 'password' in signal_lower:
                if 'password' in extracted_str or 'пароль' in extracted_str:
                    return True
            if 'inbox' in signal_lower and 'inbox' in extracted_str:
                return True

        # Проверяем в result
        if execution.result:
            result_str = str(execution.result).lower()

            if any(keyword in result_str for keyword in ['success', 'успешно', 'complete', 'done']):
                if 'регистр' in signal_lower or 'аккаунт' in signal_lower or 'созда' in signal_lower:
                    return True

        # Проверяем URL из шагов
        if execution.steps:
            for step in execution.steps:
                if step.page_url:
                    url_lower = step.page_url.lower()

                    if 'inbox' in signal_lower and 'inbox' in url_lower:
                        return True
                    if 'mail' in signal_lower and 'mail' in url_lower:
                        return True
                    if 'dashboard' in signal_lower and ('dashboard' in url_lower or 'home' in url_lower):
                        return True

        # Проверяем успешность выполнения
        if 'без ошибок' in signal_lower and execution.success:
            return True

        return False

    async def _analyze_with_ai(
        self,
        mini_prompt: str,
        execution: TaskExecution,
        found_signals: List[str],
        missing_signals: List[str]
    ) -> Dict[str, Any]:
        """
        Использовать AI для анализа и предложения следующих действий

        Args:
            mini_prompt: Цель задачи
            execution: Результаты выполнения
            found_signals: Найденные сигналы
            missing_signals: Отсутствующие сигналы

        Returns:
            Словарь с reasoning и next_actions
        """
        # Формируем промпт для AI
        analysis_prompt = f"""
Задача: {mini_prompt}

Найденные сигналы успеха:
{self._format_list(found_signals) if found_signals else "Нет"}

Отсутствующие сигналы:
{self._format_list(missing_signals)}

Последняя ошибка: {execution.error if execution.error else "Нет"}

Выполненные шаги: {len(execution.steps)}

Проанализируй результаты и предложи 2-3 конкретных следующих действия для достижения цели.
Ответь в формате:

REASONING: [краткий анализ ситуации]
NEXT_ACTIONS:
1. [конкретное действие]
2. [конкретное действие]
3. [конкретное действие]
"""

        try:
            response = await self.ai_provider.generate_response(
                prompt=analysis_prompt,
                system_prompt="Ты опытный аналитик автоматизации браузера. Анализируй результаты и предлагай конкретные, выполнимые действия."
            )

            # Парсим ответ
            reasoning = ""
            next_actions = []

            if "REASONING:" in response:
                reasoning_part = response.split("REASONING:")[1].split("NEXT_ACTIONS:")[0].strip()
                reasoning = reasoning_part

            if "NEXT_ACTIONS:" in response:
                actions_part = response.split("NEXT_ACTIONS:")[1].strip()
                # Извлекаем пронумерованные действия
                action_lines = [line.strip() for line in actions_part.split('\n') if line.strip()]
                for line in action_lines:
                    # Удаляем номера в начале
                    clean_line = re.sub(r'^\d+\.\s*', '', line)
                    if clean_line:
                        next_actions.append(clean_line)

            return {
                "reasoning": reasoning,
                "next_actions": next_actions[:3]  # Максимум 3 действия
            }

        except Exception as e:
            logger.warning(f"⚠️  Не удалось получить AI анализ: {e}")
            return {
                "reasoning": "AI анализ недоступен",
                "next_actions": ["Повторить попытку", "Проверить последнюю ошибку", "Попробовать альтернативный подход"]
            }

    def _calculate_confidence(
        self,
        execution: TaskExecution,
        found_signals: List[str],
        expected_signals: List[str]
    ) -> float:
        """
        Вычислить уверенность в оценке

        Args:
            execution: Результаты выполнения
            found_signals: Найденные сигналы
            expected_signals: Ожидаемые сигналы

        Returns:
            Уверенность от 0.0 до 1.0
        """
        confidence = 0.0

        # Базовая уверенность от найденных сигналов
        if expected_signals:
            confidence = len(found_signals) / len(expected_signals)

        # Увеличиваем уверенность если нет ошибок
        if execution.success and not execution.error:
            confidence = min(1.0, confidence + 0.2)

        # Уменьшаем если есть ошибка
        if execution.error:
            confidence = max(0.0, confidence - 0.3)

        # Уменьшаем если мало шагов выполнено
        if len(execution.steps) < 3:
            confidence = max(0.0, confidence - 0.2)

        return min(1.0, max(0.0, confidence))

    def _format_list(self, items: List[str]) -> str:
        """Форматировать список для промпта"""
        return "\n".join(f"- {item}" for item in items)
