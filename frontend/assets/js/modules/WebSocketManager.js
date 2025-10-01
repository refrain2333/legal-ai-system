/**
 * WebSocket管理器 - 统一WebSocket连接和消息处理
 */
class WebSocketManager {
    constructor() {
        this.connection = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 2000;
        this.connectionTimeout = 2000;
        this.messageHandlers = new Map();
        this.isConnecting = false;
        this.shouldReconnect = true;

        this.setupDefaultHandlers();
    }

    /**
     * 初始化WebSocket连接
     */
    async initialize() {
        try {
            const wsUrl = window.apiConfig.getWsUrl('/api/debug/realtime');
            console.log('🌐 尝试连接WebSocket:', wsUrl);

            await this.connect(wsUrl);
        } catch (error) {
            console.error('❌ WebSocket初始化失败:', error);
            if (window.StateManager && typeof window.StateManager.setWebSocketStatus === 'function') {
                window.StateManager.setWebSocketStatus('error');
            }
        }
    }

    /**
     * 建立WebSocket连接
     */
    connect(url) {
        return new Promise((resolve, reject) => {
            if (this.isConnecting) {
                console.log('⚠️ WebSocket正在连接中，跳过重复连接');
                return;
            }

            this.isConnecting = true;
            if (window.StateManager && typeof window.StateManager.setWebSocketStatus === 'function') {
                window.StateManager.setWebSocketStatus('connecting');
            }

            try {
                this.connection = new WebSocket(url);

                // 设置连接超时
                const connectionTimeout = setTimeout(() => {
                    if (this.connection.readyState === WebSocket.CONNECTING) {
                        console.log('⏰ WebSocket连接超时');
                        this.connection.close();
                        if (window.StateManager && typeof window.StateManager.setWebSocketStatus === 'function') {
                            window.StateManager.setWebSocketStatus('timeout');
                        }
                        reject(new Error('连接超时'));
                    }
                }, this.connectionTimeout);

                this.connection.onopen = () => {
                    clearTimeout(connectionTimeout);
                    this.isConnecting = false;
                    this.reconnectAttempts = 0;

                    console.log('✅ WebSocket连接已建立');
                    if (window.StateManager && typeof window.StateManager.setWebSocketStatus === 'function') {
                        window.StateManager.setWebSocketStatus('connected', this.connection);
                    }
                    window.EventBus.emit(window.AppEvents.WS_CONNECTED);

                    resolve();
                };

                this.connection.onmessage = (event) => {
                    this.handleMessage(event);
                };

                this.connection.onclose = (event) => {
                    clearTimeout(connectionTimeout);
                    this.isConnecting = false;

                    console.log('🔌 WebSocket连接已断开', event.code, event.reason);
                    if (window.StateManager && typeof window.StateManager.setWebSocketStatus === 'function') {
                        window.StateManager.setWebSocketStatus('disconnected');
                    }
                    window.EventBus.emit(window.AppEvents.WS_DISCONNECTED, event);

                    // 自动重连
                    if (this.shouldReconnect && event.code !== 1000) {
                        this.scheduleReconnect(url);
                    }
                };

                this.connection.onerror = (error) => {
                    clearTimeout(connectionTimeout);
                    this.isConnecting = false;

                    console.error('❌ WebSocket连接错误:', error);
                    if (window.StateManager && typeof window.StateManager.setWebSocketStatus === 'function') {
                        window.StateManager.setWebSocketStatus('error');
                    }
                    window.EventBus.emit(window.AppEvents.WS_ERROR, error);

                    reject(error);
                };

            } catch (error) {
                this.isConnecting = false;
                console.error('❌ WebSocket创建失败:', error);
                reject(error);
            }
        });
    }

    /**
     * 处理WebSocket消息
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('📨 收到WebSocket消息:', data.type, data);

            window.EventBus.emit(window.AppEvents.WS_MESSAGE, data);

            // 调用特定消息处理器
            if (data.type && this.messageHandlers.has(data.type)) {
                const handler = this.messageHandlers.get(data.type);
                handler(data);
            }

        } catch (error) {
            console.error('❌ WebSocket消息解析失败:', error, event.data);
        }
    }

    /**
     * 注册消息处理器
     */
    onMessage(messageType, handler) {
        this.messageHandlers.set(messageType, handler);
        console.log(`📋 已注册消息处理器: ${messageType}`);
    }

    /**
     * 移除消息处理器
     */
    offMessage(messageType) {
        this.messageHandlers.delete(messageType);
    }

    /**
     * 发送消息
     */
    send(data) {
        if (this.connection && this.connection.readyState === WebSocket.OPEN) {
            try {
                const message = typeof data === 'string' ? data : JSON.stringify(data);
                this.connection.send(message);
                console.log('📤 发送WebSocket消息:', data);
                return true;
            } catch (error) {
                console.error('❌ WebSocket发送消息失败:', error);
                return false;
            }
        } else {
            console.warn('⚠️ WebSocket未连接，无法发送消息');
            return false;
        }
    }

    /**
     * 安排重连
     */
    scheduleReconnect(url) {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('❌ WebSocket重连次数已达上限，停止重连');
            if (window.StateManager && typeof window.StateManager.setWebSocketStatus === 'function') {
                window.StateManager.setWebSocketStatus('failed');
            }
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1);

        console.log(`🔄 ${delay}ms后尝试第${this.reconnectAttempts}次重连...`);

        setTimeout(() => {
            if (this.shouldReconnect) {
                this.connect(url).catch(error => {
                    console.error('❌ WebSocket重连失败:', error);
                });
            }
        }, delay);
    }

    /**
     * 手动重连
     */
    async reconnect() {
        if (this.connection) {
            this.connection.close();
        }

        this.reconnectAttempts = 0;
        const wsUrl = window.apiConfig.getWsUrl('/api/debug/realtime');
        await this.connect(wsUrl);
    }

    /**
     * 关闭连接
     */
    disconnect() {
        this.shouldReconnect = false;

        if (this.connection) {
            console.log('🔌 主动断开WebSocket连接');
            this.connection.close(1000, '用户主动断开');
            this.connection = null;
        }

        if (window.StateManager && typeof window.StateManager.setWebSocketStatus === 'function') {
            window.StateManager.setWebSocketStatus('disconnected');
        }
    }

    /**
     * 获取连接状态
     */
    getConnectionState() {
        if (!this.connection) return 'disconnected';

        switch (this.connection.readyState) {
            case WebSocket.CONNECTING: return 'connecting';
            case WebSocket.OPEN: return 'connected';
            case WebSocket.CLOSING: return 'closing';
            case WebSocket.CLOSED: return 'disconnected';
            default: return 'unknown';
        }
    }

    /**
     * 检查是否已连接
     */
    isConnected() {
        return this.connection && this.connection.readyState === WebSocket.OPEN;
    }

    /**
     * 设置默认消息处理器
     */
    setupDefaultHandlers() {
        // 阶段完成消息
        this.onMessage('stage_completed', (data) => {
            window.EventBus.emit(window.AppEvents.STAGE_COMPLETE, data);
        });

        // 模块完成消息
        this.onMessage('module_completed', (data) => {
            window.EventBus.emit(window.AppEvents.MODULE_COMPLETE, data);
        });

        // 搜索完成消息
        this.onMessage('search_completed', (data) => {
            window.EventBus.emit(window.AppEvents.SEARCH_COMPLETE, data);
        });
    }

    /**
     * 获取连接信息
     */
    getConnectionInfo() {
        return {
            connected: this.isConnected(),
            state: this.getConnectionState(),
            reconnectAttempts: this.reconnectAttempts,
            shouldReconnect: this.shouldReconnect,
            url: this.connection ? this.connection.url : null
        };
    }

    /**
     * 清理资源
     */
    destroy() {
        this.disconnect();
        this.messageHandlers.clear();
        console.log('🧹 WebSocketManager已清理');
    }
}

// 创建并导出单例
const webSocketManagerInstance = new WebSocketManager();
window.WebSocketManager = webSocketManagerInstance;

// 验证绑定是否成功
const wsVerifyMethods = ['initialize', 'connect', 'disconnect', 'isConnected', 'send'];
const wsMissingMethods = wsVerifyMethods.filter(method => typeof window.WebSocketManager[method] !== 'function');

if (wsMissingMethods.length > 0) {
    console.error('❌ WebSocketManager方法绑定失败:', wsMissingMethods);
} else {
    console.log('✅ WebSocketManager单例创建并绑定完成');
}