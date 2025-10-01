/**
 * 事件总线 - 统一事件管理，解耦组件间通信
 */
class EventBus {
    constructor() {
        this.events = new Map();
        this.onceEvents = new Map();
        this.debugMode = false;
    }

    /**
     * 注册事件监听器
     */
    on(event, callback, context = null) {
        if (typeof callback !== 'function') {
            console.error('EventBus.on: callback必须是函数');
            return;
        }

        if (!this.events.has(event)) {
            this.events.set(event, []);
        }

        const listener = {
            callback,
            context,
            id: Date.now() + Math.random()
        };

        this.events.get(event).push(listener);

        if (this.debugMode) {
            console.log(`📡 事件监听器已注册: ${event}`);
        }

        // 返回取消注册的函数
        return () => this.off(event, callback);
    }

    /**
     * 注册一次性事件监听器
     */
    once(event, callback, context = null) {
        if (!this.onceEvents.has(event)) {
            this.onceEvents.set(event, []);
        }

        const listener = {
            callback,
            context,
            id: Date.now() + Math.random()
        };

        this.onceEvents.get(event).push(listener);

        if (this.debugMode) {
            console.log(`📡 一次性事件监听器已注册: ${event}`);
        }
    }

    /**
     * 移除事件监听器
     */
    off(event, callback = null) {
        if (callback) {
            // 移除特定回调
            const listeners = this.events.get(event);
            if (listeners) {
                const index = listeners.findIndex(l => l.callback === callback);
                if (index > -1) {
                    listeners.splice(index, 1);
                    if (this.debugMode) {
                        console.log(`📡 事件监听器已移除: ${event}`);
                    }
                }
            }
        } else {
            // 移除所有监听器
            this.events.delete(event);
            this.onceEvents.delete(event);
            if (this.debugMode) {
                console.log(`📡 所有事件监听器已移除: ${event}`);
            }
        }
    }

    /**
     * 触发事件
     */
    emit(event, ...args) {
        if (this.debugMode) {
            console.log(`📡 触发事件: ${event}`, args);
        }

        let listeners = [];

        // 收集常规监听器
        if (this.events.has(event)) {
            listeners = [...this.events.get(event)];
        }

        // 收集一次性监听器
        if (this.onceEvents.has(event)) {
            const onceListeners = this.onceEvents.get(event);
            listeners = [...listeners, ...onceListeners];
            // 清除一次性监听器
            this.onceEvents.delete(event);
        }

        // 执行所有监听器
        listeners.forEach(listener => {
            try {
                if (listener.context) {
                    listener.callback.apply(listener.context, args);
                } else {
                    listener.callback(...args);
                }
            } catch (error) {
                console.error(`事件监听器执行错误 (${event}):`, error);
            }
        });

        return listeners.length > 0;
    }

    /**
     * 异步触发事件
     */
    async emitAsync(event, ...args) {
        if (this.debugMode) {
            console.log(`📡 异步触发事件: ${event}`, args);
        }

        const listeners = [];

        // 收集监听器
        if (this.events.has(event)) {
            listeners.push(...this.events.get(event));
        }

        if (this.onceEvents.has(event)) {
            const onceListeners = this.onceEvents.get(event);
            listeners.push(...onceListeners);
            this.onceEvents.delete(event);
        }

        // 异步执行所有监听器
        const promises = listeners.map(async listener => {
            try {
                if (listener.context) {
                    return await listener.callback.apply(listener.context, args);
                } else {
                    return await listener.callback(...args);
                }
            } catch (error) {
                console.error(`异步事件监听器执行错误 (${event}):`, error);
                return null;
            }
        });

        return await Promise.all(promises);
    }

    /**
     * 检查是否有监听器
     */
    hasListeners(event) {
        return (this.events.has(event) && this.events.get(event).length > 0) ||
               (this.onceEvents.has(event) && this.onceEvents.get(event).length > 0);
    }

    /**
     * 获取事件的监听器数量
     */
    getListenerCount(event) {
        let count = 0;
        if (this.events.has(event)) {
            count += this.events.get(event).length;
        }
        if (this.onceEvents.has(event)) {
            count += this.onceEvents.get(event).length;
        }
        return count;
    }

    /**
     * 获取所有事件名称
     */
    getEventNames() {
        const allEvents = new Set();
        this.events.forEach((_, event) => allEvents.add(event));
        this.onceEvents.forEach((_, event) => allEvents.add(event));
        return Array.from(allEvents);
    }

    /**
     * 启用/禁用调试模式
     */
    setDebugMode(enabled) {
        this.debugMode = enabled;
        console.log(`📡 EventBus调试模式: ${enabled ? '开启' : '关闭'}`);
    }

    /**
     * 清除所有监听器
     */
    clear() {
        const eventCount = this.events.size + this.onceEvents.size;
        this.events.clear();
        this.onceEvents.clear();

        if (this.debugMode) {
            console.log(`📡 已清除所有事件监听器 (${eventCount}个)`);
        }
    }

    /**
     * 获取调试信息
     */
    getDebugInfo() {
        const info = {
            totalEvents: this.events.size + this.onceEvents.size,
            regularEvents: {},
            onceEvents: {},
            totalListeners: 0
        };

        this.events.forEach((listeners, event) => {
            info.regularEvents[event] = listeners.length;
            info.totalListeners += listeners.length;
        });

        this.onceEvents.forEach((listeners, event) => {
            info.onceEvents[event] = listeners.length;
            info.totalListeners += listeners.length;
        });

        return info;
    }
}

// 创建并导出单例
if (!window.EventBus) {
    const eventBusInstance = new EventBus();
    window.EventBus = eventBusInstance;

    // 确保方法绑定正确
    console.log('EventBus实例创建完成，方法检查:', {
        hasOn: typeof eventBusInstance.on === 'function',
        hasEmit: typeof eventBusInstance.emit === 'function',
        hasOff: typeof eventBusInstance.off === 'function'
    });
}

// 预定义应用事件常量
window.AppEvents = {
    // 搜索相关事件
    SEARCH_START: 'search:start',
    SEARCH_COMPLETE: 'search:complete',
    SEARCH_ERROR: 'search:error',
    SEARCH_RESET: 'search:reset',

    // WebSocket事件
    WS_CONNECTED: 'websocket:connected',
    WS_DISCONNECTED: 'websocket:disconnected',
    WS_ERROR: 'websocket:error',
    WS_MESSAGE: 'websocket:message',

    // 阶段事件
    STAGE_START: 'stage:start',
    STAGE_COMPLETE: 'stage:complete',
    STAGE_ERROR: 'stage:error',

    // 模块事件
    MODULE_START: 'module:start',
    MODULE_COMPLETE: 'module:complete',
    MODULE_ERROR: 'module:error',

    // UI事件
    UI_MODE_CHANGE: 'ui:mode_change',
    UI_LOADING_UPDATE: 'ui:loading_update',
    UI_ERROR_SHOW: 'ui:error_show',
    UI_ERROR_HIDE: 'ui:error_hide',

    // 性能事件
    PERF_TIMER_START: 'performance:timer_start',
    PERF_TIMER_UPDATE: 'performance:timer_update',
    PERF_TIMER_COMPLETE: 'performance:timer_complete'
};