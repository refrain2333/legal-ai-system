// 法智导航 - 增强版 JavaScript

class LegalNavigator {
    constructor() {
        this.searchButton = document.getElementById('searchButton');
        this.searchInput = document.getElementById('searchInput');
        this.statusDiv = document.getElementById('status');
        this.loadingDiv = document.getElementById('loading');
        this.resultsDiv = document.getElementById('results');
        
        // 启动状态相关元素 - 仅保留详情面板相关
        this.loadingDetails = document.getElementById('loadingDetails');
        this.stepsList = document.getElementById('stepsList');
        this.overallProgress = document.getElementById('overallProgress');
        this.currentStep = document.getElementById('currentStep');
        this.totalDuration = document.getElementById('totalDuration');
        this.documentsLoaded = document.getElementById('documentsLoaded');
        this.documentsStatItem = document.getElementById('documentsStatItem');
        
        this.isSystemReady = false;
        this.statusUpdateInterval = null;
        
        // 分页加载状态
        this.currentQuery = '';
        this.casesOffset = 0;
        this.hasMoreCases = false;
        this.isLoadingMoreCases = false;
        
        // WebSocket支持
        this.websocket = null;
        this.searchInProgress = false;
        this.searchStartTime = null;
        
        // 使用通用API配置
        this.API_BASE_URL = '';
        
        this.init();
    }
    
    apiUrl(path) {
        return window.apiConfig.getApiUrl(path);
    }
    
    init() {
        // 绑定搜索事件
        this.searchButton.addEventListener('click', () => this.performSearch());
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.performSearch();
        });

        // 初始化WebSocket连接
        this.initWebSocket();

        // 简化的系统状态检查 - 不显示详细面板
        this.checkSystemReady();
    }
    
    // 简化的系统准备状态检查
    async checkSystemReady() {
        try {
            const response = await fetch(this.apiUrl('/api/startup/status'));
            const data = await response.json();

            if (data.success && data.system_status.is_ready) {
                this.setSystemReady();
            } else {
                // 如果系统未就绪，延迟重试
                setTimeout(() => this.checkSystemReady(), 2000);
            }
        } catch (error) {
            console.error('系统状态检查失败:', error);
            // 默认允许搜索，避免阻塞用户
            this.setSystemReady();
        }
    }
    
    // 新增：WebSocket初始化
    initWebSocket() {
        try {
            // 使用通用API配置创建WebSocket
            const wsUrl = window.apiConfig.getWsUrl('/api/debug/realtime');
            console.log('尝试连接WebSocket:', wsUrl);
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('WebSocket连接已建立');
            };

            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.websocket.onclose = () => {
                console.log('WebSocket连接已断开');
                // 5秒后尝试重连
                setTimeout(() => {
                    if (this.websocket.readyState === WebSocket.CLOSED) {
                        console.log('尝试重新连接WebSocket...');
                        this.initWebSocket();
                    }
                }, 5000);
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket错误:', error);
            };
        } catch (error) {
            this.handleError(error, 'WebSocket初始化失败', 'WebSocket初始化');
        }
    }
    
    // 新增：处理WebSocket消息
    handleWebSocketMessage(data) {
        console.log('收到WebSocket消息:', data);
        
        // 处理阶段完成消息
        if (data.type === 'stage_completed') {
            const stageNum = data.stage_number;
            const stageName = data.stage_name;
            const processingTime = data.processing_time_ms;
            
            console.log(`阶段${stageNum}完成: ${stageName}, 耗时: ${processingTime}ms`);
            this.updateStageProgress(stageNum, stageName, processingTime, true);
        }
        
        // 处理模块完成消息
        if (data.type === 'module_completed') {
            const moduleName = data.module_name;
            const status = data.status;
            const processingTime = data.processing_time_ms;
            const resultsCount = data.results_count || 0;
            
            console.log(`模块${moduleName}完成: ${status}, 耗时: ${processingTime}ms, 结果: ${resultsCount}条`);
            this.updateModuleProgress(moduleName, status, processingTime, resultsCount);
        }
        
        // 处理搜索完成消息
        if (data.type === 'search_completed') {
            console.log('搜索全部完成:', data);
            this.onSearchCompleted(data);
        }
    }
    
    // 新增：更新阶段进度的方法
    updateStageProgress(stageNum, stageName, processingTime, completed) {
        // 在加载显示中动态更新阶段进度
        if (this.loadingDiv && this.loadingDiv.style.display !== 'none') {
            // 创建或更新阶段进度显示
            let stageProgress = document.getElementById('stage-progress');
            if (!stageProgress) {
                stageProgress = document.createElement('div');
                stageProgress.id = 'stage-progress';
                stageProgress.innerHTML = `
                    <h4>🚀 AI搜索进度 - 5阶段流程</h4>
                    <div id="stages-list"></div>
                `;
                this.loadingDiv.appendChild(stageProgress);
            }
            
            let stagesList = document.getElementById('stages-list');
            let stageElement = document.getElementById(`stage-${stageNum}`);
            
            if (!stageElement) {
                stageElement = document.createElement('div');
                stageElement.id = `stage-${stageNum}`;
                stageElement.className = 'stage-item';
                stageElement.innerHTML = `
                    <div class="stage-header">
                        <span class="stage-icon">加载中</span>
                        <span class="stage-name">阶段${stageNum}: ${stageName}</span>
                        <span class="stage-time">计算中...</span>
                    </div>
                `;
                stagesList.appendChild(stageElement);
            }
            
            if (completed) {
                stageElement.querySelector('.stage-icon').textContent = '完成';
                stageElement.querySelector('.stage-time').textContent = `⏱️ ${processingTime}ms`;
                stageElement.className = 'stage-item completed';
            }
        }
    }
    
    // 新增：更新模块进度的方法
    updateModuleProgress(moduleName, status, processingTime, resultsCount) {
        // 在阶段4的区域内显示模块进度
        let stage4Element = document.getElementById('stage-4');
        if (stage4Element) {
            let modulesContainer = stage4Element.querySelector('.modules-container');
            if (!modulesContainer) {
                modulesContainer = document.createElement('div');
                modulesContainer.className = 'modules-container';
                modulesContainer.innerHTML = '<h5>多路搜索模块：</h5>';
                stage4Element.appendChild(modulesContainer);
            }
            
            let moduleElement = document.getElementById(`module-${moduleName}`);
            if (!moduleElement) {
                moduleElement = document.createElement('div');
                moduleElement.id = `module-${moduleName}`;
                moduleElement.className = 'module-item';
                moduleElement.innerHTML = `
                    <span class="module-icon">加载中</span>
                    <span class="module-name">${moduleName}</span>
                    <span class="module-status">运行中...</span>
                `;
                modulesContainer.appendChild(moduleElement);
            }
            
            // 更新模块状态
            const icon = status === 'success' ? '成功' : (status === 'error' ? '失败' : '运行中');
            const statusText = status === 'success' ? `完成 (${resultsCount}条) - ${processingTime}ms` :
                              status === 'error' ? `失败 - ${processingTime}ms` : '运行中...';
            
            moduleElement.querySelector('.module-icon').textContent = icon;
            moduleElement.querySelector('.module-status').textContent = statusText;
            moduleElement.className = `module-item ${status}`;
        }
    }
    
    // 新增：搜索完成处理
    onSearchCompleted(data) {
        this.searchInProgress = false;
        
        // 计算总用时
        if (this.searchStartTime) {
            const totalTime = Date.now() - this.searchStartTime;
            console.log(`🏁 搜索完成，总耗时: ${totalTime}ms`);
        }
        
        // 隐藏加载显示
        this.showLoading(false);
        
        // 显示结果（如果有的话）
        if (data.results && data.results.length > 0) {
            this.displayMixedResults(data.results, this.currentQuery);
            this.showStatus(`找到 ${data.results.length} 条相关结果`, 'success');
        }
    }
    
    setSystemReady() {
        this.isSystemReady = true;
        this.searchButton.disabled = false;
        this.searchInput.placeholder = '输入法律问题或关键词...';
    }

    // 为导航栏设置按钮提供的状态更新方法
    async updateSystemStatusDisplay() {
        if (!this.loadingDetails || this.loadingDetails.style.display === 'none') {
            return; // 如果详情面板隐藏，不需要更新
        }

        try {
            const response = await fetch(this.apiUrl('/api/startup/status'));
            const data = await response.json();

            if (data.success) {
                // 只更新详细面板
                this.updateDetailedStatusDisplay(data);
            }
        } catch (error) {
            console.error('系统状态更新失败:', error);
        }
    }

    updateDetailedStatusDisplay(data) {
        const { system_status, summary, steps } = data;

        if (this.overallProgress && this.currentStep && this.totalDuration) {
            // 更新摘要信息
            this.overallProgress.textContent = `${Math.round(system_status.overall_progress)}%`;
            this.currentStep.textContent = system_status.current_step ?
                this.getStepDisplayName(system_status.current_step) : '就绪';
            this.totalDuration.textContent = system_status.total_duration ?
                `${system_status.total_duration.toFixed(1)}s` : '-';

            // 显示文档统计（如果有数据）
            if (summary && summary.documents_loaded && summary.documents_loaded.total > 0) {
                this.documentsLoaded.textContent = summary.documents_loaded.breakdown;
                this.documentsStatItem.style.display = 'flex';
            } else {
                this.documentsStatItem.style.display = 'none';
            }
        }

        // 更新步骤列表
        if (steps && Array.isArray(steps)) {
            this.updateStepsList(steps);
        } else {
            // 如果没有步骤数据，生成默认的系统信息
            this.generateDefaultSystemInfo(system_status);
        }
    }

    updateStepsList(steps) {
        if (!this.stepsList) return;

        this.stepsList.innerHTML = '';

        steps.forEach(step => {
            const stepItem = document.createElement('div');
            stepItem.className = `step-item ${step.status}`;

            const statusIcon = this.getStatusIcon(step.status);
            const progressText = step.status === 'loading' ?
                `${Math.round(step.progress)}%` :
                (step.duration ? `${step.duration.toFixed(1)}s` : '');

            stepItem.innerHTML = `
                <div class="step-status-icon">${statusIcon}</div>
                <div class="step-content">
                    <div class="step-name">${step.name}</div>
                    <div class="step-description">${step.description}</div>
                </div>
                <div class="step-progress">${progressText}</div>
            `;

            // 如果有错误信息，显示
            if (step.error_message) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'step-error';
                errorDiv.style.cssText = 'color: #f44336; font-size: 12px; margin-top: 4px;';
                errorDiv.textContent = step.error_message;
                stepItem.querySelector('.step-content').appendChild(errorDiv);
            }

            this.stepsList.appendChild(stepItem);
        });
    }

    generateDefaultSystemInfo(systemStatus) {
        if (!this.stepsList) return;

        const defaultSteps = [
            {
                name: '配置检查',
                description: '检查系统配置和环境变量',
                status: 'success',
                duration: 0.1
            },
            {
                name: '兼容性初始化',
                description: '初始化系统兼容性设置',
                status: 'success',
                duration: 0.2
            },
            {
                name: '向量数据加载',
                description: '加载法条和案例向量数据',
                status: 'success',
                duration: 2.5
            },
            {
                name: 'AI模型加载',
                description: '加载Lawformer语义分析模型',
                status: 'success',
                duration: 3.8
            },
            {
                name: '搜索引擎初始化',
                description: '初始化多路搜索引擎和知识图谱',
                status: 'success',
                duration: 1.2
            },
            {
                name: '系统健康检查',
                description: '验证所有模块正常运行',
                status: systemStatus.is_ready ? 'success' : 'loading',
                duration: systemStatus.is_ready ? 0.3 : null
            }
        ];

        this.updateStepsList(defaultSteps);
    }

    getStatusIcon(status) {
        const icons = {
            'pending': '<i class="fas fa-clock text-warning"></i>',
            'loading': '<i class="fas fa-spinner fa-spin text-primary"></i>',
            'success': '<i class="fas fa-check-circle text-success"></i>',
            'error': '<i class="fas fa-times-circle text-danger"></i>',
            'skipped': '<i class="fas fa-forward text-muted"></i>'
        };
        return icons[status] || '<i class="fas fa-question-circle text-muted"></i>';
    }

    getStepDisplayName(stepId) {
        const stepNames = {
            'config_check': '配置检查',
            'compatibility_init': '兼容性初始化',
            'vectors_loading': '向量数据加载',
            'model_loading': 'AI模型加载',
            'search_engine_init': '搜索引擎初始化',
            'health_check': '系统健康检查'
        };
        return stepNames[stepId] || stepId;
    }

    async performSearch() {
        if (!this.isSystemReady) {
            this.showStatus('系统尚未准备就绪，请等待加载完成', 'error');
            return;
        }
        
        const query = this.searchInput.value.trim();
        if (!query) {
            this.showStatus('请输入搜索内容', 'error');
            return;
        }
        
        // 重置分页状态
        this.currentQuery = query;
        this.casesOffset = 5; // 从第6条案例开始分页
        this.hasMoreCases = false;
        
        this.showLoading(true);
        this.clearResults();
        
        try {
            const response = await fetch(this.apiUrl('/api/search'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query
                })
            });
            
            if (response.status === 503) {
                // 服务不可用
                const errorData = await response.json();
                this.showStatus('系统正在加载中，请稍后再试', 'error');
                return;
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.displayMixedResults(data.results, query);
                this.showStatus(`找到 ${data.total} 条相关结果（5条法条 + 5条案例）`, 'success');
            } else {
                this.showStatus('搜索失败: ' + (data.detail || '未知错误'), 'error');
            }
        } catch (error) {
            this.handleError(error, '搜索请求失败', 'Search');
        } finally {
            this.showLoading(false);
        }
    }
    
    // 显示无结果的通用方法
    showNoResults(query) {
        this.resultsDiv.innerHTML = `
            <div class="no-results">
                <p>未找到与 "${query}" 相关的结果</p>
                <p>建议：</p>
                <ul>
                    <li>尝试使用不同的关键词</li>
                    <li>使用更通用的法律术语</li>
                    <li>检查拼写是否正确</li>
                </ul>
            </div>
        `;
    }

    // 清空结果容器的通用方法
    clearResults() {
        this.resultsDiv.innerHTML = '';
    }

    // 批量添加结果元素的通用方法
    appendResults(container, results) {
        const fragment = document.createDocumentFragment();
        results.forEach(result => {
            const element = this.createResultElement(result);
            fragment.appendChild(element);
        });
        container.appendChild(fragment);
    }

    // 通用错误处理方法
    handleError(error, userMessage, context = '') {
        console.error(`${context} error:`, error);
        this.showStatus(userMessage + (error.message ? ': ' + error.message : ''), 'error');
    }

    // 通用按钮状态管理方法
    setButtonState(button, isLoading, loadingText, normalText) {
        button.disabled = isLoading;
        button.textContent = isLoading ? loadingText : normalText;
    }

    // 通用文本清理方法
    cleanTitle(title, type = '', fallbackId = '') {
        if (!title) return title;

        // 移除标题开头的冒号
        let cleanTitle = title.replace(/^[：:]+/, '').trim();

        // 案例专用清理
        if (type === 'case') {
            // 提取被告人姓名和罪名 - 支持多种格式
            const caseMatch = cleanTitle.match(/^(.+?)([【\[].*?[】\]].*?)案/);
            if (caseMatch) {
                const defendant = caseMatch[1].trim();
                let crimes = caseMatch[2];

                // 清理罪名格式：移除多余的括号，统一使用顿号分隔
                crimes = crimes.replace(/[【\[\]】]/g, ''); // 移除所有方括号
                crimes = crimes.replace(/[,，]\s*/g, '、'); // 逗号改为顿号
                crimes = crimes.replace(/、+/g, '、'); // 合并多个顿号
                crimes = crimes.replace(/^、|、$/g, ''); // 移除开头结尾的顿号
                crimes = crimes.trim();

                cleanTitle = `${defendant}${crimes}案`;
            } else {
                // 如果没有匹配到标准格式，尝试清理现有标题
                cleanTitle = cleanTitle.replace(/\]+([^【\[\]]*)/g, '$1'); // 移除孤立的右括号
                cleanTitle = cleanTitle.replace(/[,，]\s*/g, '、'); // 统一分隔符
            }
        }

        // 移除重复的括号和标点
        cleanTitle = cleanTitle.replace(/\[+/g, '[').replace(/\]+/g, ']');
        cleanTitle = cleanTitle.replace(/【+/g, '【').replace(/】+/g, '】');

        // 如果标题为空或太短，使用默认标题
        if (!cleanTitle || cleanTitle.length < 2) {
            if (type === 'case') {
                cleanTitle = `案例 ${fallbackId || '未知'}`;
            } else if (type === 'article') {
                cleanTitle = `法条 第${fallbackId || '?'}条`;
            }
        }

        return cleanTitle;
    }

    displayMixedResults(results, query) {
        this.clearResults();

        if (results.length === 0) {
            this.showNoResults(query);
            return;
        }
        
        // 分离法条和案例
        const articles = results.filter(result => result.type === 'article');
        const cases = results.filter(result => result.type === 'case');
        
        // 设置分页状态
        this.hasMoreCases = cases.length >= 5; // 如果有5条案例，可能有更多
        
        // 创建结果容器
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'mixed-results-container';
        
        // 添加法条部分
        if (articles.length > 0) {
            const articlesSection = document.createElement('div');
            articlesSection.className = 'results-section';
            articlesSection.innerHTML = `
                <div class="section-header">
                    <h3>相关法律条文 (${articles.length})</h3>
                </div>
                <div class="section-content" id="articlesContent"></div>
            `;
            
            const articlesContent = articlesSection.querySelector('#articlesContent');
            this.appendResults(articlesContent, articles);
            
            resultsContainer.appendChild(articlesSection);
        }
        
        // 添加案例部分
        if (cases.length > 0) {
            const casesSection = document.createElement('div');
            casesSection.className = 'results-section';
            casesSection.innerHTML = `
                <div class="section-header">
                    <h3>相关案例 (${cases.length}${this.hasMoreCases ? '+' : ''})</h3>
                </div>
                <div class="section-content" id="casesContent"></div>
            `;
            
            const casesContent = casesSection.querySelector('#casesContent');
            this.appendResults(casesContent, cases);
            
            // 添加"加载更多案例"按钮
            if (this.hasMoreCases) {
                const loadMoreBtn = document.createElement('button');
                loadMoreBtn.className = 'load-more-btn';
                loadMoreBtn.innerHTML = `
                    <span class="load-more-text">加载更多案例</span>
                    <span class="load-more-loading hidden">正在加载...</span>
                `;
                loadMoreBtn.addEventListener('click', () => this.loadMoreCases());
                casesContent.appendChild(loadMoreBtn);
            }
            
            resultsContainer.appendChild(casesSection);
        }
        
        this.resultsDiv.appendChild(resultsContainer);
    }
    
    async loadMoreCases() {
        if (this.isLoadingMoreCases || !this.hasMoreCases) {
            return;
        }
        
        this.isLoadingMoreCases = true;
        
        // 更新按钮状态
        const loadMoreBtn = document.querySelector('.load-more-btn');
        const loadMoreText = loadMoreBtn.querySelector('.load-more-text');
        const loadMoreLoading = loadMoreBtn.querySelector('.load-more-loading');
        
        loadMoreBtn.disabled = true;
        loadMoreText.classList.add('hidden');
        loadMoreLoading.classList.remove('hidden');
        
        try {
            const response = await fetch(this.apiUrl(`/api/search/cases/more?query=${encodeURIComponent(this.currentQuery)}&offset=${this.casesOffset}&limit=5`));
            const data = await response.json();
            
            if (data.success && data.cases.length > 0) {
                // 获取案例内容容器
                const casesContent = document.getElementById('casesContent');
                
                // 移除"加载更多"按钮
                loadMoreBtn.remove();
                
                // 添加新的案例
                this.appendResults(casesContent, data.cases);
                
                // 更新状态
                this.casesOffset += data.returned_count;
                this.hasMoreCases = data.has_more;
                
                // 如果还有更多案例，重新添加按钮
                if (this.hasMoreCases) {
                    const newLoadMoreBtn = document.createElement('button');
                    newLoadMoreBtn.className = 'load-more-btn';
                    newLoadMoreBtn.innerHTML = `
                        <span class="load-more-text">加载更多案例</span>
                        <span class="load-more-loading hidden">正在加载...</span>
                    `;
                    newLoadMoreBtn.addEventListener('click', () => this.loadMoreCases());
                    casesContent.appendChild(newLoadMoreBtn);
                }
                
                // 更新案例数量显示
                const casesHeader = document.querySelector('.results-section:last-child .section-header h3');
                const currentCasesCount = document.querySelectorAll('#casesContent .result-item').length;
                casesHeader.textContent = `相关案例 (${currentCasesCount}${this.hasMoreCases ? '+' : ''})`;
                
                this.showStatus(`加载了 ${data.returned_count} 条新案例`, 'success');
            } else {
                this.hasMoreCases = false;
                loadMoreBtn.remove();
                this.showStatus('没有更多案例了', 'info');
            }
        } catch (error) {
            this.handleError(error, '加载更多案例失败', 'Load more cases');
        } finally {
            this.isLoadingMoreCases = false;
            
            // 恢复按钮状态（如果还存在）
            if (document.querySelector('.load-more-btn')) {
                loadMoreBtn.disabled = false;
                loadMoreText.classList.remove('hidden');
                loadMoreLoading.classList.add('hidden');
            }
        }
    }
    
    displayResults(results, query) {
        this.clearResults();

        if (results.length === 0) {
            this.showNoResults(query);
            return;
        }
        
        this.appendResults(this.resultsDiv, results);
    }
    
    createResultElement(result) {
        const div = document.createElement('div');
        div.className = 'result-item';

        const similarityPercent = Math.round(result.similarity * 100);

        // 清理标题中的特殊字符
        const fallbackId = result.type === 'case' ? result.case_id : result.article_number;
        let cleanTitle = this.cleanTitle(result.title, result.type, fallbackId);

        // 生成法律标签
        const legalTags = this.createLegalTags(result);

        // 处理内容显示 - 支持展开/收起
        let contentDisplay = '';
        if (result.content === '内容加载失败' || !result.content || result.content.length === 0) {
            contentDisplay = '<div class="result-content error-content">内容加载失败，请稍后重试</div>';
        } else {
            contentDisplay = this.createExpandableContent(result.content);
        }

        // 处理详细信息
        let detailsHtml = '';
        if (result.type === 'case') {
            detailsHtml = this.createCaseDetails(result);
        } else if (result.type === 'article') {
            detailsHtml = this.createArticleDetails(result);
        }

        div.innerHTML = `
            <div class="result-header">
                <div class="result-title-section">
                    <h3 class="result-title">${cleanTitle}</h3>
                    <div class="legal-tags-container">
                        ${legalTags}
                    </div>
                </div>
                <div class="similarity-score">
                    <div class="score-value">${similarityPercent}%</div>
                    <div class="score-label">相似度</div>
                </div>
            </div>
            ${contentDisplay}
            ${detailsHtml}
        `;

        // 绑定展开/收起事件
        this.bindToggleEvents(div);

        return div;
    }

    createLegalTags(result) {
        const tags = [];

        // 文档类型标签
        const docType = result.type === 'case' ? '案例' : '法条';
        tags.push(`<span class="legal-tag document-type">${docType}</span>`);

        // 法条编号标签
        if (result.type === 'article' && result.article_number) {
            tags.push(`<span class="legal-tag article-number">第${result.article_number}条</span>`);
        }

        // 案例编号标签
        if (result.type === 'case' && result.case_id) {
            tags.push(`<span class="legal-tag case-id">${result.case_id}</span>`);
        }

        // 章节标签
        if (result.chapter) {
            tags.push(`<span class="legal-tag chapter">${result.chapter}</span>`);
        }

        // 罪名标签
        if (result.accusations && result.accusations.length > 0) {
            const mainAccusation = result.accusations[0];
            if (mainAccusation) {
                const cleanAccusation = mainAccusation.replace(/[【\[\]】]/g, '').trim();
                tags.push(`<span class="legal-tag accusation">${cleanAccusation}</span>`);
            }
        }

        // 相关法条标签
        if (result.relevant_articles && result.relevant_articles.length > 0) {
            const articlesText = result.relevant_articles.length > 3
                ? `第${result.relevant_articles.slice(0, 3).join('、')}条等`
                : `第${result.relevant_articles.join('、')}条`;
            tags.push(`<span class="legal-tag related-articles">${articlesText}</span>`);
        }

        return tags.join('');
    }
    
    createExpandableContent(content) {
        const previewLength = 200;
        const isLong = content.length > previewLength;

        if (!isLong) {
            return `<div class="result-content">${content}</div>`;
        }

        const preview = content.substring(0, previewLength);
        const uniqueId = 'content_' + Math.random().toString(36).substr(2, 9);

        return `
            <div class="result-content">
                <div class="content-preview" id="preview_${uniqueId}">
                    ${preview}...
                </div>
                <div class="content-full hidden" id="full_${uniqueId}">
                    ${content}
                </div>
                <button class="expand-toggle" data-target="${uniqueId}">
                    <i class="fas fa-chevron-down toggle-icon"></i>
                    <span class="expand-text">查看全文</span>
                    <span class="collapse-text hidden">收起</span>
                </button>
            </div>
        `;
    }
    
    bindToggleEvents(resultElement) {
        const toggleBtns = resultElement.querySelectorAll('.expand-toggle');
        console.log('Found toggle buttons:', toggleBtns.length);

        toggleBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Toggle button clicked');

                const targetId = btn.getAttribute('data-target');
                console.log('Target ID:', targetId);

                const previewElement = resultElement.querySelector(`#preview_${targetId}`);
                const fullElement = resultElement.querySelector(`#full_${targetId}`);
                const expandText = btn.querySelector('.expand-text');
                const collapseText = btn.querySelector('.collapse-text');
                const toggleIcon = btn.querySelector('.toggle-icon');

                console.log('Elements found:', {
                    preview: !!previewElement,
                    full: !!fullElement,
                    expandText: !!expandText,
                    collapseText: !!collapseText
                });

                if (previewElement && fullElement) {
                    const isExpanded = fullElement.classList.contains('hidden');
                    console.log('Current state - is hidden (should expand):', isExpanded);

                    if (isExpanded) {
                        // 展开
                        previewElement.classList.add('hidden');
                        fullElement.classList.remove('hidden');
                        if (expandText) expandText.classList.add('hidden');
                        if (collapseText) collapseText.classList.remove('hidden');
                        btn.classList.add('expanded');
                        if (toggleIcon) {
                            toggleIcon.classList.remove('fa-chevron-down');
                            toggleIcon.classList.add('fa-chevron-up');
                        }
                        console.log('Expanded content');
                    } else {
                        // 收起
                        previewElement.classList.remove('hidden');
                        fullElement.classList.add('hidden');
                        if (expandText) expandText.classList.remove('hidden');
                        if (collapseText) collapseText.classList.add('hidden');
                        btn.classList.remove('expanded');
                        if (toggleIcon) {
                            toggleIcon.classList.remove('fa-chevron-up');
                            toggleIcon.classList.add('fa-chevron-down');
                        }
                        console.log('Collapsed content');
                    }
                }
            });
        });
    }
    
    createCaseDetails(result) {
        let html = '<div class="case-details">';

        // 被告人信息 - 标签中没有这个信息，保留
        if (result.criminals && result.criminals.length > 0) {
            const cleanedCriminals = result.criminals.map(name => {
                return name.replace(/^[：:【\[（\(]+|[：:】\]）\)]+$/g, '').trim();
            }).filter(name => name.length > 0);

            if (cleanedCriminals.length > 0) {
                html += `<div class="detail-item"><strong>被告人:</strong> ${cleanedCriminals.join('、')}</div>`;
            }
        }

        // 刑罚信息 - 标签中没有这个信息，保留
        const penalties = [];
        if (result.death_penalty) penalties.push('<div class="detail-item penalty"><strong>死刑</strong></div>');
        if (result.life_imprisonment) penalties.push('<div class="detail-item penalty"><strong>无期徒刑</strong></div>');
        if (result.imprisonment_months) {
            const years = Math.floor(result.imprisonment_months / 12);
            const months = result.imprisonment_months % 12;
            let imprisonmentText = '';
            if (years > 0) imprisonmentText += `${years}年`;
            if (months > 0) imprisonmentText += `${months}个月`;
            penalties.push(`<div class="detail-item penalty"><strong>有期徒刑:</strong> ${imprisonmentText}</div>`);
        }
        if (result.punish_of_money) {
            penalties.push(`<div class="detail-item penalty"><strong>罚金:</strong> ${result.punish_of_money}万元</div>`);
        }

        if (penalties.length > 0) {
            html += `<div class="detail-item"><strong>刑罚:</strong><br>${penalties.join('')}</div>`;
        }

        html += '</div>';
        return html;
    }
    
    createArticleDetails(result) {
        let html = '<div class="article-details">';

        // 法条编号和章节信息已经在标签中显示，这里不再重复
        // 如果有其他需要显示的信息可以在这里添加

        html += '</div>';
        return html;
    }
    
    showLoading(show) {
        this.loadingDiv.style.display = show ? 'block' : 'none';
    }
    
    showStatus(message, type) {
        this.statusDiv.textContent = message;
        this.statusDiv.className = `status ${type}`;
        this.statusDiv.style.display = 'block';
        
        // 3秒后自动隐藏
        setTimeout(() => {
            this.statusDiv.style.display = 'none';
        }, 3000);
    }
    
    clearResults() {
        this.resultsDiv.innerHTML = '';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 创建实例并暴露到全局变量，供导航栏调用
    window.legalNavigator = new LegalNavigator();
});