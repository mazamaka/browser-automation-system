#!/usr/bin/env python3
"""
Скрипт для проверки API ключа Anthropic
"""
import os
import sys
import asyncio
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

async def check_api_key():
    """Проверить работоспособность API ключа"""

    # Загружаем .env
    load_dotenv()

    api_key = os.getenv('ANTHROPIC_API_KEY')

    print("=" * 60)
    print("🔍 Проверка API ключа Anthropic")
    print("=" * 60)

    if not api_key:
        print("❌ ОШИБКА: ANTHROPIC_API_KEY не найден в .env файле!")
        print("\n📝 Создайте .env файл с содержимым:")
        print("   ANTHROPIC_API_KEY=sk-ant-...")
        return False

    print(f"✅ API ключ найден")
    print(f"   Начало ключа: {api_key[:10]}...")
    print(f"   Длина ключа: {len(api_key)} символов")

    # Проверяем формат
    if not api_key.startswith('sk-ant-'):
        print("\n⚠️  ВНИМАНИЕ: Ключ не начинается с 'sk-ant-'")
        print("   Убедитесь что это правильный ключ Anthropic")

    print("\n🔧 Тестируем подключение к Anthropic API...")

    try:
        client = AsyncAnthropic(api_key=api_key)

        # Простой тестовый запрос
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Say 'OK'"}
            ]
        )

        print("✅ API работает!")
        print(f"   Ответ: {response.content[0].text}")
        print(f"   Токены: input={response.usage.input_tokens}, output={response.usage.output_tokens}")

        print("\n💰 Баланс API ключа в норме")
        print("   API доступен для использования")

        return True

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ ОШИБКА при вызове API:")
        print(f"   {error_msg}")

        if "credit balance" in error_msg.lower():
            print("\n💳 Проблема с балансом!")
            print("   1. Зайдите на https://console.anthropic.com/settings/billing")
            print("   2. Проверьте текущий баланс")
            print("   3. Пополните кредиты (минимум $5)")

        elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            print("\n🔑 Проблема с ключом!")
            print("   1. Проверьте что ключ правильный")
            print("   2. Создайте новый ключ на https://console.anthropic.com/settings/keys")
            print("   3. Обновите .env файл")

        else:
            print("\n🔍 Неизвестная ошибка:")
            print(f"   Тип: {type(e).__name__}")

        return False

if __name__ == "__main__":
    print("\n")
    result = asyncio.run(check_api_key())
    print("\n" + "=" * 60)

    if result:
        print("🎉 Всё в порядке! Можно использовать систему.")
        sys.exit(0)
    else:
        print("⚠️  Исправьте проблемы выше и повторите проверку.")
        sys.exit(1)
