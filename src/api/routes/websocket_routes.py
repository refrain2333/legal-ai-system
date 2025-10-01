#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket路由模块
包含WebSocket实时通信相关的接口
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# 创建WebSocket路由器
router = APIRouter()

# 导入统一的WebSocket管理器
from ..websocket_manager import get_websocket_manager

# 获取全局WebSocket管理器实例
websocket_manager = get_websocket_manager()


@router.websocket("/debug/realtime")
async def debug_websocket(websocket: WebSocket):
    """WebSocket端点 - 用于实时调试数据推送"""
    logger.info("新的WebSocket连接请求")

    await websocket_manager.connect(websocket)

    try:
        # 发送欢迎消息
        welcome_message = {
            "type": "connected",
            "message": "调试WebSocket连接已建立",
            "timestamp": "2024-01-01T00:00:00Z",
            "connection_id": len(websocket_manager.active_connections)
        }
        await websocket.send_json(welcome_message)
        logger.info(f"已发送欢迎消息: {welcome_message}")

        # 保持连接活跃
        while True:
            try:
                # 等待来自客户端的消息
                data = await websocket.receive_json()
                logger.info(f"收到WebSocket消息: {data}")

                if data.get("type") == "ping":
                    pong_message = {
                        "type": "pong",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                    await websocket.send_json(pong_message)
                    logger.info("回复pong消息")

                elif data.get("type") == "subscribe":
                    subscribe_message = {
                        "type": "subscribed",
                        "subscription": data.get("events", ["all"]),
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                    await websocket.send_json(subscribe_message)
                    logger.info(f"确认订阅: {subscribe_message}")

            except WebSocketDisconnect:
                logger.info("客户端主动断开WebSocket连接")
                break
            except Exception as e:
                logger.error(f"WebSocket处理消息错误: {e}")
                break

    except WebSocketDisconnect:
        logger.info("WebSocket连接断开")
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    finally:
        await websocket_manager.disconnect(websocket)


# WebSocket管理器已在websocket_manager.py中统一定义