"""
TokenUsageTracker - отслеживание использования токенов и подсчёт стоимости
"""
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


# Цены за 1M токенов (Claude Sonnet 4.0)
PRICING = {
    "claude-sonnet-4-0": {
        "input": 3.0,      # $3 за 1M input tokens
        "output": 15.0,    # $15 за 1M output tokens
        "cached": 0.30     # $0.30 за 1M cached tokens
    },
    "claude-sonnet-4-20250514": {
        "input": 3.0,
        "output": 15.0,
        "cached": 0.30
    },
    # Fallback для других моделей
    "default": {
        "input": 3.0,
        "output": 15.0,
        "cached": 0.30
    }
}


class TokenUsageTracker(BaseCallbackHandler):
    """
    Callback для отслеживания использования токенов через LangChain
    """

    def __init__(self, model_name: str = "claude-sonnet-4-0"):
        """
        Args:
            model_name: Название модели для определения цен
        """
        super().__init__()
        self.model_name = model_name

        # Статистика
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cached_tokens = 0
        self.total_calls = 0

        # История вызовов
        self.calls_history = []

        # Время начала
        self.started_at = datetime.now()

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """
        Вызывается при завершении LLM вызова

        Args:
            response: Результат от LLM
        """
        try:
            # Извлекаем usage из response
            if hasattr(response, 'llm_output') and response.llm_output:
                usage = response.llm_output.get('usage', {})

                # Anthropic формат
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)

                # Кэшированные токены (если есть)
                cache_read_tokens = usage.get('cache_read_input_tokens', 0)
                cache_creation_tokens = usage.get('cache_creation_input_tokens', 0)

                # Обновляем статистику
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                self.total_cached_tokens += cache_read_tokens
                self.total_calls += 1

                # Сохраняем в историю
                call_data = {
                    "timestamp": datetime.now().isoformat(),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cached_tokens": cache_read_tokens,
                    "cache_creation_tokens": cache_creation_tokens,
                    "total_tokens": input_tokens + output_tokens
                }
                self.calls_history.append(call_data)

                logger.debug(f"📊 LLM Call #{self.total_calls}: "
                           f"input={input_tokens}, output={output_tokens}, cached={cache_read_tokens}")

        except Exception as e:
            logger.warning(f"⚠️  Не удалось извлечь usage: {e}")

    def get_pricing(self) -> Dict[str, float]:
        """Получить цены для текущей модели"""
        return PRICING.get(self.model_name, PRICING["default"])

    def calculate_cost(self) -> Dict[str, float]:
        """
        Рассчитать стоимость использования

        Returns:
            Словарь с breakdown стоимости
        """
        pricing = self.get_pricing()

        # Стоимость в долларах
        input_cost = (self.total_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * pricing["output"]
        cached_cost = (self.total_cached_tokens / 1_000_000) * pricing["cached"]

        total_cost = input_cost + output_cost + cached_cost

        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "cached_cost": round(cached_cost, 6),
            "total_cost": round(total_cost, 6),
            "currency": "USD"
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Получить полную статистику использования

        Returns:
            Словарь со статистикой
        """
        costs = self.calculate_cost()
        duration = (datetime.now() - self.started_at).total_seconds()

        return {
            "tokens": {
                "input": self.total_input_tokens,
                "output": self.total_output_tokens,
                "cached": self.total_cached_tokens,
                "total": self.total_input_tokens + self.total_output_tokens
            },
            "costs": costs,
            "calls": {
                "total": self.total_calls,
                "history": self.calls_history
            },
            "duration_seconds": round(duration, 2),
            "model": self.model_name,
            "pricing": self.get_pricing()
        }

    def log_summary(self):
        """Вывести итоговую статистику в лог"""
        summary = self.get_summary()

        logger.info("=" * 60)
        logger.info("📊 Token Usage Summary")
        logger.info("=" * 60)
        logger.info(f"🤖 Model: {summary['model']}")
        logger.info(f"⏱️  Duration: {summary['duration_seconds']}s")
        logger.info(f"📞 Total LLM Calls: {summary['calls']['total']}")
        logger.info("")
        logger.info("🎫 Tokens:")
        logger.info(f"  Input:  {summary['tokens']['input']:,}")
        logger.info(f"  Output: {summary['tokens']['output']:,}")
        logger.info(f"  Cached: {summary['tokens']['cached']:,}")
        logger.info(f"  Total:  {summary['tokens']['total']:,}")
        logger.info("")
        logger.info("💰 Cost Breakdown:")
        logger.info(f"  Input:  ${summary['costs']['input_cost']:.6f}")
        logger.info(f"  Output: ${summary['costs']['output_cost']:.6f}")
        logger.info(f"  Cached: ${summary['costs']['cached_cost']:.6f}")
        logger.info(f"  TOTAL:  ${summary['costs']['total_cost']:.6f} USD")
        logger.info("=" * 60)


class CostEstimator:
    """Утилита для оценки стоимости до выполнения"""

    @staticmethod
    def estimate_cost(
        prompt_length: int,
        expected_output_length: int = 500,
        model_name: str = "claude-sonnet-4-0"
    ) -> Dict[str, Any]:
        """
        Оценить стоимость выполнения

        Args:
            prompt_length: Длина промпта в символах
            expected_output_length: Ожидаемая длина ответа
            model_name: Название модели

        Returns:
            Оценка стоимости
        """
        # Приблизительная конверсия: 1 токен ≈ 4 символа
        estimated_input_tokens = prompt_length // 4
        estimated_output_tokens = expected_output_length // 4

        pricing = PRICING.get(model_name, PRICING["default"])

        input_cost = (estimated_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (estimated_output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        return {
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_total_tokens": estimated_input_tokens + estimated_output_tokens,
            "estimated_cost": round(total_cost, 6),
            "currency": "USD",
            "note": "This is a rough estimate. Actual cost may vary."
        }
