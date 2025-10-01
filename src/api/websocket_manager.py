#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享的WebSocket管理器
统一管理所有WebSocket连接，避免重复实例
"""

import logging
from fastapi import WebSocket
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class WebSocketManager:
    """统一的WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """建立WebSocket连接"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")

    async def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"WebSocket断开连接错误: {e}")

    async def broadcast(self, message: Dict[str, Any]):
        """广播消息到所有活跃连接"""
        if not self.active_connections:
            logger.debug("没有活跃的WebSocket连接，跳过广播")
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                logger.debug(f"WebSocket消息发送成功: {message.get('type', 'unknown')}")
            except Exception as e:
                logger.warning(f"WebSocket发送消息失败: {e}")
                disconnected.append(connection)

        # 清理失效连接
        for conn in disconnected:
            await self.disconnect(conn)

    def get_stats(self) -> Dict[str, Any]:
        """获取WebSocket统计信息"""
        return {
            "active_connections": len(self.active_connections),
            "connection_details": [
                {
                    "id": id(conn),
                    "state": conn.client_state.name if hasattr(conn, 'client_state') else "unknown"
                }
                for conn in self.active_connections
            ]
        }


# 全局单例WebSocket管理器
_websocket_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """获取全局WebSocket管理器实例"""
    return _websocket_manager