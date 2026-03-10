"""
WebSocket для реал-тайм обновлений
"""
import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json


class ConnectionManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        # Активные соединения: task_id -> set of WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Глобальные соединения (получают все события)
        self.global_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, task_id: str = None):
        """Подключить WebSocket"""
        await websocket.accept()
        
        if task_id:
            if task_id not in self.active_connections:
                self.active_connections[task_id] = set()
            self.active_connections[task_id].add(websocket)
        else:
            # Глобальное подключение
            self.global_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket, task_id: str = None):
        """Отключить WebSocket"""
        if task_id and task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        else:
            self.global_connections.discard(websocket)
    
    async def send_message(self, message: dict, websocket: WebSocket):
        """Отправить сообщение конкретному клиенту"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
    
    async def broadcast_to_task(self, task_id: str, message: dict):
        """Отправить сообщение всем подписчикам задачи"""
        connections = self.active_connections.get(task_id, set())
        
        disconnected = set()
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Удаляем отключенные соединения
        for conn in disconnected:
            self.disconnect(conn, task_id)
    
    async def broadcast_global(self, message: dict):
        """Отправить сообщение всем глобальным подписчикам"""
        disconnected = set()
        
        for connection in self.global_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Удаляем отключенные соединения
        for conn in disconnected:
            self.disconnect(conn)
    
    async def emit_task_event(
        self,
        task_id: str,
        event: str,
        data: dict
    ):
        """Отправить событие задачи"""
        message = {
            "type": "task_update",
            "task_id": task_id,
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Отправляем подписчикам задачи
        await self.broadcast_to_task(task_id, message)
        
        # И глобальным подписчикам
        await self.broadcast_global(message)
    
    async def emit_step_complete(
        self,
        task_id: str,
        step_number: int,
        step_data: dict
    ):
        """Отправить событие завершения шага"""
        message = {
            "type": "step_complete",
            "task_id": task_id,
            "step_number": step_number,
            "data": step_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_task(task_id, message)
        await self.broadcast_global(message)
    
    async def emit_error(
        self,
        task_id: str,
        error: str
    ):
        """Отправить событие ошибки"""
        message = {
            "type": "error",
            "task_id": task_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_task(task_id, message)
        await self.broadcast_global(message)


# Глобальный менеджер соединений
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, task_id: str = None):
    """WebSocket endpoint"""
    await manager.connect(websocket, task_id)
    
    try:
        # Отправляем приветственное сообщение
        await websocket.send_json({
            "type": "connected",
            "task_id": task_id,
            "message": "Подключено к WebSocket",
            "timestamp": datetime.now().isoformat()
        })
        
        # Ждем сообщения от клиента (для поддержания соединения)
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0  # Пинг каждые 60 секунд
                )
                
                # Обрабатываем пинг
                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
            except asyncio.TimeoutError:
                # Отправляем пинг если клиент молчит
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        print(f"WebSocket ошибка: {e}")
        manager.disconnect(websocket, task_id)


def setup_websocket_callbacks(agent_manager):
    """Настройка колбэков для WebSocket событий"""
    
    async def on_task_update(task_id: str, event: str, task):
        """Колбэк для обновления задачи"""
        await manager.emit_task_event(
            task_id=task_id,
            event=event,
            data={
                "status": task.status,
                "mini_prompt": task.mini_prompt
            }
        )
    
    async def on_step_complete(task_id: str, step_number: int, step_data: dict):
        """Колбэк для завершения шага"""
        await manager.emit_step_complete(
            task_id=task_id,
            step_number=step_number,
            step_data=step_data
        )
    
    # Устанавливаем колбэки
    agent_manager.set_on_task_update(on_task_update)
    agent_manager.set_on_step_complete(on_step_complete)
