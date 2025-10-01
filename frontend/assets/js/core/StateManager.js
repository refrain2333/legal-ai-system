/**
 * 状态管理器 - 统一管理应用状态，减少状态散乱问题
 */
class StateManager {
    constructor() {
        this.state = {
            // 搜索状态
            search: {
                inProgress: false,
                completed: false,
                query: '',
                startTime: null,
                results: null,
                currentTrace: null
            },

            // WebSocket状态
            websocket: {
                connection: null,
                connected: false,
                status: 'disconnected',
                reconnectAttempts: 0
            },

            // 服务器配置
            server: {
                host: '127.0.0.1',
                port: 5006,
                ready: false
            },

            // 阶段状态
            stages: {
                current: 0,
                completed: [],
                data: {}
            },

            // 第4阶段模块状态
            stage4Modules: {},

            // 性能监控
            performance: {
                startTime: null,
                metrics: {},
                timerInterval: null
            },

            // UI状态
            ui: {
                viewMode: 'debug',
                loadingProgress: 0,
                currentLoadingStep: 0
            },

            // 分页状态
            pagination: {
                casesOffset: 0,
                hasMoreCases: false,
                isLoadingMore: false
            }
        };

        this.listeners = new Map();
        this.initialized = false;
    }

    /**
     * 初始化状态管理器
     */
    initialize() {
        if (this.initialized) return;

        // 设置默认值
        this.resetToDefaults();
        this.initialized = true;

        console.log('✅ StateManager初始化完成');
    }

    /**
     * 重置到默认状态
     */
    resetToDefaults() {
        this.state.search.inProgress = false;
        this.state.search.completed = false;
        this.state.search.query = '';
        this.state.search.startTime = null;
        this.state.search.results = null;
        this.state.search.currentTrace = null;

        this.state.websocket.connected = false;
        this.state.websocket.status = 'disconnected';
        this.state.websocket.reconnectAttempts = 0;

        this.state.stages.current = 0;
        this.state.stages.completed = [];
        this.state.stages.data = {};

        this.state.stage4Modules = {};

        this.state.performance.startTime = null;
        this.state.performance.metrics = {};

        this.state.ui.viewMode = 'debug';
        this.state.ui.loadingProgress = 0;
        this.state.ui.currentLoadingStep = 0;

        this.state.pagination.casesOffset = 0;
        this.state.pagination.hasMoreCases = false;
        this.state.pagination.isLoadingMore = false;
    }

    /**
     * 获取状态值
     */
    get(path) {
        const keys = path.split('.');
        let current = this.state;

        for (const key of keys) {
            if (current && typeof current === 'object' && key in current) {
                current = current[key];
            } else {
                return undefined;
            }
        }

        return current;
    }

    /**
     * 设置状态值
     */
    set(path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        let current = this.state;

        // 导航到目标对象
        for (const key of keys) {
            if (!(key in current)) {
                current[key] = {};
            }
            current = current[key];
        }

        // 设置值
        const oldValue = current[lastKey];
        current[lastKey] = value;

        // 触发监听器
        this.emit(path, value, oldValue);

        return value;
    }

    /**
     * 更新对象状态（浅合并）
     */
    update(path, updates) {
        const current = this.get(path);
        if (current && typeof current === 'object') {
            const newValue = { ...current, ...updates };
            this.set(path, newValue);
            return newValue;
        }
        return this.set(path, updates);
    }

    /**
     * 监听状态变化
     */
    on(path, callback) {
        if (!this.listeners.has(path)) {
            this.listeners.set(path, []);
        }
        this.listeners.get(path).push(callback);
    }

    /**
     * 移除状态监听
     */
    off(path, callback) {
        const pathListeners = this.listeners.get(path);
        if (pathListeners) {
            const index = pathListeners.indexOf(callback);
            if (index > -1) {
                pathListeners.splice(index, 1);
            }
        }
    }

    /**
     * 触发状态变化事件
     */
    emit(path, newValue, oldValue) {
        const pathListeners = this.listeners.get(path);
        if (pathListeners) {
            pathListeners.forEach(callback => {
                try {
                    callback(newValue, oldValue, path);
                } catch (error) {
                    console.error('状态监听器执行错误:', error);
                }
            });
        }
    }

    /**
     * 搜索状态管理方法
     */
    startSearch(query) {
        this.update('search', {
            inProgress: true,
            completed: false,
            query: query,
            startTime: Date.now(),
            results: null
        });
    }

    completeSearch(results = null) {
        this.update('search', {
            inProgress: false,
            completed: true,
            results: results
        });
    }

    resetSearch() {
        this.update('search', {
            inProgress: false,
            completed: false,
            query: '',
            startTime: null,
            results: null,
            currentTrace: null
        });
    }

    /**
     * WebSocket状态管理
     */
    setWebSocketStatus(status, connection = null) {
        this.update('websocket', {
            status: status,
            connected: status === 'connected',
            connection: connection
        });
    }

    /**
     * 阶段状态管理
     */
    completeStage(stageNumber, data = null) {
        const completed = [...this.get('stages.completed')];
        if (!completed.includes(stageNumber)) {
            completed.push(stageNumber);
        }

        this.update('stages', {
            current: Math.max(this.get('stages.current'), stageNumber),
            completed: completed
        });

        if (data) {
            this.set(`stages.data.stage${stageNumber}`, data);
        }
    }

    /**
     * 第4阶段模块管理
     */
    updateStage4Module(moduleName, moduleData) {
        const currentModules = { ...this.get('stage4Modules') };
        currentModules[moduleName] = moduleData;
        this.set('stage4Modules', currentModules);
    }

    getStage4Module(moduleName) {
        return this.get(`stage4Modules.${moduleName}`);
    }

    /**
     * 性能监控管理
     */
    startPerformanceTimer() {
        this.set('performance.startTime', performance.now());
    }

    updatePerformanceMetrics(metrics) {
        this.update('performance.metrics', metrics);
    }

    /**
     * UI状态管理
     */
    setViewMode(mode) {
        this.set('ui.viewMode', mode);
    }

    updateLoadingProgress(progress, step = null) {
        this.set('ui.loadingProgress', progress);
        if (step !== null) {
            this.set('ui.currentLoadingStep', step);
        }
    }

    /**
     * 分页状态管理
     */
    updatePagination(updates) {
        this.update('pagination', updates);
    }

    /**
     * 获取当前完整状态（调试用）
     */
    getFullState() {
        return JSON.parse(JSON.stringify(this.state));
    }

    /**
     * 清理状态管理器
     */
    destroy() {
        // 清理定时器
        if (this.state.performance.timerInterval) {
            clearInterval(this.state.performance.timerInterval);
        }

        // 清理监听器
        this.listeners.clear();

        // 重置状态
        this.resetToDefaults();
        this.initialized = false;
    }
}

// 创建并导出单例
if (!window.StateManager) {
    const stateManagerInstance = new StateManager();
    window.StateManager = stateManagerInstance;

    // 确保方法绑定正确
    console.log('StateManager实例创建完成，方法检查:', {
        hasSet: typeof stateManagerInstance.set === 'function',
        hasGet: typeof stateManagerInstance.get === 'function',
        hasInitialize: typeof stateManagerInstance.initialize === 'function'
    });
}