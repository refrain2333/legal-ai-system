/**
 * 通用API配置模块
 * 自动检测访问方式（本地文件 vs 服务器），智能配置API地址
 */
class ApiConfig {
    constructor() {
        this.config = {
            defaultHost: '127.0.0.1',
            defaultPort: 5006,
            fallbackPorts: [5006, 5007, 8000, 3000],
            timeout: 3000
        };

        this.baseUrl = '';
        this.wsUrl = '';
        this.isFileProtocol = false;
        this.isInitialized = false;

        this.init();
    }

    init() {
        this.isFileProtocol = window.location.protocol === 'file:';

        if (this.isFileProtocol) {
            // 本地文件访问：使用绝对路径
            this.baseUrl = `http://${this.config.defaultHost}:${this.config.defaultPort}`;
            this.wsUrl = `ws://${this.config.defaultHost}:${this.config.defaultPort}`;
            console.log('[ApiConfig] 检测到本地文件访问，使用绝对路径:', this.baseUrl);
        } else {
            // 服务器访问：使用相对路径
            this.baseUrl = '';
            this.wsUrl = `ws://${window.location.host}`;
            console.log('[ApiConfig] 检测到服务器访问，使用相对路径');
        }

        this.isInitialized = true;
    }

    /**
     * 自动检测可用端口（仅在本地文件访问时使用）
     */
    async autoDetectPort() {
        if (!this.isFileProtocol) {
            return true; // 服务器访问不需要检测端口
        }

        console.log('[ApiConfig] 开始自动检测服务器端口...');

        for (const port of this.config.fallbackPorts) {
            try {
                const testUrl = `http://${this.config.defaultHost}:${port}/api/health`;
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

                const response = await fetch(testUrl, {
                    method: 'GET',
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (response.ok) {
                    this.config.defaultPort = port;
                    this.baseUrl = `http://${this.config.defaultHost}:${port}`;
                    this.wsUrl = `ws://${this.config.defaultHost}:${port}`;
                    console.log(`[ApiConfig] 发现服务器运行在端口: ${port}`);
                    return true;
                }
            } catch (error) {
                console.log(`[ApiConfig] 端口 ${port} 不可用:`, error.message);
                continue;
            }
        }

        console.warn('[ApiConfig] 未能检测到可用的服务器端口，使用默认配置');
        return false;
    }

    /**
     * 获取完整的API URL
     * @param {string} endpoint - API端点（如：'/api/search'）
     * @returns {string} 完整的URL
     */
    getApiUrl(endpoint) {
        if (!this.isInitialized) {
            console.warn('[ApiConfig] 配置未初始化，请先调用 init()');
            return endpoint;
        }

        // 确保端点以 / 开头
        const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

        if (this.isFileProtocol) {
            return `${this.baseUrl}${cleanEndpoint}`;
        } else {
            return cleanEndpoint; // 相对路径
        }
    }

    /**
     * 获取WebSocket URL
     * @param {string} endpoint - WebSocket端点（如：'/api/debug/realtime'）
     * @returns {string} 完整的WebSocket URL
     */
    getWsUrl(endpoint) {
        if (!this.isInitialized) {
            console.warn('[ApiConfig] 配置未初始化，请先调用 init()');
            return endpoint;
        }

        const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
        return `${this.wsUrl}${cleanEndpoint}`;
    }

    /**
     * 创建配置好的fetch函数
     * @param {string} endpoint - API端点
     * @param {object} options - fetch选项
     * @returns {Promise} fetch Promise
     */
    fetch(endpoint, options = {}) {
        const url = this.getApiUrl(endpoint);
        console.log(`[ApiConfig] Fetch: ${url}`);
        return fetch(url, options);
    }

    /**
     * 创建WebSocket连接
     * @param {string} endpoint - WebSocket端点
     * @param {array} protocols - WebSocket协议
     * @returns {WebSocket} WebSocket实例
     */
    createWebSocket(endpoint, protocols = []) {
        const url = this.getWsUrl(endpoint);
        console.log(`[ApiConfig] WebSocket: ${url}`);
        return new WebSocket(url, protocols);
    }

    /**
     * 检查服务器健康状态
     * @returns {Promise<boolean>} 服务器是否可用
     */
    async checkHealth() {
        try {
            const response = await this.fetch('/api/health');
            return response.ok;
        } catch (error) {
            console.error('[ApiConfig] 健康检查失败:', error);
            return false;
        }
    }

    /**
     * 获取当前配置信息
     * @returns {object} 配置信息
     */
    getConfig() {
        return {
            isFileProtocol: this.isFileProtocol,
            baseUrl: this.baseUrl,
            wsUrl: this.wsUrl,
            host: this.config.defaultHost,
            port: this.config.defaultPort,
            isInitialized: this.isInitialized
        };
    }

    /**
     * 打印调试信息
     */
    debug() {
        console.log('[ApiConfig] 当前配置:', this.getConfig());
        console.log('[ApiConfig] 示例URL:', {
            api: this.getApiUrl('/api/search'),
            websocket: this.getWsUrl('/api/debug/realtime'),
            health: this.getApiUrl('/api/health')
        });
    }
}

// 创建全局实例
window.apiConfig = new ApiConfig();

// 自动检测端口（仅在需要时）
if (window.apiConfig.isFileProtocol) {
    window.apiConfig.autoDetectPort().then(success => {
        if (success) {
            console.log('[ApiConfig] 端口检测完成，配置已就绪');
        } else {
            console.warn('[ApiConfig] 端口检测失败，使用默认配置');
        }

        // 触发自定义事件，通知其他模块配置已就绪
        window.dispatchEvent(new CustomEvent('apiConfigReady', {
            detail: window.apiConfig.getConfig()
        }));
    });
} else {
    // 服务器访问时立即触发就绪事件
    setTimeout(() => {
        window.dispatchEvent(new CustomEvent('apiConfigReady', {
            detail: window.apiConfig.getConfig()
        }));
    }, 0);
}

// 调试信息（开发环境）
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.protocol === 'file:') {
    window.apiConfig.debug();
}