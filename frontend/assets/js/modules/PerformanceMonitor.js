/**
 * 性能监控器 - 统一性能监控和计时逻辑
 */
class PerformanceMonitor {
    constructor() {
        this.isInitialized = false;
        this.timers = new Map();
        this.metrics = {};
        this.timerInterval = null;
    }

    /**
     * 初始化性能监控器
     */
    initialize() {
        if (this.isInitialized) return;

        this.setupEventListeners();
        this.initializePerformancePanel();
        this.isInitialized = true;

        console.log('✅ PerformanceMonitor初始化完成');
    }

    /**
     * 设置事件监听
     */
    setupEventListeners() {
        // 确保EventBus已加载
        if (!window.EventBus) {
            console.warn('⚠️ EventBus未加载，延迟设置事件监听器');
            setTimeout(() => this.setupEventListeners(), 100);
            return;
        }

        // 监听搜索开始事件
        window.EventBus.on(window.AppEvents.SEARCH_START, () => {
            this.startSearchTimer();
        });

        // 监听搜索完成事件
        window.EventBus.on(window.AppEvents.SEARCH_COMPLETE, (data) => {
            this.completeSearchTimer(data);
        });

        // 监听性能指标更新事件
        window.EventBus.on(window.AppEvents.PERF_TIMER_UPDATE, (metrics) => {
            this.updateMetrics(metrics);
        });
    }

    /**
     * 初始化性能监控面板
     */
    initializePerformancePanel() {
        // 确保DOMManager可用
        if (!window.DOMManager || typeof window.DOMManager.get !== 'function') {
            console.error('❌ DOMManager不可用或get方法不存在');
            return;
        }

        // 显示性能监控面板
        const panel = window.DOMManager.get('performancePanel');
        if (panel) {
            panel.style.display = 'block';
        }

        // 设置初始值
        this.resetPerformanceDisplay();

        console.log('🎯 性能监控面板已初始化');
    }

    /**
     * 重置性能显示
     */
    resetPerformanceDisplay() {
        // 验证DOMManager及其方法是否可用
        if (!window.DOMManager || typeof window.DOMManager.updateTexts !== 'function') {
            console.error('❌ DOMManager.updateTexts不可用');
            return;
        }

        window.DOMManager.updateTexts({
            'debugTotalTime': '0ms',
            'debugApiTime': '0',
            'debugServerTime': '0',
            'debugFrontendTime': '0%',
            'debugApiPercent': '0%',
            'debugServerPercent': '0%',
            'debugFrontendPercent': '待评估'
        });

        const statusElement = window.DOMManager.get('debugTimerStatus');
        if (statusElement) {
            statusElement.textContent = '';
            statusElement.className = 'debug-timer-status';
        }
    }

    /**
     * 开始搜索计时
     */
    startSearchTimer() {
        console.log('⏱️ 开始搜索计时');

        const startTime = performance.now();
        this.timers.set('search_start', startTime);

        // 更新状态
        if (window.StateManager) {
            window.StateManager.set('performance.startTime', startTime);
        }

        // 启动实时计时器
        this.startRealtimeTimer(startTime);

        // 触发计时开始事件
        window.EventBus.emit(window.AppEvents.PERF_TIMER_START, { startTime });
    }

    /**
     * 启动实时计时器
     */
    startRealtimeTimer(startTime) {
        // 清除现有计时器
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }

        // 更新状态文本
        const statusElement = window.DOMManager.get('debugTimerStatus');
        const statusIconElement = window.DOMManager.get('debug-status-icon');
        const statusTextElement = window.DOMManager.get('debug-status-text');

        if (statusElement) {
            statusElement.className = 'debug-timer-status running';
        }

        if (statusIconElement) {
            statusIconElement.className = 'fas fa-spinner fa-spin me-2';
        }

        if (statusTextElement) {
            statusTextElement.textContent = '';
        }

        // 实时更新计时器
        this.timerInterval = setInterval(() => {
            const currentTime = performance.now();
            const elapsed = currentTime - startTime;

            window.DOMManager.updateTexts({
                'debugTotalTime': `${elapsed.toFixed(0)}ms`
            });

            // 更新进度条（估计最大时间为30秒）
            const progress = Math.min((elapsed / 30000) * 100, 100);
            const progressBar = document.getElementById('debugTotalProgress');
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }

        }, 100);
    }

    /**
     * 完成搜索计时
     */
    completeSearchTimer(searchData) {
        console.log('🏁 完成搜索计时');

        // 清除实时计时器
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }

        const startTime = this.timers.get('search_start');
        if (!startTime) {
            console.warn('⚠️ 搜索开始时间未找到');
            return;
        }

        const endTime = performance.now();
        const totalDuration = endTime - startTime;

        // 立即更新状态显示为完成状态
        this.updateStatusDisplayToCompleted(totalDuration);

        // 计算各部分耗时
        const timings = this.calculateTimings(totalDuration, searchData);

        // 更新总耗时显示（由updateTimerDisplay处理）
        this.updateTimerDisplay(timings);

        // 从searchData中提取或创建正确的metrics数据
        const performanceMetrics = {
            totalDuration: `${totalDuration.toFixed(0)}ms`,
            stagesCompleted: searchData.stagesCompleted || searchData.completed_stages || 4,
            successfulModules: searchData.successfulModules || searchData.modules || 3,
            highestConfidence: searchData.highestConfidence || searchData.confidence || 95
        };

        console.log('📊 完成时的性能指标:', performanceMetrics);

        // 使用updateMetrics正确更新其他显示项
        this.updateMetrics(performanceMetrics);

        // 保存指标
        this.metrics = timings;
        if (window.StateManager) {
            window.StateManager.updatePerformanceMetrics(timings);
        }

        // 触发计时完成事件
        window.EventBus.emit(window.AppEvents.PERF_TIMER_COMPLETE, timings);
    }

    /**
     * 计算各部分耗时
     */
    calculateTimings(totalDuration, searchData) {
        // 从搜索数据中提取实际耗时
        const apiTime = searchData.api_time || totalDuration * 0.8;
        const serverTime = searchData.server_processing_time || totalDuration * 0.75;
        const frontendTime = totalDuration * 0.05;

        return {
            total: totalDuration,
            api: apiTime,
            server: serverTime,
            frontend: frontendTime,
            // 计算百分比
            apiPercent: (apiTime / totalDuration) * 100,
            serverPercent: (serverTime / totalDuration) * 100,
            frontendPercent: (frontendTime / totalDuration) * 100
        };
    }

    /**
     * 更新计时器显示
     */
    updateTimerDisplay(timings) {
        console.log('📊 更新性能指标显示:', timings);

        // 更新总耗时（这是正确的）
        window.DOMManager.updateTexts({
            'debugTotalTime': `${timings.total.toFixed(0)}ms`
        });

        // 不再更新其他显示项，让updateMetrics处理这些逻辑
        // 更新状态
        this.updateStatusDisplay(timings.total);
    }

    /**
     * 更新状态显示为完成状态
     */
    updateStatusDisplayToCompleted(totalTime) {
        const statusElement = window.DOMManager.get('debugTimerStatus');
        const statusIconElement = window.DOMManager.get('debug-status-icon');
        const statusTextElement = window.DOMManager.get('debug-status-text');
        const statusTimeElement = window.DOMManager.get('debug-status-time');

        if (!statusElement) return;

        let statusClass = 'success';
        let iconClass = 'fa-check-circle';
        let statusText = '';

        // 根据耗时设置状态
        if (totalTime > 20000) {
            statusClass = 'error';
            iconClass = 'fa-exclamation-triangle';
            statusText = '';
        } else if (totalTime > 10000) {
            statusClass = 'warning';
            iconClass = 'fa-exclamation-circle';
            statusText = '';
        }

        // 更新状态显示
        statusElement.className = `debug-timer-status ${statusClass}`;

        if (statusIconElement) {
            statusIconElement.className = `fas ${iconClass} me-2`;
        }

        if (statusTextElement) {
            statusTextElement.textContent = statusText;
        }

        if (statusTimeElement) {
            statusTimeElement.textContent = ` - 耗时: ${totalTime.toFixed(0)}ms`;
            statusTimeElement.style.display = 'inline';
        }

        // 输出性能分析
        this.logPerformanceAnalysis(totalTime);
    }

    /**
     * 更新状态显示
     */
    updateStatusDisplay(totalTime) {
        const statusElement = window.DOMManager.get('debugTimerStatus');
        const statusIconElement = window.DOMManager.get('debug-status-icon');
        const statusTextElement = window.DOMManager.get('debug-status-text');
        const statusTimeElement = window.DOMManager.get('debug-status-time');

        if (!statusElement) return;

        let statusClass = 'success';
        let iconClass = 'fa-check-circle';
        let statusText = '';

        // 根据耗时设置状态
        if (totalTime > 20000) {
            statusClass = 'error';
            iconClass = 'fa-exclamation-triangle';
            statusText = '';
        } else if (totalTime > 10000) {
            statusClass = 'warning';
            iconClass = 'fa-exclamation-circle';
            statusText = '';
        }

        // 更新状态显示
        statusElement.className = `debug-timer-status ${statusClass}`;

        if (statusIconElement) {
            statusIconElement.className = `fas ${iconClass} me-2`;
        }

        if (statusTextElement) {
            statusTextElement.textContent = statusText;
        }

        if (statusTimeElement) {
            statusTimeElement.textContent = ` - 耗时: ${totalTime.toFixed(0)}ms`;
            statusTimeElement.style.display = 'inline';
        }

        // 输出性能分析
        this.logPerformanceAnalysis(totalTime);
    }

    /**
     * 输出性能分析
     */
    logPerformanceAnalysis(totalTime) {
        console.log(`📈 性能分析:`);
        console.log(`  总耗时: ${totalTime.toFixed(0)}ms`);

        if (totalTime > 10000) {
            console.warn(`⚠️ [性能警告] 总耗时${totalTime.toFixed(0)}ms超过10秒，可能存在性能问题！`);

            if (this.metrics.api > totalTime * 0.8) {
                console.warn(`  🔍 API调用耗时过长: ${this.metrics.api.toFixed(0)}ms`);
            }

            if (this.metrics.frontend > 2000) {
                console.warn(`  🎨 前端渲染耗时过长: ${this.metrics.frontend.toFixed(0)}ms`);
            }
        } else {
            console.log(`✅ 性能表现良好`);
        }
    }

    /**
     * 更新指标
     */
    updateMetrics(metrics) {
        console.log('📊 更新性能指标:', metrics);

        // 检查数据类型，处理可能的时间数据转换为计数数据
        let stagesCompleted = metrics.stagesCompleted || 0;
        let successfulModules = metrics.successfulModules || 0;
        let highestConfidence = metrics.highestConfidence || 0;

        // 如果传入的是时间数据（包含ms），尝试从其他字段获取正确的计数数据
        if (typeof stagesCompleted === 'string' && stagesCompleted.includes('ms')) {
            console.warn('⚠️ stagesCompleted包含时间单位，尝试使用其他字段');
            stagesCompleted = metrics.completed_stages || metrics.stages || 0;
        }

        if (typeof successfulModules === 'string' && successfulModules.includes('ms')) {
            console.warn('⚠️ successfulModules包含时间单位，尝试使用其他字段');
            successfulModules = metrics.modules || metrics.successful || 0;
        }

        if (typeof highestConfidence === 'string' && highestConfidence.includes('ms')) {
            console.warn('⚠️ highestConfidence包含时间单位，尝试使用其他字段');
            highestConfidence = metrics.confidence || metrics.score || 0;
        }

        // 确保数据类型正确
        stagesCompleted = parseInt(stagesCompleted) || 0;
        successfulModules = parseInt(successfulModules) || 0;
        highestConfidence = parseFloat(highestConfidence) || 0;

        console.log('📊 处理后的数据:', {
            stagesCompleted,
            successfulModules,
            highestConfidence
        });

        if (metrics.totalDuration) {
            window.DOMManager.updateTexts({
                'debugTotalTime': metrics.totalDuration,
                'debugApiTime': stagesCompleted,
                'debugServerTime': successfulModules,
                'debugFrontendTime': `${highestConfidence}%`
            });
        }

        // 更新子标题信息
        const completed = stagesCompleted;
        const stagesPercent = Math.round((completed / 5) * 100);
        window.DOMManager.updateTexts({
            'debugApiPercent': `${stagesPercent}%`
        });

        const successful = successfulModules;
        const total = 4; // 总共4个模块
        const modulesPercent = Math.round((successful / total) * 100);
        window.DOMManager.updateTexts({
            'debugServerPercent': `${modulesPercent}%`
        });

        let confidenceLevel = '待评估';
        if (highestConfidence >= 80) {
            confidenceLevel = '高置信度';
        } else if (highestConfidence >= 60) {
            confidenceLevel = '中置信度';
        } else if (highestConfidence > 0) {
            confidenceLevel = '低置信度';
        }

        window.DOMManager.updateTexts({
            'debugFrontendPercent': confidenceLevel
        });

        // 显示性能面板
        const panel = window.DOMManager.get('performancePanel');
        if (panel) {
            panel.style.display = 'block';
        }
    }

    /**
     * 创建自定义计时器
     */
    startTimer(name) {
        const startTime = performance.now();
        this.timers.set(name, startTime);
        console.log(`⏱️ 开始计时: ${name}`);
        return startTime;
    }

    /**
     * 停止自定义计时器
     */
    stopTimer(name) {
        const startTime = this.timers.get(name);
        if (!startTime) {
            console.warn(`⚠️ 计时器不存在: ${name}`);
            return 0;
        }

        const endTime = performance.now();
        const duration = endTime - startTime;

        this.timers.delete(name);
        console.log(`⏱️ 计时结束: ${name} - 耗时: ${duration.toFixed(2)}ms`);

        return duration;
    }

    /**
     * 获取计时器状态
     */
    getTimerDuration(name) {
        const startTime = this.timers.get(name);
        if (!startTime) {
            return 0;
        }

        return performance.now() - startTime;
    }

    /**
     * 获取当前性能指标
     */
    getCurrentMetrics() {
        return { ...this.metrics };
    }

    /**
     * 清理计时器
     */
    clearTimers() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }

        this.timers.clear();
        this.metrics = {};

        console.log('🧹 性能计时器已清理');
    }

    /**
     * 重置性能监控
     */
    reset() {
        this.clearTimers();
        this.resetPerformanceDisplay();
        if (window.StateManager) {
            window.StateManager.set('performance.startTime', null);
            window.StateManager.set('performance.metrics', {});
        }

        console.log('🔄 性能监控已重置');
    }

    /**
     * 获取性能报告
     */
    getPerformanceReport() {
        const report = {
            metrics: this.getCurrentMetrics(),
            activeTimers: Array.from(this.timers.keys()),
            timestamp: new Date().toISOString()
        };

        console.log('📋 性能报告:', report);
        return report;
    }

    /**
     * 清理资源
     */
    destroy() {
        this.clearTimers();
        console.log('🧹 PerformanceMonitor已清理');
    }
}

// 创建并导出单例
if (!window.PerformanceMonitor) {
    window.PerformanceMonitor = new PerformanceMonitor();
}