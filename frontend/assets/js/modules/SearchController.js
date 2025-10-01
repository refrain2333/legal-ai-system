/**
 * 搜索控制器 - 统一搜索逻辑和状态控制
 */
class SearchController {
    constructor() {
        this.isInitialized = false;
        this.debounceTimer = null;
        this.debounceDelay = 300;

        this.setupEventListeners();
    }

    /**
     * 初始化搜索控制器
     */
    initialize() {
        if (this.isInitialized) return;

        this.bindSearchEvents();
        this.setupStateMonitoring();
        this.isInitialized = true;

        console.log('✅ SearchController初始化完成');
    }

    /**
     * 绑定搜索相关事件
     */
    bindSearchEvents() {
        const searchBtn = window.DOMManager?.get('searchBtn');
        const searchQuery = window.DOMManager?.get('searchQuery');
        const clearBtn = window.DOMManager?.get('clearBtn');

        if (searchBtn) {
            searchBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.performSearch();
            });
        }

        if (searchQuery) {
            searchQuery.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !window.StateManager?.get('search.inProgress')) {
                    this.performSearch();
                }
            });

            // 添加输入防抖
            searchQuery.addEventListener('input', (e) => {
                this.handleQueryInput(e.target.value);
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearSearch();
            });
        }
    }

    /**
     * 设置状态监控
     */
    setupStateMonitoring() {
        // 确保StateManager可用
        if (!window.StateManager || typeof window.StateManager.on !== 'function') {
            console.warn('⚠️ StateManager不可用，跳过状态监听设置');
            return;
        }

        // 监听搜索状态变化
        window.StateManager.on('search.inProgress', (inProgress) => {
            this.updateSearchButtonState(inProgress);
        });

        // 监听WebSocket状态变化
        window.StateManager.on('websocket.connected', (connected) => {
            this.updateConnectionIndicator(connected);
        });
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 确保EventBus已加载
        if (!window.EventBus) {
            console.warn('⚠️ EventBus未加载，延迟设置事件监听器');
            setTimeout(() => this.setupEventListeners(), 100);
            return;
        }

        // 监听搜索完成事件
        window.EventBus.on(window.AppEvents.SEARCH_COMPLETE, (data) => {
            this.onSearchCompleted(data);
        });

        // 监听搜索错误事件
        window.EventBus.on(window.AppEvents.SEARCH_ERROR, (error) => {
            this.onSearchError(error);
        });

        // 监听阶段完成事件
        window.EventBus.on(window.AppEvents.STAGE_COMPLETE, (data) => {
            this.onStageCompleted(data);
        });

        // 监听模块完成事件
        window.EventBus.on(window.AppEvents.MODULE_COMPLETE, (data) => {
            this.onModuleCompleted(data);
        });
    }

    /**
     * 处理查询输入（防抖）
     */
    handleQueryInput(query) {
        clearTimeout(this.debounceTimer);

        this.debounceTimer = setTimeout(() => {
            this.validateQuery(query);
        }, this.debounceDelay);
    }

    /**
     * 验证查询输入
     */
    validateQuery(query) {
        const trimmedQuery = query.trim();

        if (trimmedQuery.length === 0) {
            this.showQueryHint('请输入查询内容');
        } else if (trimmedQuery.length < 2) {
            this.showQueryHint('查询内容至少需要2个字符');
        } else {
            this.hideQueryHint();
        }
    }

    /**
     * 显示查询提示
     */
    showQueryHint(message) {
        // 可以在这里添加提示显示逻辑
        console.log('💡 查询提示:', message);
    }

    /**
     * 隐藏查询提示
     */
    hideQueryHint() {
        // 隐藏提示的逻辑
    }

    /**
     * 执行搜索
     */
    async performSearch() {
        const query = window.DOMManager?.get('searchQuery')?.value?.trim();

        if (!this.validateSearchConditions(query)) {
            return;
        }

        console.log('🔍 开始搜索:', query);

        try {
            // 更新状态
            if (window.StateManager && typeof window.StateManager.startSearch === 'function') {
                window.StateManager.startSearch(query);
            }
            if (window.StateManager && typeof window.StateManager.startPerformanceTimer === 'function') {
                window.StateManager.startPerformanceTimer();
            }

            // 触发搜索开始事件
            window.EventBus.emit(window.AppEvents.SEARCH_START, { query });

            // 重置管道阶段
            this.resetPipelineStages();

            // 执行搜索请求
            await this.executeSearchRequest(query);

        } catch (error) {
            console.error('❌ 搜索执行失败:', error);
            this.handleSearchError(error);
        }
    }

    /**
     * 验证搜索条件
     */
    validateSearchConditions(query) {
        if (!query) {
            this.showError('请输入搜索内容', 'warning');
            return false;
        }

        if (window.StateManager && window.StateManager.get('search.inProgress')) {
            this.showError('搜索正在进行中，请稍候', 'info');
            return false;
        }

        return true;
    }

    /**
     * 执行搜索请求
     */
    async executeSearchRequest(query) {
        const apiUrl = window.apiConfig.getApiUrl('/api/search/debug');
        const startTime = performance.now();

        console.log('📡 发送搜索请求到:', apiUrl);

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });

            const endTime = performance.now();
            const apiDuration = endTime - startTime;

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            console.log('✅ 搜索请求完成，耗时:', Math.round(apiDuration), 'ms');

            // 如果没有通过WebSocket完成，处理HTTP响应
            if (!window.StateManager || !window.StateManager.get('search.completed')) {
                this.handleSearchResult(result);
            }

        } catch (error) {
            console.error('❌ 搜索请求失败:', error);
            throw error;
        }
    }

    /**
     * 处理搜索结果
     */
    handleSearchResult(result) {
        console.log('📋 处理搜索结果:', result);

        // 保存搜索轨迹
        if (window.StateManager) {
            window.StateManager.set('search.currentTrace', result.trace);
        }

        // 如果WebSocket已连接，优先使用实时更新
        if (window.WebSocketManager.isConnected()) {
            console.log('🌐 使用WebSocket实时更新模式');
            // WebSocket会处理实时更新，这里不需要重复渲染
        } else {
            console.log('📄 使用HTTP响应模式');
            this.renderSearchTrace(result.trace);
        }

        // 更新性能指标
        if (result.trace) {
            this.updatePerformanceMetrics(result.trace);
        }
    }

    /**
     * 渲染搜索轨迹
     */
    renderSearchTrace(trace) {
        if (!trace) return;

        // 使用AnimationController进行渐进式显示
        if (window.AnimationController) {
            window.AnimationController.startProgressiveDisplay(trace, {
                stage1: (data) => window.StageRenderer?.renderStage1(data),
                stage2: (data) => window.StageRenderer?.renderStage2(data),
                stage3: (data) => window.StageRenderer?.renderStage3(data),
                stage4: (data) => window.StageRenderer?.renderStage4(data),
                stage5: (data) => window.StageRenderer?.renderStage5(data)
            });
        }
    }

    /**
     * 重置管道阶段
     */
    resetPipelineStages() {
        console.log('🔄 重置管道阶段');

        // 重置阶段状态
        if (window.StateManager) {
            window.StateManager.set('stages.current', 0);
            window.StateManager.set('stages.completed', []);
            window.StateManager.set('stages.data', {});
            window.StateManager.set('stage4Modules', {});
        }

        // 重置阶段UI
        for (let i = 1; i <= 5; i++) {
            const stageElement = window.DOMManager?.get(`stage${i}`);
            const resultElement = window.DOMManager?.get(`stage${i}-result`);
            const timeElement = window.DOMManager?.get(`stage${i}-time`);

            if (stageElement && resultElement && timeElement) {
                stageElement.className = 'stage pending';
                resultElement.textContent = this.getStageWaitingMessage(i);
                timeElement.textContent = '耗时: 0ms';
            }
        }

        // 隐藏搜索结果
        if (window.DOMManager && typeof window.DOMManager.updateVisibility === 'function') {
            window.DOMManager.updateVisibility({
                'searchResults': false,
                'articles-results-section': false,
                'cases-results-section': false,
                'realtime-results-container': false
            });
        }
    }

    /**
     * 获取阶段等待消息
     */
    getStageWaitingMessage(stageNumber) {
        const messages = {
            1: '等待分析用户查询...',
            2: '等待提取罪名和关键词...',
            3: '等待选择搜索路径...',
            4: '等待执行搜索...',
            5: '等待生成最终回答...'
        };
        return messages[stageNumber] || `等待阶段${stageNumber}...`;
    }

    /**
     * 清空搜索
     */
    clearSearch() {
        console.log('🧹 清空搜索结果');

        // 重置状态
        if (window.StateManager) {
            window.StateManager.resetSearch();
        }

        // 重置UI
        this.resetPipelineStages();

        // 清空输入
        const searchQuery = window.DOMManager?.get('searchQuery');
        if (searchQuery) {
            searchQuery.value = '';
        }

        // 触发清空事件
        window.EventBus.emit(window.AppEvents.SEARCH_RESET);
    }

    /**
     * 更新搜索按钮状态
     */
    updateSearchButtonState(isSearching) {
        const iconElement = window.DOMManager?.get('search-btn-icon');
        const textElement = window.DOMManager?.get('search-btn-text');
        const searchBtn = window.DOMManager?.get('searchBtn');

        if (iconElement && textElement && searchBtn) {
            if (isSearching) {
                iconElement.className = 'fas fa-spinner fa-spin me-2';
                textElement.textContent = '搜索中...';
                searchBtn.disabled = true;
            } else {
                iconElement.className = 'fas fa-search me-2';
                textElement.textContent = '开始调试搜索';
                searchBtn.disabled = false;
            }
        }
    }

    /**
     * 更新连接指示器
     */
    updateConnectionIndicator(connected) {
        const statusElement = window.DOMManager?.get('websocketStatus');
        const iconElement = window.DOMManager?.get('websocket-icon');
        const textElement = window.DOMManager?.get('websocket-text');

        if (statusElement && iconElement && textElement) {
            const status = connected ? 'connected' : 'disconnected';
            const message = connected ? '已连接' : '已断开';
            const iconClass = connected ? 'fa-plug' : 'fa-times';

            statusElement.className = `websocket-status websocket-${status}`;
            iconElement.className = `fas ${iconClass} me-2`;
            textElement.textContent = `WebSocket ${message}`;
        }
    }

    /**
     * 搜索完成处理
     */
    onSearchCompleted(data) {
        console.log('🎉 搜索完成:', data);

        // 更新状态
        if (window.StateManager) {
            window.StateManager.completeSearch(data.results);
        }

        // 显示结果
        if (data.results && data.results.length > 0) {
            this.displaySearchResults(data.results);
            this.showSuccess(`找到 ${data.results.length} 条相关结果`, '搜索完成');
        } else {
            this.showError('未找到相关结果', 'info');
        }
    }

    /**
     * 阶段完成处理
     */
    onStageCompleted(data) {
        console.log(`📋 阶段${data.stage_number}完成:`, data.stage_name);

        // 更新状态
        if (window.StateManager) {
            window.StateManager.completeStage(data.stage_number, data.trace_data);
        }

        // 渲染阶段UI
        this.renderStageUI(data.stage_number, data.trace_data);
    }

    /**
     * 模块完成处理
     */
    onModuleCompleted(data) {
        console.log(`🔧 模块完成:`, data.module_name, data);

        // 提取正确的模块数据结构
        const moduleData = data.trace_data || data;
        const moduleName = moduleData.module_name || data.module_name;
        
        console.log('🔍 模块数据结构检查:', {
            topLevelModule: data.module_name,
            traceDataModule: moduleData.module_name,
            hasOutputData: !!moduleData.output_data,
            hasArticles: !!moduleData.output_data?.articles,
            hasCase: !!moduleData.output_data?.cases,
            articlesCount: moduleData.output_data?.articles?.length || 0,
            casesCount: moduleData.output_data?.cases?.length || 0
        });

        // 更新状态
        if (window.StateManager) {
            console.log('🔍 更新StateManager前，当前stage4Modules:', window.StateManager.get('stage4Modules'));
            window.StateManager.updateStage4Module(moduleName, moduleData);
            console.log('🔍 更新StateManager后，当前stage4Modules:', window.StateManager.get('stage4Modules'));
        }

        // 重新渲染阶段4（因为模块更新了）
        this.updateStage4Modules();
    }

    /**
     * 搜索错误处理
     */
    onSearchError(error) {
        console.error('❌ 搜索错误:', error);
        this.handleSearchError(error);
    }

    /**
     * 处理搜索错误
     */
    handleSearchError(error) {
        if (window.StateManager) {
            window.StateManager.set('search.inProgress', false);
        }
        this.showError('搜索失败: ' + (error.message || '未知错误'), '搜索失败');
        window.EventBus.emit(window.AppEvents.SEARCH_ERROR, error);
    }

    /**
     * 显示搜索结果
     */
    displaySearchResults(results) {
        // 这里可以调用ResultRenderer来显示结果
        if (window.ResultRenderer) {
            window.ResultRenderer.displayResults(results);
        }
    }

    /**
     * 更新性能指标
     */
    updatePerformanceMetrics(trace) {
        if (window.DataFormatter) {
            const metrics = window.DataFormatter.formatPerformanceMetrics(trace);
            if (metrics) {
                if (window.StateManager) {
                    window.StateManager.updatePerformanceMetrics(metrics);
                }
                window.EventBus.emit(window.AppEvents.PERF_TIMER_UPDATE, metrics);
            }
        }
    }

    /**
     * 显示错误信息
     */
    showError(message, title = '错误') {
        window.EventBus.emit(window.AppEvents.UI_ERROR_SHOW, { title, message });
    }

    /**
     * 显示成功信息
     */
    showSuccess(message, title = '成功') {
        window.EventBus.emit(window.AppEvents.UI_ERROR_SHOW, { title, message, type: 'success' });
    }

    /**
     * 渲染阶段UI
     */
    renderStageUI(stageNumber, traceData) {
        console.log(`🎨 渲染阶段${stageNumber}UI:`, traceData);

        try {
            // 更新阶段状态为完成
            const stageElement = window.DOMManager?.get(`stage${stageNumber}`);
            if (stageElement) {
                stageElement.className = 'stage completed';
            }

            // 更新阶段时间
            const timeElement = window.DOMManager?.get(`stage${stageNumber}-time`);
            if (timeElement && traceData.processing_time_ms) {
                timeElement.textContent = `耗时: ${Math.round(traceData.processing_time_ms)}ms`;
            }

            // 更新阶段结果显示
            const resultElement = window.DOMManager?.get(`stage${stageNumber}-result`);
            if (resultElement) {
                resultElement.textContent = `${traceData.stage_name || '阶段'}完成`;
            }

            // 渲染详细内容（如果有StageRenderer）
            if (window.StageRenderer && typeof window.StageRenderer[`renderStage${stageNumber}`] === 'function') {
                // 阶段4使用特殊的details元素
                const detailsId = stageNumber === 4 ? `stage${stageNumber}-details-inline` : `stage${stageNumber}-details`;
                const detailsElement = window.DOMManager?.get(detailsId);

                if (detailsElement) {
                    console.log(`🎨 渲染阶段${stageNumber}详细内容`);
                    const renderedContent = window.StageRenderer[`renderStage${stageNumber}`](traceData);
                    detailsElement.innerHTML = renderedContent;
                    console.log(`✅ 阶段${stageNumber}详细内容已渲染`);
                } else {
                    console.warn(`⚠️ 阶段${stageNumber}详细元素未找到: ${detailsId}`);
                }
            } else {
                console.warn(`⚠️ StageRenderer或方法renderStage${stageNumber}不可用`);
            }

            // 特殊处理：如果是阶段5，存储最终结果数据并显示最终结果
            if (stageNumber === 5) {
                console.log('[最终结果] 阶段5完成，存储最终结果数据:', traceData);

                // 将阶段5的数据存储为最终结果
                if (window.StateManager) {
                    // 存储完整的traceData，包含trace_data.output_data
                    window.StateManager.set('search.finalResults', traceData);
                    console.log('[最终结果] 已将阶段5数据存储到 search.finalResults');

                    // 同时也存储为search.data，保持兼容性
                    window.StateManager.set('search.data', traceData);
                    console.log('[最终结果] 已将阶段5数据存储到 search.data');
                }

                // 同时存储到全局变量，确保其他地方可以访问
                window.finalSearchResults = traceData;
                console.log('[最终结果] 已将阶段5数据存储到全局变量 finalSearchResults');

                // 🎯 在阶段5完成后立即显示最终结果
                setTimeout(() => {
                    if (window.extractAndDisplayFinalResults && typeof window.extractAndDisplayFinalResults === 'function') {
                        console.log('[最终结果] 阶段5完成，开始显示最终结果');
                        window.extractAndDisplayFinalResults(traceData);
                    } else {
                        console.error('[最终结果] extractAndDisplayFinalResults函数不可用');
                    }
                }, 500); // 短暂延迟确保DOM已更新
            }

        } catch (error) {
            console.error(`❌ 渲染阶段${stageNumber}UI失败:`, error);
        }
    }

    /**
     * 更新阶段4模块
     */
    updateStage4Modules() {
        console.log('🔄 更新阶段4模块显示');

        try {
            // 获取所有阶段4模块数据
            const stage4Modules = window.StateManager?.get('stage4Modules') || {};
            console.log('🔍 阶段4模块数据:', stage4Modules);

            if (Object.keys(stage4Modules).length > 0) {
                // 如果有StageRenderer，使用它渲染阶段4
                console.log('🔍 检查StageRenderer:', {
                    exists: !!window.StageRenderer,
                    hasRenderStage4: typeof window.StageRenderer?.renderStage4 === 'function'
                });

                if (window.StageRenderer && typeof window.StageRenderer.renderStage4 === 'function') {
                    const detailsElement = window.DOMManager?.get('stage4-details-inline');
                    const fallbackElement = document.getElementById('stage4-details-inline');

                    console.log('🔍 检查详细元素:', {
                        domManagerElement: !!detailsElement,
                        fallbackElement: !!fallbackElement,
                        elementId: 'stage4-details-inline',
                        availableIds: Array.from(document.querySelectorAll('[id*="stage4"]')).map(el => el.id)
                    });

                    const targetElement = detailsElement || fallbackElement;
                    if (targetElement) {
                        console.log('🎨 开始渲染阶段4模块内容...');
                        const renderedContent = window.StageRenderer.renderStage4(stage4Modules);
                        console.log('🎨 渲染内容长度:', renderedContent ? renderedContent.length : 'null');
                        targetElement.innerHTML = renderedContent;
                        console.log('✅ 阶段4模块内容已更新');
                    } else {
                        console.warn('⚠️ 阶段4详细元素未找到: stage4-details-inline');
                        console.log('🔍 尝试查找其他stage4元素:');
                        ['stage4-details', 'stage4', 'stage4-result'].forEach(id => {
                            const element = document.getElementById(id);
                            console.log(`  ${id}:`, !!element);
                        });
                    }
                } else {
                    console.warn('⚠️ StageRenderer或renderStage4方法不可用');
                }

                // 检查所有模块是否完成
                const allModules = Object.values(stage4Modules);
                const completedModules = allModules.filter(m => m.status === 'success' || m.status === 'error');
                const completedCount = allModules.filter(m => m.status === 'success').length;
                const totalCount = allModules.length;

                // 更新阶段4状态
                const stageElement = window.DOMManager?.get('stage4');
                if (stageElement) {
                    if (completedModules.length === totalCount) {
                        // 所有模块都完成了
                        stageElement.className = 'stage completed';
                        console.log('✅ 阶段4所有模块已完成');

                        // 自动显示内联模块详情
                        setTimeout(() => {
                            if (window.displayModulesInline && typeof window.displayModulesInline === 'function') {
                                console.log('[详情] 自动显示内联模块详情');
                                window.displayModulesInline();
                            }
                        }, 500);
                    } else {
                        stageElement.className = 'stage running';
                    }
                }

                // 更新结果显示
                const resultElement = window.DOMManager?.get('stage4-result');
                if (resultElement) {
                    if (completedModules.length === totalCount) {
                        resultElement.textContent = `搜索完成 (${completedCount}/${totalCount} 成功)`;
                    } else {
                        resultElement.textContent = `进行中 (${completedCount}/${totalCount})`;
                    }
                }

                // 更新时间
                const timeElement = window.DOMManager?.get('stage4-time');
                if (timeElement && completedModules.length === totalCount) {
                    const totalTime = allModules.reduce((sum, m) => sum + (m.processing_time_ms || 0), 0);
                    timeElement.textContent = `耗时: ${Math.round(totalTime)}ms`;
                }
            }

        } catch (error) {
            console.error('❌ 更新阶段4模块失败:', error);
        }
    }

    /**
     * 清理资源
     */
    destroy() {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        console.log('🧹 SearchController已清理');
    }
}

// 创建并导出单例
if (!window.SearchController) {
    window.SearchController = new SearchController();
}