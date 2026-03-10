"""
Контроллер для управления браузером через browser-use
"""
import asyncio
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from pathlib import Path
from browser_use import Agent, Browser
from loguru import logger


class BrowserController:
    """Контроллер для управления браузером через browser-use"""

    def __init__(
        self,
        headless: bool = False,
        screenshots_dir: str = "data/screenshots"
    ):
        self.headless = headless
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        # Browser-use управляет браузером сам, не нужно инициализировать Playwright вручную
        self._agent: Optional[Agent] = None

        # Колбэки для событий
        self._on_step_callback: Optional[Callable] = None
        self._on_action_callback: Optional[Callable] = None
    
    async def initialize(self):
        """Инициализация браузера (browser-use управляет браузером сам)"""
        logger.info("✅ BrowserController готов (browser-use управляет браузером)")

    async def close(self):
        """Закрытие браузера (browser-use управляет браузером сам)"""
        logger.info("✅ BrowserController завершен (browser-use управляет браузером)")
    
    async def execute_with_browser_use(
        self,
        task: str,
        llm_model,
        max_steps: int = 50
    ) -> Dict[str, Any]:
        """
        Выполнить задачу через browser-use агента

        Args:
            task: Задача для выполнения
            llm_model: LLM модель (ChatAnthropic из browser_use)
            max_steps: Максимальное количество шагов

        Returns:
            Dict с результатами выполнения
        """
        logger.info(f"🎯 Начало выполнения задачи: {task[:100]}...")

        try:
            # Создаем браузер с highlight_elements
            browser = Browser(
                headless=self.headless,
                highlight_elements=True  # Включаем визуализацию кликов
            )
            logger.info("🌐 Браузер создан с highlight_elements=True для визуализации кликов")

            # Создаем агента browser-use
            logger.info(f"🤖 Создание browser-use агента (max_steps={max_steps})...")
            agent = Agent(
                task=task,
                llm=llm_model,
                browser=browser,
                max_actions_per_step=10,  # Максимум действий за шаг
                max_failures=3,  # Максимум повторных попыток
                use_vision=True,  # ✅ Использовать vision для анализа страниц
                flash_mode=False,  # Полный режим с анализом
                use_thinking=True,  # Включить рассуждения агента
                generate_gif=False,  # Не генерировать GIF
                calculate_cost=True  # ✅ Включить подсчёт стоимости встроенный в browser-use
            )
            logger.info("✅ Агент создан с use_vision=True и calculate_cost=True")

            # Выполняем задачу
            logger.info("▶️  Запуск выполнения задачи через browser-use...")
            logger.info(f"🔧 Параметры Agent: use_vision=True, calculate_cost=True, max_steps={max_steps}")
            logger.info(f"🔧 LLM модель: {llm_model.__class__.__name__}")

            try:
                history = await agent.run(max_steps=max_steps)  # agent.run() возвращает AgentHistoryList
                logger.info(f"✅ Задача выполнена!")
            except Exception as e:
                logger.error(f"❌ Ошибка при выполнении agent.run(): {e}")
                logger.error(f"🔍 Тип ошибки: {type(e).__name__}")
                if "credit balance" in str(e).lower() or "api" in str(e).lower():
                    logger.error("💳 Ошибка связана с API ключом или балансом!")
                    logger.error("🔑 Проверьте ANTHROPIC_API_KEY в .env файле")
                    logger.error("💰 Проверьте баланс на https://console.anthropic.com/settings/billing")
                raise

            # Получаем результаты через history API
            logger.info("📊 Обработка результатов через history API...")

            # Проверяем успешность выполнения
            is_successful = history.is_successful() if hasattr(history, 'is_successful') else True
            final_result = history.final_result() if hasattr(history, 'final_result') else "Задача выполнена"

            # Получаем данные из history с фильтрацией None
            screenshots = history.screenshot_paths() if hasattr(history, 'screenshot_paths') else []
            screenshots = [s for s in screenshots if s is not None]  # Фильтруем None

            extracted_data = history.extracted_content() if hasattr(history, 'extracted_content') else {}
            # Если extracted_content вернул список вместо dict, конвертируем
            if isinstance(extracted_data, list):
                extracted_data = {}

            urls = history.urls() if hasattr(history, 'urls') else []
            urls = [u for u in urls if u is not None]  # Фильтруем None

            result_dict = {
                "success": is_successful if is_successful is not None else True,
                "final_result": final_result,
                "steps": self._extract_steps_from_history(history),
                "screenshots": screenshots,
                "extracted_data": extracted_data,
                "urls": urls,
                "actions": history.action_names() if hasattr(history, 'action_names') else [],
                "errors": history.errors() if hasattr(history, 'errors') else [],
                "has_errors": history.has_errors() if hasattr(history, 'has_errors') else False
            }

            logger.info(f"✅ Результаты обработаны: steps={len(result_dict['steps'])}, urls={len(result_dict['urls'])}, success={result_dict['success']}")
            logger.info("💰 Подсчёт стоимости работает через calculate_cost=True в Agent")
            return result_dict

        except Exception as e:
            logger.error(f"❌ Ошибка при выполнении задачи: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "steps": [],
                "screenshots": [],
                "extracted_data": {},
                "urls": [],
                "actions": [],
                "errors": [str(e)]
            }

    def _extract_steps_from_history(self, history) -> List[Dict[str, Any]]:
        """
        Извлечь шаги выполнения из history API с детальной информацией

        Args:
            history: AgentHistoryList объект

        Returns:
            Список шагов с детальной информацией о действиях
        """
        steps = []

        try:
            # Получаем мысли модели
            thoughts = history.model_thoughts() if hasattr(history, 'model_thoughts') else []
            # Получаем действия модели (это AgentStepInfo объекты)
            actions = history.model_actions() if hasattr(history, 'model_actions') else []
            # Получаем результаты действий
            action_results = history.action_results() if hasattr(history, 'action_results') else []

            logger.info(f"📊 Извлечение из history: {len(thoughts)} мыслей, {len(actions)} действий")

            # Объединяем всё в шаги
            max_len = max(len(thoughts), len(actions), len(action_results))

            for idx in range(max_len):
                thought = str(thoughts[idx]) if idx < len(thoughts) else ""
                action = actions[idx] if idx < len(actions) else None
                result = str(action_results[idx]) if idx < len(action_results) else ""

                # Извлекаем детали действия
                action_details = self._extract_action_details(action) if action else {}

                step = {
                    "step_number": idx + 1,
                    "thought": thought,
                    "action": action_details.get("action_type", str(action) if action else ""),
                    "result": result,
                    "action_details": action_details  # Добавляем детали для дальнейшего использования
                }
                steps.append(step)

            logger.info(f"✅ Извлечено {len(steps)} шагов из history")

        except Exception as e:
            logger.warning(f"⚠️  Не удалось извлечь детали шагов: {e}", exc_info=True)

        return steps

    def _extract_action_details(self, action) -> Dict[str, Any]:
        """
        Извлечь детальную информацию о действии

        Args:
            action: Объект действия из browser-use history

        Returns:
            Словарь с деталями действия
        """
        details = {
            "action_type": "unknown",
            "selector": None,
            "input_value": None,
            "coordinates": None,
            "url": None
        }

        try:
            # Преобразуем action в строку для анализа
            action_str = str(action)

            # Определяем тип действия по ключевым словам
            action_lower = action_str.lower()

            if 'click' in action_lower:
                details["action_type"] = "click"
            elif 'fill' in action_lower or 'input' in action_lower or 'type' in action_lower:
                details["action_type"] = "fill"
            elif 'navigate' in action_lower or 'go to' in action_lower:
                details["action_type"] = "navigate"
            elif 'scroll' in action_lower:
                details["action_type"] = "scroll"
            elif 'wait' in action_lower:
                details["action_type"] = "wait"
            elif 'extract' in action_lower or 'get' in action_lower:
                details["action_type"] = "extract"

            # Пытаемся извлечь селектор (если есть атрибут selector)
            if hasattr(action, 'selector'):
                details["selector"] = str(action.selector)
            elif hasattr(action, 'xpath'):
                details["selector"] = str(action.xpath)

            # Извлекаем введенное значение для fill действий
            if details["action_type"] == "fill":
                if hasattr(action, 'value'):
                    details["input_value"] = str(action.value)
                elif hasattr(action, 'text'):
                    details["input_value"] = str(action.text)

            # Извлекаем URL для navigate действий
            if details["action_type"] == "navigate":
                if hasattr(action, 'url'):
                    details["url"] = str(action.url)

            # Извлекаем координаты для click действий
            if details["action_type"] == "click":
                if hasattr(action, 'x') and hasattr(action, 'y'):
                    details["coordinates"] = (int(action.x), int(action.y))

        except Exception as e:
            logger.debug(f"Не удалось извлечь детали действия: {e}")

        return details
    
    def set_on_step_callback(self, callback: Callable):
        """Установить колбэк для событий шагов"""
        self._on_step_callback = callback

    def set_on_action_callback(self, callback: Callable):
        """Установить колбэк для событий действий"""
        self._on_action_callback = callback
