/**
 * 法智导航 - 完整流程可视化主应用（重构版）
 *
 * 重构要点：
 * - 模块化架构，分离关注点
 * - 统一状态管理
 * - 事件驱动通信
 * - DOM缓存优化
 * - 性能监控集成
 */

class CompleteFlowApp {
    constructor() {
        this.isInitialized = false;
        this.loadingSteps = [
            '初始化页面组件...',
            '检测服务器配置...',
            '建立WebSocket连接...',
            '加载模块状态...',
            '页面准备完成！'
        ];
        this.currentLoadingStep = 0;
        this.loadingProgress = 0;
        this.initRetryCount = 0;
        this.maxRetries = 10;
    }

    /**
     * 应用初始化
     */
    async init() {
        if (this.isInitialized) return;

        console.log('🚀 CompleteFlowApp开始初始化');

        try {
            // 显示加载进度
            this.updateLoadingProgress(0, '页面初始化中...');

            // 等待依赖模块加载完成
            await this.waitForDependencies();

            // 阶段1: 初始化核心模块
            await this.initializeCoreModules();
            this.updateLoadingProgress(30, 'UI组件初始化完成');

            // 阶段2: 设置事件系统
            this.setupEventSystem();
            this.updateLoadingProgress(50, '事件系统配置完成');

            // 阶段3: 初始化功能模块（延迟初始化）
            setTimeout(async () => {
                this.updateLoadingProgress(70, '准备WebSocket连接...');
                await this.initializeFunctionalModules();

                // 阶段4: 完成初始化
                setTimeout(() => {
                    this.updateLoadingProgress(100, '页面准备完成！');
                    this.completeInitialization();
                }, 500);
            }, 100);

        } catch (error) {
            console.error('❌ CompleteFlowApp初始化失败:', error);
            this.handleInitializationError(error);
        }
    }

    /**
     * 等待依赖模块加载完成
     */
    async waitForDependencies() {
        console.log('⏳ 等待依赖模块加载完成...');

        const requiredModules = [
            'DOMManager', 'StateManager', 'EventBus', 'AppEvents',
            'StageRenderer', 'WebSocketManager', 'SearchController',
            'ResultRenderer', 'PerformanceMonitor'
        ];

        const checkDependencies = () => {
            const missing = requiredModules.filter(module => !window[module]);
            if (missing.length > 0) {
            if (this.initRetryCount % 5 === 0) { // 每5次检查输出一次日志
                console.log('⏳ 等待模块加载:', missing);
            }
            return false;
            }

            // 特别检查关键模块的方法
            if (window.DOMManager) {
                const domMethods = ['get', 'updateTexts', 'updateVisibility', 'getTemplate'];
                const missingDomMethods = domMethods.filter(method => typeof window.DOMManager[method] !== 'function');
                
                if (missingDomMethods.length > 0) {
                    if (this.initRetryCount % 5 === 0) {
                        console.log('⏳ 等待DOMManager方法绑定，缺少:', missingDomMethods);
                    }
                    return false;
                }
            }

            if (window.WebSocketManager) {
                const wsMethods = ['initialize', 'isConnected', 'connect'];
                const missingWsMethods = wsMethods.filter(method => typeof window.WebSocketManager[method] !== 'function');

                if (missingWsMethods.length > 0) {
                    if (this.initRetryCount % 5 === 0) {
                        console.log('⏳ 等待WebSocketManager方法绑定，缺少:', missingWsMethods);
                    }
                    return false;
                }
            }

            // 特殊检查StageRenderer
            if (window.StageRenderer) {
                const stageRendererMethods = ['renderStage1', 'renderStage2', 'renderStage3', 'renderStage4', 'renderStage5'];
                const missingStageRendererMethods = stageRendererMethods.filter(method => typeof window.StageRenderer[method] !== 'function');

                if (missingStageRendererMethods.length > 0) {
                    if (this.initRetryCount % 5 === 0) {
                        console.log('⏳ 等待StageRenderer方法绑定，缺少:', missingStageRendererMethods);
                    }
                    return false;
                }
            }

            console.log('✅ 所有依赖模块已加载');
            return true;
        };

        // 最多等待5秒
        while (this.initRetryCount < this.maxRetries && !checkDependencies()) {
            await new Promise(resolve => setTimeout(resolve, 500));
            this.initRetryCount++;
        }

        if (this.initRetryCount >= this.maxRetries) {
            throw new Error('依赖模块加载超时，缺少模块: ' +
                requiredModules.filter(module => !window[module]).join(', '));
        }
    }

    /**
     * 初始化核心模块
     */
    async initializeCoreModules() {
        console.log('🔧 初始化核心模块');

        // 确保模块存在并初始化
        if (!window.DOMManager) {
            throw new Error('DOMManager模块未加载');
        }
        if (!window.StateManager) {
            throw new Error('StateManager模块未加载');
        }

        // 初始化DOM管理器（必须最先初始化）
        window.DOMManager.initialize();

        // 初始化状态管理器
        window.StateManager.initialize();

        // 设置基本的DOM事件监听
        this.setupBasicEventListeners();

        console.log('✅ 核心模块初始化完成');
    }

    /**
     * 设置事件系统
     */
    setupEventSystem() {
        console.log('📡 设置事件系统');

        // 设置视图模式控制
        this.setupViewModeControls();

        // 设置全局事件委托
        this.setupGlobalEventDelegation();

        // 设置错误处理
        this.setupErrorHandling();

        console.log('✅ 事件系统设置完成');
    }

    /**
     * 设置全局事件委托
     */
    setupGlobalEventDelegation() {
        console.log('🔗 设置全局事件委托');

        // 检查是否已经设置过事件委托
        if (this.globalEventDelegate) {
            console.log('⚠️ 全局事件委托已存在，跳过设置');
            return;
        }

        // 创建事件委托处理函数
        this.globalEventDelegate = (event) => {
            // 检查点击的元素是否是模块详情按钮
            if (event.target.closest('.module-detail-btn-simple')) {
                const button = event.target.closest('.module-detail-btn-simple');
                const searchPath = button.getAttribute('data-module-path');

                if (searchPath && window.showModuleDetails) {
                    console.log('🔍 通过事件委托触发模块详情:', searchPath);
                    window.showModuleDetails(searchPath);
                }
            }

            // 检查点击的元素是否是答案切换按钮
            if (event.target.closest('.toggle-answer-btn')) {
                const button = event.target.closest('.toggle-answer-btn');
                const action = button.getAttribute('data-action');

                if (action === 'toggle-answer' && window.toggleAnswerFull) {
                    console.log('🔄 通过事件委托触发答案切换');
                    window.toggleAnswerFull();
                }
            }
        };

        // 添加事件监听器
        document.addEventListener('click', this.globalEventDelegate);

        console.log('✅ 全局事件委托设置完成');
    }

    /**
     * 紧急修复：为按钮添加直接的onclick事件处理（作为事件委托的备用方案）
     */
    setupEmergencyButtonHandlers() {
        console.log('🚨 设置紧急按钮处理器');

        // 为所有现有的模块详情按钮添加直接事件监听
        document.querySelectorAll('.module-detail-btn-simple').forEach(button => {
            // 移除之前的事件监听器（如果有）
            button.removeEventListener('click', this.emergencyModuleHandler);

            // 添加新的直接事件监听器
            this.emergencyModuleHandler = (event) => {
                event.stopPropagation();
                const searchPath = button.getAttribute('data-module-path');
                if (searchPath && window.showModuleDetails) {
                    console.log('🚨 通过紧急处理器触发模块详情:', searchPath);
                    window.showModuleDetails(searchPath);
                }
            };
            button.addEventListener('click', this.emergencyModuleHandler);
        });

        // 为所有现有的答案切换按钮添加直接事件监听
        document.querySelectorAll('.toggle-answer-btn').forEach(button => {
            // 移除之前的事件监听器（如果有）
            button.removeEventListener('click', this.emergencyAnswerHandler);

            // 添加新的直接事件监听器
            this.emergencyAnswerHandler = (event) => {
                event.stopPropagation();
                if (window.toggleAnswerFull) {
                    console.log('🚨 通过紧急处理器触发答案切换');
                    window.toggleAnswerFull();
                }
            };
            button.addEventListener('click', this.emergencyAnswerHandler);
        });

        console.log('✅ 紧急按钮处理器设置完成');
    }

    /**
     * 初始化功能模块
     */
    async initializeFunctionalModules() {
        console.log('⚙️ 初始化功能模块');

        try {
            // 初始化WebSocket管理器
            if (window.WebSocketManager) {
                await window.WebSocketManager.initialize();
            }

            // 初始化搜索控制器
            if (window.SearchController) {
                window.SearchController.initialize();
            }

            // 初始化结果渲染器
            if (window.ResultRenderer) {
                window.ResultRenderer.initialize();
            }

            // 初始化性能监控器
            if (window.PerformanceMonitor) {
                window.PerformanceMonitor.initialize();
            }

            // 初始化其他组件
            if (window.StageRenderer) {
                window.StageRenderer.init();
            }

            console.log('✅ 功能模块初始化完成');

        } catch (error) {
            console.error('❌ 功能模块初始化失败:', error);
            throw error;
        }
    }

    /**
     * 设置基本事件监听
     */
    setupBasicEventListeners() {
        // 全局键盘事件
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.handleEscapeKey();
            }
        });

        // 确保按钮状态正确
        this.ensureButtonStates();
    }

    /**
     * 设置视图模式控制
     */
    setupViewModeControls() {
        const radioButtons = document.querySelectorAll('input[name="viewMode"]');
        radioButtons.forEach(radio => {
            radio.addEventListener('change', () => {
                if (radio.checked && window.StateManager && typeof window.StateManager.set === 'function') {
                    window.StateManager.set('ui.viewMode', radio.value);
                    this.updateViewMode(radio.value);
                    if (window.EventBus && window.AppEvents) {
                        window.EventBus.emit(window.AppEvents.UI_MODE_CHANGE, radio.value);
                    }
                }
            });
        });

        // 设置默认视图模式
        const defaultMode = 'debug';
        if (window.StateManager && typeof window.StateManager.set === 'function') {
            window.StateManager.set('ui.viewMode', defaultMode);
        }
        this.updateViewMode(defaultMode);
    }

    /**
     * 更新视图模式
     */
    updateViewMode(mode) {
        console.log('👀 更新视图模式:', mode);

        // 控制详情面板的显示
        for (let i = 1; i <= 5; i++) {
            const detailsId = i === 4 ? `stage${i}-details-inline` : `stage${i}-details`;
            const details = document.getElementById(detailsId);
            if (details) {
                details.style.display = mode === 'debug' ? 'block' : 'none';
            }
        }

        // 控制性能监控面板
        const performancePanel = window.DOMManager?.get('performancePanel');
        if (performancePanel) {
            performancePanel.style.display = mode === 'debug' ? 'block' : 'none';
        }
    }


    /**
     * 设置错误处理
     */
    setupErrorHandling() {
        // 监听错误显示事件
        window.EventBus.on(window.AppEvents.UI_ERROR_SHOW, (data) => {
            this.showError(data.title, data.message, data.type);
        });

        // 监听错误隐藏事件
        window.EventBus.on(window.AppEvents.UI_ERROR_HIDE, () => {
            this.hideError();
        });

        // 全局错误处理
        window.addEventListener('error', (event) => {
            console.error('❌ 全局错误:', event.error);
            this.showError('系统错误', event.error.message);
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('❌ 未处理的Promise拒绝:', event.reason);
            this.showError('系统错误', event.reason.message || event.reason);
        });
    }

    /**
     * 处理ESC键
     */
    handleEscapeKey() {
        // 关闭模块详情面板
        const modulePanel = window.DOMManager.get('module-detail-panel');
        if (modulePanel && modulePanel.style.display !== 'none') {
            window.hideModuleDetails?.();
            return;
        }

        // 关闭融合详情面板
        const fusionPanel = document.getElementById('fusion-detail-panel');
        if (fusionPanel && fusionPanel.style.display !== 'none') {
            window.hideFusionDetails?.();
            return;
        }

        // 其他ESC操作
        console.log('⌨️ ESC键按下');
    }

    /**
     * 确保按钮状态正确
     */
    ensureButtonStates() {
        // 定期检查按钮状态
        setInterval(() => {
            const searchInProgress = window.StateManager?.get('search.inProgress');
            const searchBtn = window.DOMManager?.get('searchBtn');

            if (searchBtn && !searchInProgress && searchBtn.disabled) {
                console.log('🔧 强制恢复按钮状态');
                searchBtn.disabled = false;
            }
        }, 2000);
    }

    /**
     * 完成初始化
     */
    completeInitialization() {
        this.isInitialized = true;
        this.hideLoadingIndicator();

        console.log('🎉 CompleteFlowApp初始化完成');

        // 触发应用就绪事件
        window.EventBus.emit('app:ready');

        // 自动进行连接测试
        this.performInitialConnectionTest();
    }

    /**
     * 执行初始连接测试
     */
    async performInitialConnectionTest() {
        try {
            console.log('🧪 执行初始连接测试');

            // 这里可以添加初始的健康检查逻辑
            const wsConnected = window.WebSocketManager.isConnected();
            console.log('WebSocket连接状态:', wsConnected ? '已连接' : '未连接');

        } catch (error) {
            console.error('❌ 初始连接测试失败:', error);
        }
    }

    /**
     * 处理初始化错误
     */
    handleInitializationError(error) {
        console.error('❌ 应用初始化失败:', error);

        // 显示错误信息
        this.showError('初始化失败', error.message || '应用启动时发生未知错误');

        // 尝试基本功能降级
        this.fallbackInitialization();
    }

    /**
     * 降级初始化
     */
    fallbackInitialization() {
        console.log('🛠️ 执行降级初始化');

        try {
            // 至少保证基本的DOM缓存工作
            if (window.DOMManager && typeof window.DOMManager.initialize === 'function' && !window.DOMManager.initialized) {
                window.DOMManager.initialize();
            }

            // 基本的搜索功能
            let searchBtn, searchQuery;

            if (window.DOMManager && typeof window.DOMManager.get === 'function') {
                searchBtn = window.DOMManager.get('searchBtn');
                searchQuery = window.DOMManager.get('searchQuery');
            } else {
                searchBtn = document.getElementById('searchBtn');
                searchQuery = document.getElementById('searchQuery');
            }

            if (searchBtn && searchQuery) {
                searchBtn.addEventListener('click', () => {
                    const query = searchQuery.value.trim();
                    if (query) {
                        alert('系统在降级模式下运行，请刷新页面重试完整功能');
                    }
                });
            }

            this.hideLoadingIndicator();
            console.log('✅ 降级初始化完成');

        } catch (fallbackError) {
            console.error('❌ 降级初始化也失败了:', fallbackError);
            this.showCriticalError();
        }
    }

    /**
     * 显示严重错误
     */
    showCriticalError() {
        document.body.innerHTML = `
            <div style="display: flex; justify-content: center; align-items: center; height: 100vh; background: #f8f9fa;">
                <div style="text-align: center; color: #dc3545;">
                    <h1>系统启动失败</h1>
                    <p>应用无法正常启动，请刷新页面重试</p>
                    <button onclick="location.reload()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">刷新页面</button>
                </div>
            </div>
        `;
    }

    /**
     * 更新加载进度
     */
    updateLoadingProgress(progress, message) {
        const progressBar = document.getElementById('loadingProgressBar');
        const loadingText = document.querySelector('.loading-text');

        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }

        if (loadingText && message) {
            loadingText.textContent = message;
        }

        this.loadingProgress = progress;
        console.log(`📊 加载进度: ${progress}% - ${message}`);
    }

    /**
     * 隐藏加载指示器
     */
    hideLoadingIndicator() {
        const indicator = document.getElementById('pageLoadingIndicator');
        if (indicator) {
            indicator.classList.add('hide');
            setTimeout(() => {
                indicator.remove();
            }, 1000);
        }
    }

    /**
     * 显示错误信息
     */
    showError(title, message, type = 'error') {
        // 尝试使用DOMManager，否则回退到传统方法
        let errorPanel;
        if (window.DOMManager && typeof window.DOMManager.get === 'function') {
            errorPanel = window.DOMManager.get('errorPanel');
        } else {
            errorPanel = document.getElementById('errorPanel');
        }

        if (!errorPanel) {
            console.error('错误面板未找到，使用控制台输出:', title, message);
            return;
        }

        // 更新错误内容
        const errorTitle = document.getElementById('error-title');
        const errorDescription = document.getElementById('error-description');
        const errorMessage = document.getElementById('error-message');
        const successMessage = document.getElementById('success-message');

        if (errorTitle) errorTitle.textContent = title;
        if (errorDescription) errorDescription.textContent = message;

        // 显示错误消息
        if (errorMessage) errorMessage.style.display = 'block';
        if (successMessage) successMessage.style.display = 'none';

        errorPanel.style.display = 'block';

        // 非严重错误自动隐藏
        if (!title.includes('严重') && !title.includes('失败')) {
            setTimeout(() => {
                this.hideError();
            }, 8000);
        }
    }

    /**
     * 隐藏错误信息
     */
    hideError() {
        let errorPanel;
        if (window.DOMManager && typeof window.DOMManager.get === 'function') {
            errorPanel = window.DOMManager.get('errorPanel');
        } else {
            errorPanel = document.getElementById('errorPanel');
        }

        if (errorPanel) {
            errorPanel.style.display = 'none';
        }

        const errorMessage = document.getElementById('error-message');
        const successMessage = document.getElementById('success-message');

        if (errorMessage) errorMessage.style.display = 'none';
        if (successMessage) successMessage.style.display = 'none';
    }

    /**
     * 清理应用资源
     */
    destroy() {
        console.log('🧹 清理CompleteFlowApp资源');

        // 清理各个模块
        try {
            WebSocketManager?.destroy?.();
            SearchController?.destroy?.();
            ResultRenderer?.destroy?.();
            PerformanceMonitor?.destroy?.();
            StateManager?.destroy?.();
            DOMManager?.destroy?.();
        } catch (error) {
            console.error('❌ 清理资源时发生错误:', error);
        }

        this.isInitialized = false;
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', async () => {
    console.log('📄 DOM内容已加载');

    // 创建应用实例
    window.completeFlowApp = new CompleteFlowApp();

    // 初始化应用
    try {
        await window.completeFlowApp.init();
    } catch (error) {
        console.error('❌ 应用启动失败:', error);
    }
});

// 确保页面完全加载后重新检查事件委托
window.addEventListener('load', () => {
    console.log('🖥️ 页面完全加载');

    // 延迟一点时间确保所有内容都已渲染
    setTimeout(() => {
        if (window.completeFlowApp && !window.completeFlowApp.globalEventDelegate) {
            console.log('🔗 重新设置全局事件委托');
            window.completeFlowApp.setupGlobalEventDelegation();
        }

        // 验证事件委托是否正常工作
        if (window.completeFlowApp && window.completeFlowApp.globalEventDelegate) {
            console.log('✅ 事件委托验证成功');
        } else {
            console.warn('⚠️ 事件委托可能未正确设置');
        }
    }, 1000);
});

// 额外的安全网：使用多重检查确保事件委托正常工作
function ensureEventDelegateWorking() {
    if (window.completeFlowApp) {
        if (!window.completeFlowApp.globalEventDelegate) {
            console.log('🔗 安全网：设置全局事件委托');
            window.completeFlowApp.setupGlobalEventDelegation();
        }

        // 总是设置紧急按钮处理器作为备用
        console.log('🚨 安全网：设置紧急按钮处理器');
        window.completeFlowApp.setupEmergencyButtonHandlers();
    }
}

// 在多个时机检查事件委托
setTimeout(ensureEventDelegateWorking, 2000);  // 2秒后检查
setTimeout(ensureEventDelegateWorking, 5000);  // 5秒后检查
setTimeout(ensureEventDelegateWorking, 8000);  // 8秒后检查

// 页面卸载时清理资源
window.addEventListener('beforeunload', () => {
    if (window.completeFlowApp) {
        window.completeFlowApp.destroy();
    }
});

// ====== 全局函数兼容性支持 ======
// 为了保持现有功能的兼容性，保留一些必要的全局函数

/**
 * 搜索可视化器兼容性对象
 */
window.searchVisualizer = {
    get appState() {
        return {
            currentTrace: window.StateManager?.get('search.currentTrace'),
            searchCompleted: window.StateManager?.get('search.completed'),
            stage4Modules: window.StateManager?.get('stage4Modules'),
            websocket: {
                readyState: window.WebSocketManager?.connection?.readyState
            }
        };
    }
};

// 保留关键的全局函数
window.selectSearchModule = function(searchPath) {
    console.log('🔍 选择搜索模块:', searchPath);

    const moduleData = window.StateManager?.getStage4Module(searchPath);
    if (moduleData && window.showModuleDetails) {
        window.showModuleDetails(searchPath);
    }
};


// ==================== 全局函数定义 ====================

/**
 * 显示模块详情 - 极简版
 * @param {string} searchPath - 搜索路径/模块名称
 */
window.showModuleDetails = function(searchPath) {
    console.log('🔍 显示模块详情:', searchPath);

    try {
        // 获取模块面板
        const modulePanel = document.getElementById('module-detail-panel');
        if (!modulePanel) {
            console.error('❌ 模块详情面板未找到');
            return;
        }

        // 检查面板是否已经显示，如果显示则替换内容
        const isCurrentlyVisible = modulePanel.style.display !== 'none';

        // 获取模块数据
        const stage4Modules = window.StateManager?.get?.('stage4Modules') || {};
        const moduleData = stage4Modules[searchPath];

        if (!moduleData) {
            showModuleError(modulePanel, searchPath);
            return;
        }

        // 显示模块信息（自动替换内容）
        showModuleBasicInfo(modulePanel, moduleData, searchPath);

        // 如果面板之前不可见，滚动到面板位置
        if (!isCurrentlyVisible) {
            setTimeout(() => {
                modulePanel.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest'
                });
            }, 100);
        }

        // 添加一个活跃状态标识当前模块
        highlightActiveModule(searchPath);

    } catch (error) {
        console.error('❌ 显示模块详情失败:', error);
    }
};

/**
 * 显示模块错误信息
 */
function showModuleError(panel, searchPath) {
    const titleElement = panel.querySelector('#module-detail-title');
    const contentElement = panel.querySelector('#module-detail-content');

    if (titleElement) titleElement.textContent = `模块详情: ${searchPath}`;
    if (contentElement) {
        contentElement.innerHTML = `
            <div class="alert alert-warning m-3">
                <div class="d-flex align-items-center">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <div>
                        <strong>数据不可用</strong><br>
                        <small>模块 "${searchPath}" 的数据暂不可用</small>
                    </div>
                </div>
            </div>
        `;
    }
        panel.style.display = 'block';
}

/**
 * 显示模块基本信息
 */
function showModuleBasicInfo(panel, moduleData, searchPath) {
    const titleElement = panel.querySelector('#module-detail-title');
    const contentElement = panel.querySelector('#module-detail-content');

    const displayName = getModuleDisplayName(searchPath);
    const articles = moduleData.output_data?.articles || [];
    const cases = moduleData.output_data?.cases || [];
    const processingTime = Math.round(moduleData.processing_time_ms || 0);

    if (titleElement) titleElement.textContent = `模块详情: ${displayName}`;

    if (contentElement) {
        contentElement.innerHTML = `
            <div class="module-basic-info">
                <div class="info-header d-flex justify-content-between align-items-center mb-3">
                    <span class="badge ${moduleData.status === 'success' ? 'bg-success' : 'bg-danger'}">
                        ${moduleData.status}
                    </span>
                    <small class="text-muted">${searchPath}</small>
                </div>

                <div class="row text-center mb-3">
                    <div class="col-3">
                        <div class="h4 text-primary mb-0">${articles.length}</div>
                        <div class="small text-muted">法条</div>
                    </div>
                    <div class="col-3">
                        <div class="h4 text-success mb-0">${cases.length}</div>
                        <div class="small text-muted">案例</div>
                    </div>
                    <div class="col-3">
                        <div class="h5 text-warning mb-0">${processingTime}ms</div>
                        <div class="small text-muted">耗时</div>
                    </div>
                    <div class="col-3">
                        <div class="h5 text-info mb-0">${confidence}%</div>
                        <div class="small text-muted">置信度</div>
                    </div>
                </div>

                ${articles.length > 0 ? `
                    <div class="mb-3">
                        <h6 class="text-primary">法条结果 (${articles.length})</h6>
                        <div class="list-group list-group-flush">
                            ${articles.slice(0, 2).map(article => `
                                <div class="list-group-item px-0">
                                    <div class="d-flex justify-content-between">
                                        <div class="fw-medium">${article.title || '未知法条'}</div>
                                        <small class="text-success">${((article.similarity || 0) * 100).toFixed(1)}%</small>
                                    </div>
                                </div>
                            `).join('')}
                            ${articles.length > 2 ? `
                                <div class="list-group-item px-0 text-center text-muted">
                                    <small>还有 ${articles.length - 2} 条法条...</small>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                ` : ''}

                ${cases.length > 0 ? `
                    <div class="mb-3">
                        <h6 class="text-success">案例结果 (${cases.length})</h6>
                        <div class="list-group list-group-flush">
                            ${cases.slice(0, 2).map(case_item => `
                                <div class="list-group-item px-0">
                                    <div class="d-flex justify-content-between">
                                        <div class="fw-medium">${case_item.case_id || '未知案例'}</div>
                                        <small class="text-warning">${((case_item.similarity || 0) * 100).toFixed(1)}%</small>
                                    </div>
                                </div>
                            `).join('')}
                            ${cases.length > 2 ? `
                                <div class="list-group-item px-0 text-center text-muted">
                                    <small>还有 ${cases.length - 2} 个案例...</small>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                ` : ''}

                ${moduleData.error_message ? `
                    <div class="alert alert-danger mt-3 mb-0">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <small>${moduleData.error_message}</small>
                    </div>
                ` : ''}
            </div>
        `;
    }

    panel.style.display = 'block';
}

/**
 * 高亮显示当前活跃的模块
 * @param {string} activeSearchPath - 当前活跃的模块路径
 */
function highlightActiveModule(activeSearchPath) {
    try {
        // 移除所有模块的活跃状态
        document.querySelectorAll('.module-overview-card').forEach(card => {
            card.classList.remove('active-module');
            card.style.border = '';
        });

        // 为当前模块添加活跃状态
        const activeCard = document.querySelector(`[data-module-path="${activeSearchPath}"]`)?.closest('.module-overview-card');
        if (activeCard) {
            activeCard.classList.add('active-module');
            activeCard.style.border = '2px solid #007bff';
            activeCard.style.boxShadow = '0 0 10px rgba(0,123,255,0.3)';
        }
    } catch (error) {
        console.warn('⚠️ 高亮活跃模块失败:', error);
    }
}

/**
 * 获取模块显示名称
 */
function getModuleDisplayName(searchPath) {
    const nameMap = {
        'semantic_search.vector_search': '向量搜索',
        'semantic_search.keyword_search': '关键词搜索',
        'semantic_search.hybrid_search': '混合搜索',
        'enhanced_semantic_search.query2doc': 'Query2Doc增强',
        'enhanced_semantic_search.hyde': 'HyDE增强',
        'vector_search_base': '基础向量搜索',
        'llm_enhanced_search': 'LLM增强搜索',
        'query2doc_expansion': 'Query2Doc扩展搜索',
        'hyde_search': 'HyDE假设搜索',
        'knowledge_graph_search': '知识图谱搜索'
    };
    return nameMap[searchPath] || searchPath;
}

/**
 * 切换答案显示完整/简略 - 平滑展开效果
 */
window.toggleAnswerFull = function() {
    console.log('🔄 切换答案显示模式');

    try {
        // 使用ID查找答案内容元素
        const answerElement = document.getElementById('ai-answer-content');
        const toggleBtn = document.getElementById('toggle-answer-btn');
        const toggleIcon = document.getElementById('toggle-answer-icon');
        const toggleText = document.getElementById('toggle-answer-text');

        if (!answerElement) {
            console.warn('⚠️ 答案内容元素未找到');
            return;
        }

        // 切换显示模式
        const isExpanded = answerElement.classList.contains('expanded');

        if (isExpanded) {
            // 收起状态
            answerElement.classList.remove('expanded');
            answerElement.classList.add('collapsed');
            answerElement.style.maxHeight = '100px';
            answerElement.style.overflow = 'hidden';

            // 更新按钮
            if (toggleIcon) toggleIcon.className = 'fas fa-chevron-down me-1';
            if (toggleText) toggleText.textContent = '展开完整回答';
            if (toggleBtn) {
                toggleBtn.className = 'btn btn-sm btn-outline-secondary mt-2 toggle-answer-btn';
                toggleBtn.setAttribute('data-action', 'toggle-answer');
            }

            console.log('📝 答案已收起');
        } else {
            // 展开状态
            answerElement.classList.remove('collapsed');
            answerElement.classList.add('expanded');
            answerElement.style.maxHeight = 'none';
            answerElement.style.overflow = 'visible';

            // 更新按钮
            if (toggleIcon) toggleIcon.className = 'fas fa-chevron-up me-1';
            if (toggleText) toggleText.textContent = '收起回答';
            if (toggleBtn) {
                toggleBtn.className = 'btn btn-sm btn-outline-secondary mt-2 toggle-answer-btn';
                toggleBtn.setAttribute('data-action', 'toggle-answer');
            }

            console.log('📖 答案已展开');
        }

        // 添加过渡动画
        answerElement.style.transition = 'max-height 0.3s ease-in-out, overflow 0.3s ease-in-out';

    } catch (error) {
        console.error('❌ 切换答案显示模式失败:', error);
    }
};

/**
 * 关闭模块详情面板
 */
window.hideModuleDetails = function() {
    console.log('🙈 关闭模块详情面板');

    const modulePanel = window.DOMManager?.get('module-detail-panel');
    if (modulePanel) {
        modulePanel.style.display = 'none';
        console.log('✅ 模块详情面板已关闭');
    }
};

/**
 * 显示单个模块的内联详情
 */
window.showModuleInline = function(modulePath) {
    console.log('🔍 显示模块内联详情:', modulePath);

    try {
        // 先显示整个内联区域
        window.displayModulesInline();

        // 展开指定的模块
        const targetModules = [
            'semantic_search.vector_search',
            'semantic_search.keyword_search',
            'semantic_search.hybrid_search',
            'enhanced_semantic_search.query2doc',
            'knowledge_graph_search'
        ];

        const moduleIndex = targetModules.indexOf(modulePath);
        if (moduleIndex !== -1) {
            setTimeout(() => {
                window.toggleInlineModule(moduleIndex);
            }, 100);
        }

    } catch (error) {
        console.error('❌ 显示模块内联详情失败:', error);
    }
};

/**
 * 显示5个搜索模块的内联详细内容
 */
window.displayModulesInline = function() {
    console.log('📋 开始显示5个搜索模块的内联详细内容');

    try {
        // 获取搜索结果数据
        const stage4Modules = window.StateManager?.get?.('stage4Modules') ||
                           window.currentSearchData?.stage4 ||
                           {};

        if (!stage4Modules || Object.keys(stage4Modules).length === 0) {
            console.warn('⚠️ 没有找到搜索模块数据');
            return;
        }

        // 获取内联显示区域
        const inlineDisplay = document.getElementById('modules-inline-display');
        const contentContainer = document.getElementById('modules-content-container');

        if (!inlineDisplay || !contentContainer) {
            console.error('❌ 内联显示区域未找到');
            return;
        }

        // 清空容器
        contentContainer.innerHTML = '';

        // 获取所有可用的搜索模块
        const availableModules = Object.keys(stage4Modules);
        console.log('🔍 发现的搜索模块:', availableModules);

        // 如果没有找到预定义的模块，则显示所有可用模块
        const targetModules = availableModules.length > 0 ? availableModules : [
            'semantic_search.vector_search',
            'semantic_search.keyword_search',
            'semantic_search.hybrid_search',
            'enhanced_semantic_search.query2doc',
            'knowledge_graph_search'
        ];

        console.log('🔍 将要显示的模块:', targetModules);

        // 调试：查看所有可用的模块
        console.log('🔍 可用的模块:', Object.keys(stage4Modules));
        console.log('🔍 目标模块:', targetModules);

        // 为每个模块创建内容
        targetModules.forEach((modulePath, index) => {
            const moduleData = stage4Modules[modulePath];
            console.log(`📋 模块 ${modulePath}:`, moduleData ? '存在' : '不存在');
            if (moduleData) {
                console.log(`📋 模块 ${modulePath} 数据:`, {
                    status: moduleData.status,
                    articles: moduleData.output_data?.articles?.length || 0,
                    cases: moduleData.output_data?.cases?.length || 0
                });
                const moduleElement = createInlineModuleElement(modulePath, moduleData, index);
                contentContainer.appendChild(moduleElement);
            } else {
                console.warn(`⚠️ 模块 ${modulePath} 数据不存在`);
            }
        });

        // 显示内联区域
        inlineDisplay.style.display = 'block';

        console.log(`✅ 成功显示 ${targetModules.length} 个搜索模块的详细内容`);

    } catch (error) {
        console.error('❌ 显示内联模块内容失败:', error);
    }
};

/**
 * 创建单个模块的内联显示元素
 */
function createInlineModuleElement(modulePath, moduleData, index) {
    const displayName = getModuleDisplayName(modulePath);
    const articles = moduleData.output_data?.articles || [];
    const cases = moduleData.output_data?.cases || [];
    const processingTime = Math.round(moduleData.processing_time_ms || 0);

    const moduleElement = document.createElement('div');
    moduleElement.className = 'inline-module-item';
    moduleElement.innerHTML = `
        <div class="inline-module-header" onclick="window.toggleInlineModule(${index})">
            <div class="module-title-section">
                <h6><i class="fas fa-search me-2"></i>${displayName}</h6>
                <div class="module-badges">
                    <span class="badge ${moduleData.status === 'success' ? 'bg-success' : 'bg-danger'}">
                        ${moduleData.status}
                    </span>
                    <span class="badge bg-info">${processingTime}ms</span>
                </div>
            </div>
            <div class="module-toggle">
                <i class="fas fa-chevron-down toggle-icon" id="toggle-icon-${index}"></i>
            </div>
        </div>
        <div class="inline-module-content" id="module-content-${index}" style="display:none;">
            <div class="module-content-grid">
                ${articles.length > 0 ? `
                    <div class="content-section">
                        <h7><i class="fas fa-gavel me-1"></i>相关法条 (${articles.length}条)</h7>
                        <div class="articles-container">
                            ${articles.slice(0, 5).map((article, articleIndex) => `
                                <div class="article-item" onclick="window.showItemDetail(${JSON.stringify(article).replace(/"/g, '&quot;')}, 'article')">
                                    <div class="article-title">#${articleIndex + 1} ${article.title || article.id}</div>
                                    <div class="article-similarity">相似度: ${((article.similarity || 0) * 100).toFixed(1)}%</div>
                                    <div class="article-content">${(article.content || '').substring(0, 100)}${(article.content || '').length > 100 ? '...' : ''}</div>
                                </div>
                            `).join('')}
                            ${articles.length > 5 ? `<div class="more-items">还有 ${articles.length - 5} 条法条...</div>` : ''}
                        </div>
                    </div>
                ` : ''}

                ${cases.length > 0 ? `
                    <div class="content-section">
                        <h7><i class="fas fa-folder me-1"></i>相关案例 (${cases.length}个)</h7>
                        <div class="cases-container">
                            ${cases.slice(0, 5).map((case_item, caseIndex) => `
                                <div class="case-item" onclick="window.showItemDetail(${JSON.stringify(case_item).replace(/"/g, '&quot;')}, 'case')">
                                    <div class="case-title">#${caseIndex + 1} ${case_item.title || case_item.id}</div>
                                    <div class="case-similarity">相似度: ${((case_item.similarity || 0) * 100).toFixed(1)}%</div>
                                    ${case_item.sentence_result ? `
                                        <div class="case-sentence">判决: ${case_item.sentence_result}</div>
                                    ` : ''}
                                    <div class="case-content">${(case_item.content || '').substring(0, 80)}${(case_item.content || '').length > 80 ? '...' : ''}</div>
                                </div>
                            `).join('')}
                            ${cases.length > 5 ? `<div class="more-items">还有 ${cases.length - 5} 个案例...</div>` : ''}
                        </div>
                    </div>
                ` : ''}

                ${!articles.length && !cases.length ? `
                    <div class="no-content">
                        <i class="fas fa-info-circle me-2"></i>该模块暂无详细数据
                    </div>
                ` : ''}
            </div>
        </div>
    `;

    return moduleElement;
}

/**
 * 切换单个模块的展开/收起状态
 */
window.toggleInlineModule = function(index) {
    const content = document.getElementById(`module-content-${index}`);
    const icon = document.getElementById(`toggle-icon-${index}`);
    const header = document.querySelector(`#module-content-${index}`).previousElementSibling;

    if (!content) return;

    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up toggle-icon';
        if (header) {
            header.classList.add('expanded');
        }
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down toggle-icon';
        if (header) {
            header.classList.remove('expanded');
        }
    }
};

/**
 * 全部展开/收起所有模块
 */
window.toggleAllModules = function() {
    const toggleBtn = document.getElementById('toggle-all-modules');
    const isExpanding = toggleBtn.innerHTML.includes('全部展开');

    // 切换所有模块内容
    for (let i = 0; i < 5; i++) {
        const content = document.getElementById(`module-content-${i}`);
        const icon = document.getElementById(`toggle-icon-${i}`);
        const header = content ? content.previousElementSibling : null;

        if (content && icon) {
            content.style.display = isExpanding ? 'block' : 'none';
            icon.className = isExpanding ? 'fas fa-chevron-up toggle-icon' : 'fas fa-chevron-down toggle-icon';

            if (header) {
                if (isExpanding) {
                    header.classList.add('expanded');
                } else {
                    header.classList.remove('expanded');
                }
            }
        }
    }

    // 更新按钮状态
    toggleBtn.innerHTML = isExpanding ?
        '<i class="fas fa-compress-alt me-1"></i>全部收起' :
        '<i class="fas fa-expand-alt me-1"></i>全部展开';
};

/**
 * 获取模块显示名称
 */
function getModuleDisplayName(searchPath) {
    const nameMap = {
        'vector_search': '向量搜索',
        'keyword_search': '关键词搜索',
        'hybrid_search': '混合搜索',
        'query2doc_enhancement': 'Query2Doc增强',
        'knowledge_graph_search': '知识图谱搜索',
        'semantic_search.vector_search': '向量搜索',
        'semantic_search.keyword_search': '关键词搜索',
        'semantic_search.hybrid_search': '混合搜索',
        'enhanced_semantic_search.query2doc': 'Query2Doc增强',
        'enhanced_semantic_search.hyde': 'HyDE增强',
        'llm_enhanced_search': 'LLM增强搜索'
    };
    return nameMap[searchPath] || searchPath;
}

/**
 * 获取嵌套对象的值
 * @param {Object} obj - 目标对象
 * @param {String} path - 路径字符串，如 'trace_data.output_data.final_articles'
 * @return {*} 找到的值或undefined
 */
function getNestedValue(obj, path) {
    if (!obj || !path) return undefined;

    const keys = path.split('.');
    let current = obj;

    for (const key of keys) {
        if (current === null || current === undefined || typeof current !== 'object') {
            return undefined;
        }
        current = current[key];
    }

    return current;
}

/**
 * 智能检测并提取最终结果数据
 * @param {Object} data - 要检测的数据对象
 * @return {Object} 包含articles和cases的对象
 */
function extractFinalResultsIntelligent(data) {
    console.log('[智能检测] 开始智能检测最终结果:', data);

    const result = {
        articles: [],
        cases: []
    };

    if (!data || typeof data !== 'object') {
        return result;
    }

    // 情况1：数据本身就是数组
    if (Array.isArray(data)) {
        console.log(`[智能检测] 检测到数组，长度: ${data.length}`);
        if (data.length > 0) {
            const firstItem = data[0];
            if (firstItem) {
                // 检测是否是文章类型
                if (firstItem.article_number || firstItem.title || firstItem.content) {
                    result.articles = data;
                    console.log(`[智能检测] 识别为文章数组，数量: ${data.length}`);
                }
                // 检测是否是案例类型
                else if (firstItem.case_id || firstItem.fact || firstItem.accusations) {
                    result.cases = data;
                    console.log(`[智能检测] 识别为案例数组，数量: ${data.length}`);
                }
            }
        }
        return result;
    }

    // 情况2：对象包含多个数组字段
    Object.keys(data).forEach(key => {
        const value = data[key];
        if (Array.isArray(value) && value.length > 0) {
            const firstItem = value[0];
            if (firstItem) {
                // 检测文章类型
                if (key.includes('article') || key.includes('law') || key.includes('legal') ||
                    firstItem.article_number || firstItem.title || firstItem.content) {
                    if (result.articles.length === 0) {
                        result.articles = value;
                        console.log(`[智能检测] 从字段 ${key} 找到 ${value.length} 条文章`);
                    }
                }
                // 检测案例类型
                else if (key.includes('case') || key.includes('example') ||
                        firstItem.case_id || firstItem.fact || firstItem.accusations) {
                    if (result.cases.length === 0) {
                        result.cases = value;
                        console.log(`[智能检测] 从字段 ${key} 找到 ${value.length} 个案例`);
                    }
                }
            }
        }
    });

    return result;
}

/**
 * 从文本中提取文章信息
 * @param {String} text - 包含文章信息的文本
 * @return {Array} 文章数组
 */
function extractArticlesFromText(text) {
    console.log('[文本提取] 开始从文本中提取文章信息，文本长度:', text.length);

    const articles = [];

    if (!text || typeof text !== 'string') {
        return articles;
    }

    try {
        // 尝试查找类似 "第X条" 或 "刑法第X条" 的模式
        const articlePatterns = [
            /(?:刑法)?第?(\d+)条[：:](.*?)(?=(?:刑法)?第?\d+条|$)/g,
            /第(\d+)条[：:](.*?)(?=第\d+条|$)/g,
            /《中华人民共和国刑法》第(\d+)条[：:](.*?)(?=《中华人民共和国刑法》第\d+条|$)/g
        ];

        for (const pattern of articlePatterns) {
            let match;
            while ((match = pattern.exec(text)) !== null) {
                const articleNumber = match[1];
                const content = match[2] ? match[2].trim() : '';

                if (articleNumber && content) {
                    articles.push({
                        article_number: articleNumber,
                        title: `刑法第${articleNumber}条`,
                        content: content,
                        source: '从文本提取'
                    });
                }
            }

            if (articles.length > 0) {
                break; // 找到了就停止
            }
        }

        // 如果正则匹配失败，尝试简单的句子分割
        if (articles.length === 0) {
            console.log('[文本提取] 正则匹配失败，尝试简单分割...');
            const sentences = text.split(/[。；;]/).filter(s => s.trim().length > 10);

            sentences.forEach((sentence, index) => {
                if (sentence.includes('条') && sentence.length > 20) {
                    articles.push({
                        article_number: `相关${index + 1}`,
                        title: `相关法律条文${index + 1}`,
                        content: sentence.trim(),
                        source: '文本分割提取'
                    });
                }
            });
        }

        console.log(`[文本提取] 成功提取 ${articles.length} 条文章`);

    } catch (error) {
        console.error('[文本提取] 提取过程出错:', error);
    }

    return articles.slice(0, 5); // 最多返回5条
}

/**
 * 显示最终搜索结果（final_articles 和 final_cases）
 */
window.displayFinalResults = function(finalData, finalAnswer) {
    console.log('[最终结果] 显示最终搜索结果:', { finalData, finalAnswer });

    const finalResultsDisplay = document.getElementById('final-results-display');
    if (!finalResultsDisplay) {
        console.warn('最终结果显示区域未找到');
        return;
    }

    // --- START OF FIX ---
    // 1. 渲染AI综合回答
    const header = finalResultsDisplay.querySelector('.final-results-header');
    // 移除旧的回答（如果有）
    const oldAnswerWrapper = finalResultsDisplay.querySelector('.final-answer-wrapper');
    if (oldAnswerWrapper) {
        oldAnswerWrapper.remove();
    }

    if (finalAnswer && header) {
        console.log('[AI回答] 渲染AI综合回答...');
        // 尝试使用StageRenderer的Markdown渲染器
        const markdownHtml = (window.StageRenderer && typeof window.StageRenderer.renderMarkdown === 'function')
            ? window.StageRenderer.renderMarkdown(finalAnswer)
            : finalAnswer.replace(/\n/g, '<br>');

        const answerHTML = `
            <div class="final-answer-wrapper" style="padding: 20px 30px; background: #f0faff; border-bottom: 1px solid #d4e9f7;">
                 <h6 style="font-weight: bold; color: #005a9e; display: flex; align-items: center; margin-bottom: 15px;">
                    <i class="fas fa-robot me-2"></i>AI 综合回答
                 </h6>
                 <div class="markdown-content" style="line-height: 1.7; font-size: 1rem;">${markdownHtml}</div>
            </div>
        `;
        header.insertAdjacentHTML('afterend', answerHTML);
    }
    // --- END OF FIX ---

    // 2. 渲染法条和案例
    const container = document.getElementById('final-results-container');
    if (!container) {
        console.warn('最终结果容器未找到');
        return;
    }

    // 🔧 确保结果按相关度分数排序（从高到低）
    let { final_articles = [], final_cases = [] } = finalData;
    
    final_articles = final_articles.sort((a, b) => (b.score || b.similarity || 0) - (a.score || a.similarity || 0));
    final_cases = final_cases.sort((a, b) => (b.score || b.similarity || 0) - (a.score || a.similarity || 0));
    
    console.log('[排序] 法条和案例已按相关度排序', {
        articlesCount: final_articles.length,
        casesCount: final_cases.length,
        topArticleScore: final_articles[0]?.score || 0,
        topCaseScore: final_cases[0]?.score || 0
    });

    // 默认显示文章标签页
    container.innerHTML = `
        <!-- 文章结果 -->
        <div id="final-articles-tab" class="final-tab-content">
            ${final_articles.length > 0 ? `
                <div class="final-results-grid">
                    ${final_articles.map((article, index) => `
                        <div class="final-result-card article-card clickable-result" onclick="window.showItemDetail(${JSON.stringify(article).replace(/"/g, '&quot;')}, 'article')">
                            <div class="card-header">
                                <div class="card-icon">
                                    <i class="fas fa-gavel"></i>
                                </div>
                                <div class="card-title-section">
                                    <h4 class="card-title">${article.article_number || `法条${index + 1}`}</h4>
                                    <div class="card-subtitle">${article.title || '法律条文'}</div>
                                </div>
                                <div class="card-score">
                                    <span class="score-label">相关度</span>
                                    <span class="score-value">${((article.score || article.similarity || 0) * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                            <div class="card-body">
                                <div class="article-content">
                                    ${(article.content || article.full_content || '暂无内容').substring(0, 150)}
                                    ${(article.content || article.full_content || '').length > 150 ? '...' : ''}
                                </div>
                                <div class="article-meta">
                                    ${article.chapter ? `<span class="meta-tag"><i class="fas fa-book me-1"></i>${article.chapter}</span>` : ''}
                                    ${article.related_cases ? `<span class="meta-tag"><i class="fas fa-link me-1"></i>${article.related_cases.length} 个相关案例</span>` : ''}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div class="no-final-results">
                    <i class="fas fa-search me-2"></i>暂无相关法律条文
                </div>
            `}
        </div>

        <!-- 案例结果 -->
        <div id="final-cases-tab" class="final-tab-content" style="display: none;">
            ${final_cases.length > 0 ? `
                <div class="final-results-grid">
                    ${final_cases.map((case_item, index) => `
                        <div class="final-result-card case-card clickable-result" onclick="window.showItemDetail(${JSON.stringify(case_item).replace(/"/g, '&quot;')}, 'case')">
                            <div class="card-header">
                                <div class="card-icon">
                                    <i class="fas fa-briefcase"></i>
                                </div>
                                <div class="card-title-section">
                                    <h4 class="card-title">${case_item.case_id || `案例${index + 1}`}</h4>
                                    <div class="card-subtitle">${case_item.accusations ? case_item.accusations.join(', ') : '刑事案例'}</div>
                                </div>
                                <div class="card-score">
                                    <span class="score-label">相关度</span>
                                    <span class="score-value">${((case_item.score || case_item.similarity || 0) * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                            <div class="card-body">
                                <div class="case-fact">
                                    ${(case_item.fact || case_item.content || '暂无案情描述').substring(0, 120)}
                                    ${(case_item.fact || case_item.content || '').length > 120 ? '...' : ''}
                                </div>
                                <div class="case-meta">
                                    ${case_item.relevant_articles ? `<span class="meta-tag"><i class="fas fa-gavel me-1"></i>${case_item.relevant_articles.join(', ')}</span>` : ''}
                                    ${case_item.sentence_months ? `<span class="meta-tag"><i class="fas fa-clock me-1"></i>${case_item.sentence_months}个月</span>` : ''}
                                    ${case_item.sentence_result ? `<span class="meta-tag"><i class="fas fa-balance-scale me-1"></i>${case_item.sentence_result}</span>` : ''}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div class="no-final-results">
                    <i class="fas fa-search me-2"></i>暂无相关案例
                </div>
            `}
        </div>
    `;

    // 更新统计信息
    document.getElementById('final-articles-count').textContent = final_articles.length;
    document.getElementById('final-cases-count').textContent = final_cases.length;

    // 3. 显示整个最终结果区域
    finalResultsDisplay.style.display = 'block';
    container.style.display = 'block'; // 确保内部容器也显示
    finalResultsDisplay.scrollIntoView({ behavior: 'smooth', block: 'start' });

    console.log(`[完成] 最终结果已显示: ${finalAnswer ? finalAnswer.length : 0}字符回答, ${final_articles.length}条法律条文, ${final_cases.length}个案例`);
};

/**
 * 切换最终结果标签页
 */
window.switchFinalResultsTab = function(tabType) {
    console.log(`[切换] 切换到${tabType === 'articles' ? '法律条文' : '案例'}标签页`);

    // 检查最终结果是否已经显示
    const finalResultsDisplay = document.getElementById('final-results-display');
    if (!finalResultsDisplay || finalResultsDisplay.style.display === 'none') {
        console.warn('[切换] 最终结果尚未显示，无法切换标签页');
        return;
    }

    // 更新标签按钮状态
    const articlesBtn = document.getElementById('final-articles-btn');
    const casesBtn = document.getElementById('final-cases-btn');

    if (!articlesBtn || !casesBtn) {
        console.warn('[切换] 标签按钮未找到');
        return;
    }

    if (tabType === 'articles') {
        articlesBtn.classList.add('active');
        casesBtn.classList.remove('active');
    } else {
        articlesBtn.classList.remove('active');
        casesBtn.classList.add('active');
    }

    // 切换内容显示
    const articlesTab = document.getElementById('final-articles-tab');
    const casesTab = document.getElementById('final-cases-tab');

    if (!articlesTab || !casesTab) {
        console.warn('[切换] 最终结果标签页元素未找到，可能最终结果尚未渲染:', {
            articlesTab: !!articlesTab,
            casesTab: !!casesTab
        });
        return;
    }

    if (tabType === 'articles') {
        articlesTab.style.display = 'block';
        casesTab.style.display = 'none';
    } else {
        articlesTab.style.display = 'none';
        casesTab.style.display = 'block';
    }
};

/**
 * 从搜索数据中提取并显示最终结果
 */
window.extractAndDisplayFinalResults = function(searchData) {
    console.log('[提取] 从搜索数据中提取最终结果:', searchData);

    if (!searchData || typeof searchData !== 'object') {
        console.warn('搜索数据格式不正确');
        return;
    }

    // 详细分析数据结构
    console.log('[提取] 数据结构分析:');
    console.log('- searchData类型:', typeof searchData);
    console.log('- searchData键:', Object.keys(searchData));

    if (searchData.trace_data) {
        console.log('- trace_data类型:', typeof searchData.trace_data);
        console.log('- trace_data键:', Object.keys(searchData.trace_data));

        if (searchData.trace_data.output_data) {
            console.log('- output_data类型:', typeof searchData.trace_data.output_data);
            console.log('- output_data键:', Object.keys(searchData.trace_data.output_data));
            console.log('- output_data内容:', searchData.trace_data.output_data);
        }
    }

    let finalData = {
        final_articles: [],
        final_cases: []
    };
    let finalAnswer = '';

    // 直接从阶段5的数据结构获取：output_data
    if (searchData.output_data) {
        console.log('[提取] 从阶段5数据结构提取最终结果');
        const outputData = searchData.output_data;

        // 直接提取最终结果
        finalData.final_articles = outputData.final_articles || [];
        finalData.final_cases = outputData.final_cases || [];
        finalAnswer = outputData.final_answer || '';

        console.log(`[提取] ✅ 提取完成: ${finalData.final_articles.length}条法条, ${finalData.final_cases.length}个案例, ${finalAnswer ? finalAnswer.length + '字符回答' : '无回答'}`);
    } else {
        console.warn('[提取] ❌ 未找到阶段5数据结构 output_data');
        console.log('[提取] 可用的数据键:', Object.keys(searchData));
    }

    // --- START OF MODIFICATION ---
    // 显示最终结果
    if (finalData.final_articles.length > 0 || finalData.final_cases.length > 0 || finalAnswer) {
        window.displayFinalResults(finalData, finalAnswer);
    } else {
        console.warn('未找到最终结果数据');
        // 显示空状态
        document.getElementById('final-results-container').innerHTML = `
            <div class="no-final-results">
                <i class="fas fa-info-circle me-2"></i>暂无最终搜索结果
            </div>
        `;

        // 显示最终结果显示区域
        const finalResultsDisplay = document.getElementById('final-results-display');
        if (finalResultsDisplay) {
            finalResultsDisplay.style.display = 'block';
            console.log('[最终结果] 最终结果显示区域已设为可见（空状态）');
        }

        document.getElementById('final-results-container').style.display = 'block';
    }
    // --- END OF MODIFICATION ---
};

console.log('[系统] CompleteFlowApp模块加载完成');