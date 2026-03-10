"""
Хранилище промптов и задач в JSON файлах
"""
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import aiofiles
from loguru import logger
from .models import Task, TaskExecution, SystemPrompt, LearningPattern, WebsiteContext


class PromptStore:
    """Класс для работы с хранилищем промптов"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.prompts_dir = self.data_dir / "prompts"
        self.executions_dir = self.data_dir / "executions"
        self.screenshots_dir = self.data_dir / "screenshots"
        self.patterns_dir = self.data_dir / "patterns"
        self.websites_dir = self.data_dir / "websites"
        
        # Создаем директории если не существуют
        self._init_directories()
    
    def _init_directories(self):
        """Инициализация директорий"""
        for directory in [
            self.prompts_dir,
            self.executions_dir,
            self.screenshots_dir,
            self.patterns_dir,
            self.websites_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def save_task(self, task: Task) -> bool:
        """Сохранить задачу в файл"""
        try:
            file_path = self.prompts_dir / f"{task.task_id}.json"
            task_dict = task.model_dump(mode='json')
            
            # Преобразуем datetime в строки
            task_dict = self._serialize_datetimes(task_dict)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(task_dict, indent=2, ensure_ascii=False))
            
            return True
        except Exception as e:
            print(f"Ошибка сохранения задачи: {e}")
            return False
    
    async def load_task(self, task_id: str) -> Optional[Task]:
        """Загрузить задачу из файла"""
        try:
            file_path = self.prompts_dir / f"{task_id}.json"
            
            if not file_path.exists():
                return None
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                task_dict = json.loads(content)
            
            # Преобразуем строки обратно в datetime
            task_dict = self._deserialize_datetimes(task_dict)
            
            return Task(**task_dict)
        except Exception as e:
            print(f"Ошибка загрузки задачи: {e}")
            return None
    
    async def get_all_tasks(self, limit: int = 100, offset: int = 0) -> List[Task]:
        """Получить все задачи"""
        tasks = []
        
        task_files = sorted(
            self.prompts_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for file_path in task_files[offset:offset + limit]:
            task = await self.load_task(file_path.stem)
            if task:
                tasks.append(task)
        
        return tasks
    
    async def save_execution(self, task_id: str, execution: TaskExecution) -> bool:
        """Сохранить результат выполнения"""
        try:
            file_path = self.executions_dir / f"{task_id}_{execution.execution_id}.json"
            execution_dict = execution.model_dump(mode='json')
            execution_dict = self._serialize_datetimes(execution_dict)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(execution_dict, indent=2, ensure_ascii=False))
            
            return True
        except Exception as e:
            print(f"Ошибка сохранения выполнения: {e}")
            return False
    
    async def get_task_executions(self, task_id: str) -> List[TaskExecution]:
        """Получить все выполнения задачи"""
        executions = []
        
        pattern = f"{task_id}_*.json"
        for file_path in self.executions_dir.glob(pattern):
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    execution_dict = json.loads(content)
                    execution_dict = self._deserialize_datetimes(execution_dict)
                    executions.append(TaskExecution(**execution_dict))
            except Exception as e:
                print(f"Ошибка загрузки выполнения: {e}")
        
        return sorted(executions, key=lambda x: x.timestamp, reverse=True)
    
    async def find_similar_tasks(self, mini_prompt: str, limit: int = 5) -> List[Task]:
        """Найти похожие задачи по промпту"""
        all_tasks = await self.get_all_tasks(limit=1000)
        
        # Простой поиск по ключевым словам
        keywords = set(mini_prompt.lower().split())
        
        similar_tasks = []
        for task in all_tasks:
            task_keywords = set(task.mini_prompt.lower().split())
            common = keywords.intersection(task_keywords)
            
            if common:
                similarity_score = len(common) / max(len(keywords), len(task_keywords))
                similar_tasks.append((task, similarity_score))
        
        # Сортируем по схожести
        similar_tasks.sort(key=lambda x: x[1], reverse=True)
        
        return [task for task, _ in similar_tasks[:limit]]
    
    async def save_learning_pattern(self, pattern: LearningPattern) -> bool:
        """Сохранить паттерн обучения"""
        try:
            file_path = self.patterns_dir / f"{pattern.pattern_id}.json"
            pattern_dict = pattern.model_dump(mode='json')
            pattern_dict = self._serialize_datetimes(pattern_dict)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(pattern_dict, indent=2, ensure_ascii=False))
            
            return True
        except Exception as e:
            print(f"Ошибка сохранения паттерна: {e}")
            return False
    
    async def get_patterns_by_type(self, task_type: str) -> List[LearningPattern]:
        """Получить паттерны по типу задачи"""
        patterns = []
        
        for file_path in self.patterns_dir.glob("*.json"):
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    pattern_dict = json.loads(content)
                    pattern_dict = self._deserialize_datetimes(pattern_dict)
                    pattern = LearningPattern(**pattern_dict)
                    
                    if pattern.task_type == task_type:
                        patterns.append(pattern)
            except Exception as e:
                print(f"Ошибка загрузки паттерна: {e}")
        
        return sorted(patterns, key=lambda x: x.success_count, reverse=True)
    
    async def save_website_context(self, context: WebsiteContext) -> bool:
        """Сохранить контекст сайта"""
        try:
            # Используем домен как имя файла
            from urllib.parse import urlparse
            domain = urlparse(context.website_url).netloc.replace(".", "_")
            
            file_path = self.websites_dir / f"{domain}.json"
            context_dict = context.model_dump(mode='json')
            context_dict = self._serialize_datetimes(context_dict)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(context_dict, indent=2, ensure_ascii=False))
            
            return True
        except Exception as e:
            print(f"Ошибка сохранения контекста сайта: {e}")
            return False
    
    async def get_website_context(self, website_url: str) -> Optional[WebsiteContext]:
        """Получить контекст сайта"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(website_url).netloc.replace(".", "_")
            
            file_path = self.websites_dir / f"{domain}.json"
            
            if not file_path.exists():
                return None
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                context_dict = json.loads(content)
                context_dict = self._deserialize_datetimes(context_dict)
                return WebsiteContext(**context_dict)
        except Exception as e:
            print(f"Ошибка загрузки контекста сайта: {e}")
            return None
    
    async def update_task_status(self, task_id: str, status: str) -> bool:
        """Обновить статус задачи"""
        task = await self.load_task(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now()
            return await self.save_task(task)
        return False
    
    async def add_execution_to_task(self, task_id: str, execution: TaskExecution) -> bool:
        """Добавить выполнение к задаче"""
        logger.info(f"💾 Добавление execution к задаче {task_id}...")
        logger.info(f"📊 Execution: success={execution.success}, steps={len(execution.steps)}, duration={execution.duration_ms}ms")

        task = await self.load_task(task_id)
        if task:
            logger.info(f"✅ Задача загружена: {task.mini_prompt[:50]}...")
            task.executions.append(execution)
            task.updated_at = datetime.now()
            logger.info(f"📝 Execution добавлен к задаче, всего executions: {len(task.executions)}")

            # Обновляем статус задачи
            task.status = execution.status
            logger.info(f"📝 Статус задачи обновлен: {execution.status}")

            # Обновляем success_rate если есть системный промпт
            if task.system_prompt:
                task.system_prompt.executions_count += 1
                successful = sum(1 for e in task.executions if e.success)
                task.system_prompt.success_rate = successful / len(task.executions)
                logger.info(f"📈 Статистика промпта обновлена: success_rate={task.system_prompt.success_rate:.2%}, executions={task.system_prompt.executions_count}")

            logger.info("💾 Сохранение задачи...")
            await self.save_task(task)
            logger.info("✅ Задача сохранена")

            logger.info("💾 Сохранение execution отдельно...")
            await self.save_execution(task_id, execution)
            logger.info("✅ Execution сохранен")

            logger.info(f"🎉 Execution успешно добавлен к задаче {task_id}")
            return True
        else:
            logger.error(f"❌ Задача {task_id} не найдена!")
            return False
    
    def _serialize_datetimes(self, obj: Any) -> Any:
        """Рекурсивно преобразовать datetime в строки"""
        if isinstance(obj, dict):
            return {k: self._serialize_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetimes(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    def _deserialize_datetimes(self, obj: Any) -> Any:
        """Рекурсивно преобразовать строки в datetime"""
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                # Определяем поля которые должны быть datetime
                if k in ['timestamp', 'created_at', 'updated_at', 'last_used', 'last_analyzed']:
                    if isinstance(v, str):
                        try:
                            result[k] = datetime.fromisoformat(v)
                        except:
                            result[k] = v
                    else:
                        result[k] = v
                else:
                    result[k] = self._deserialize_datetimes(v)
            return result
        elif isinstance(obj, list):
            return [self._deserialize_datetimes(item) for item in obj]
        return obj
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику по задачам"""
        all_tasks = await self.get_all_tasks(limit=10000)
        
        total_tasks = len(all_tasks)
        completed_tasks = sum(1 for t in all_tasks if t.status == "completed")
        failed_tasks = sum(1 for t in all_tasks if t.status == "failed")
        
        total_executions = sum(len(t.executions) for t in all_tasks)
        successful_executions = sum(
            sum(1 for e in t.executions if e.success)
            for t in all_tasks
        )
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "total_executions": total_executions,
            "patterns_count": len(list(self.patterns_dir.glob("*.json"))),
            "websites_count": len(list(self.websites_dir.glob("*.json")))
        }
