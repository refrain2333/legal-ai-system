// 法智导航 - 增强版 JavaScript

class LegalNavigator {
    constructor() {
        this.searchButton = document.getElementById('searchButton');
        this.searchInput = document.getElementById('searchInput');
        this.statusDiv = document.getElementById('status');
        this.loadingDiv = document.getElementById('loading');
        this.resultsDiv = document.getElementById('results');
        
        // 启动状态相关元素
        this.systemStatusBar = document.getElementById('systemStatusBar');
        this.statusIcon = document.getElementById('statusIcon');
        this.statusText = document.getElementById('statusText');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.toggleDetails = document.getElementById('toggleDetails');
        this.loadingDetails = document.getElementById('loadingDetails');
        this.stepsList = document.getElementById('stepsList');
        this.reloadSystem = document.getElementById('reloadSystem');
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
        
        // API基础URL配置
        this.API_BASE_URL = window.location.protocol === 'file:' 
            ? 'http://127.0.0.1:5006'  // 直接打开文件时，修正端口为5006
            : '';  // 通过Web服务器访问时
        
        this.init();
    }
    
    apiUrl(path) {
        return this.API_BASE_URL + path;
    }
    
    init() {
        // 绑定搜索事件
        this.searchButton.addEventListener('click', () => this.performSearch());
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.performSearch();
        });
        
        // 绑定启动状态相关事件
        this.toggleDetails.addEventListener('click', () => this.toggleLoadingDetails());
        this.reloadSystem.addEventListener('click', () => this.reloadSystemAction());
        
        // 开始监控系统状态
        this.startStatusMonitoring();
    }
    
    startStatusMonitoring() {
        // 立即检查一次状态
        this.updateSystemStatus();
        
        // 设置定时更新
        this.statusUpdateInterval = setInterval(() => {
            this.updateSystemStatus();
        }, 1000); // 每秒更新一次
    }
    
    async updateSystemStatus() {
        try {
            const response = await fetch(this.apiUrl('/api/startup/status'));
            const data = await response.json();
            
            if (data.success) {
                this.updateStatusBar(data.system_status);
                this.updateDetailedStatus(data);
                
                // 如果系统准备就绪，停止频繁更新
                if (data.system_status.is_ready && !data.system_status.is_loading) {
                    this.setSystemReady();
                    if (this.statusUpdateInterval) {
                        clearInterval(this.statusUpdateInterval);
                        // 改为每30秒检查一次（保持连接）
                        this.statusUpdateInterval = setInterval(() => {
                            this.updateSystemStatus();
                        }, 30000);
                    }
                }
            }
        } catch (error) {
            console.error('Failed to update system status:', error);
            this.setSystemError('连接错误');
        }
    }
    
    updateStatusBar(systemStatus) {
        const { is_loading, overall_progress, current_step, is_ready } = systemStatus;
        
        // 更新状态图标和文本
        if (is_ready) {
            this.statusIcon.textContent = '✅';
            this.statusIcon.classList.add('ready');
            this.statusText.textContent = '系统准备就绪';
            this.systemStatusBar.className = 'system-status-bar ready';
        } else if (is_loading) {
            this.statusIcon.textContent = '🔄';
            this.statusIcon.classList.remove('ready');
            this.statusText.textContent = current_step ? 
                this.getStepDisplayName(current_step) : '系统启动中...';
            this.systemStatusBar.className = 'system-status-bar';
        } else {
            this.statusIcon.textContent = '❌';
            this.statusIcon.classList.remove('ready');
            this.statusText.textContent = '系统初始化失败';
            this.systemStatusBar.className = 'system-status-bar error';
        }
        
        // 更新进度条
        this.progressFill.style.width = `${overall_progress}%`;
        this.progressText.textContent = `${Math.round(overall_progress)}%`;
    }
    
    updateDetailedStatus(data) {
        const { system_status, steps, summary } = data;
        
        // 更新摘要信息
        this.overallProgress.textContent = `${Math.round(system_status.overall_progress)}%`;
        this.currentStep.textContent = system_status.current_step ? 
            this.getStepDisplayName(system_status.current_step) : '-';
        this.totalDuration.textContent = system_status.total_duration ? 
            `${system_status.total_duration.toFixed(1)}s` : '-';
        
        // 显示文档统计（如果有数据）
        if (summary && summary.documents_loaded && summary.documents_loaded.total > 0) {
            this.documentsLoaded.textContent = summary.documents_loaded.breakdown;
            this.documentsStatItem.style.display = 'flex';
        } else {
            this.documentsStatItem.style.display = 'none';
        }
        
        // 更新步骤列表
        this.updateStepsList(steps);
    }
    
    updateStepsList(steps) {
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
    
    getStatusIcon(status) {
        const icons = {
            'pending': '⏳',
            'loading': '🔄',
            'success': '✅',
            'error': '❌',
            'skipped': '⏭️'
        };
        return icons[status] || '❓';
    }
    
    setSystemReady() {
        this.isSystemReady = true;
        this.searchButton.disabled = false;
        this.searchInput.placeholder = '输入法律问题或关键词...';
    }
    
    setSystemError(message) {
        this.isSystemReady = false;
        this.searchButton.disabled = true;
        this.searchInput.placeholder = '系统初始化失败，请刷新页面重试';
        this.statusText.textContent = message;
        this.systemStatusBar.className = 'system-status-bar error';
    }
    
    toggleLoadingDetails() {
        this.loadingDetails.classList.toggle('hidden');
        this.toggleDetails.textContent = 
            this.loadingDetails.classList.contains('hidden') ? '详情' : '收起';
    }
    
    async reloadSystemAction() {
        try {
            this.reloadSystem.disabled = true;
            this.reloadSystem.textContent = '重新加载中...';
            
            const response = await fetch(this.apiUrl('/api/startup/reload'), {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // 重新开始监控
                this.isSystemReady = false;
                this.searchButton.disabled = true;
                this.startStatusMonitoring();
                this.showStatus('系统重新加载已启动', 'success');
            } else {
                this.showStatus('重新加载失败', 'error');
            }
        } catch (error) {
            console.error('Reload failed:', error);
            this.showStatus('重新加载请求失败', 'error');
        } finally {
            this.reloadSystem.disabled = false;
            this.reloadSystem.textContent = '重新加载';
        }
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
            console.error('Search error:', error);
            this.showStatus('搜索请求失败: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    displayMixedResults(results, query) {
        this.resultsDiv.innerHTML = '';
        
        if (results.length === 0) {
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
            articles.forEach(article => {
                const articleElement = this.createResultElement(article);
                articlesContent.appendChild(articleElement);
            });
            
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
            cases.forEach(caseResult => {
                const caseElement = this.createResultElement(caseResult);
                casesContent.appendChild(caseElement);
            });
            
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
                data.cases.forEach(caseResult => {
                    const caseElement = this.createResultElement(caseResult);
                    casesContent.appendChild(caseElement);
                });
                
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
            console.error('Load more cases error:', error);
            this.showStatus('加载更多案例失败: ' + error.message, 'error');
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
        this.resultsDiv.innerHTML = '';
        
        if (results.length === 0) {
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
            return;
        }
        
        results.forEach(result => {
            const resultElement = this.createResultElement(result);
            this.resultsDiv.appendChild(resultElement);
        });
    }
    
    createResultElement(result) {
        const div = document.createElement('div');
        div.className = 'result-item';
        
        let detailsHtml = '';
        
        if (result.type === 'case') {
            detailsHtml = this.createCaseDetails(result);
        } else if (result.type === 'article') {
            detailsHtml = this.createArticleDetails(result);
        }
        
        const similarityPercent = Math.round(result.similarity * 100);
        
        // 清理标题中的特殊字符
        let cleanTitle = result.title;
        if (cleanTitle) {
            // 移除标题开头的冒号
            cleanTitle = cleanTitle.replace(/^[：:]+/, '').trim();
            
            // 统一处理案例标题中的罪名格式
            if (result.type === 'case') {
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
                if (result.type === 'case') {
                    cleanTitle = `案例 ${result.case_id || '未知'}`;
                } else {
                    cleanTitle = `法条 第${result.article_number || '?'}条`;
                }
            }
        }
        
        // 处理内容显示 - 支持展开/收起
        let contentDisplay = '';
        if (result.content === '内容加载失败' || !result.content || result.content.length === 0) {
            contentDisplay = '<div class="result-content error-content">⚠️ 内容加载失败，请稍后重试</div>';
        } else {
            contentDisplay = this.createExpandableContent(result.content);
        }
        
        div.innerHTML = `
            <div class="result-title">${cleanTitle}</div>
            ${contentDisplay}
            ${detailsHtml}
            <div class="result-meta">
                <span>类型: ${result.type === 'case' ? '案例' : '法条'}</span>
                <span>相似度: ${similarityPercent}%</span>
                <span>内容长度: ${result.content ? result.content.length : 0} 字符</span>
            </div>
        `;
        
        // 绑定展开/收起事件
        this.bindToggleEvents(div);
        
        return div;
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
                <button class="toggle-content-btn" data-target="${uniqueId}">
                    <span class="expand-text">查看全文</span>
                    <span class="collapse-text hidden">收起</span>
                </button>
            </div>
        `;
    }
    
    bindToggleEvents(resultElement) {
        const toggleBtns = resultElement.querySelectorAll('.toggle-content-btn');
        
        toggleBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = btn.getAttribute('data-target');
                const previewElement = resultElement.querySelector(`#preview_${targetId}`);
                const fullElement = resultElement.querySelector(`#full_${targetId}`);
                const expandText = btn.querySelector('.expand-text');
                const collapseText = btn.querySelector('.collapse-text');
                
                if (previewElement && fullElement) {
                    const isExpanded = fullElement.classList.contains('hidden');
                    
                    if (isExpanded) {
                        // 展开
                        previewElement.classList.add('hidden');
                        fullElement.classList.remove('hidden');
                        expandText.classList.add('hidden');
                        collapseText.classList.remove('hidden');
                    } else {
                        // 收起
                        previewElement.classList.remove('hidden');
                        fullElement.classList.add('hidden');
                        expandText.classList.remove('hidden');
                        collapseText.classList.add('hidden');
                    }
                }
            });
        });
    }
    
    createCaseDetails(result) {
        let html = '<div class="case-details">';
        
        if (result.case_id) {
            html += `<div class="detail-item"><strong>案例编号:</strong> ${result.case_id}</div>`;
        }
        
        if (result.criminals && result.criminals.length > 0) {
            // 清理被告人名称中的特殊字符
            const cleanedCriminals = result.criminals.map(name => {
                // 移除前后的冒号、括号等特殊字符
                return name.replace(/^[：:【\[（\(]+|[：:】\]）\)]+$/g, '').trim();
            }).filter(name => name.length > 0);
            
            if (cleanedCriminals.length > 0) {
                html += `<div class="detail-item"><strong>被告人:</strong> ${cleanedCriminals.join('、')}</div>`;
            }
        }
        
        if (result.accusations && result.accusations.length > 0) {
            // 清理罪名中的特殊字符，与标题格式保持一致
            const cleanedAccusations = result.accusations.map(acc => {
                // 移除各种括号
                let cleaned = acc.replace(/[【\[\]】]/g, '').trim();
                // 移除开头和结尾的特殊字符
                cleaned = cleaned.replace(/^[：:、,，]+|[：:、,，]+$/g, '');
                // 移除多余的标点符号
                cleaned = cleaned.replace(/[,，]\s*/g, '、');
                return cleaned;
            }).filter(acc => acc.length > 0);
            
            if (cleanedAccusations.length > 0) {
                // 去重并用顿号连接
                const uniqueAccusations = [...new Set(cleanedAccusations)];
                html += `<div class="detail-item"><strong>罪名:</strong> ${uniqueAccusations.join('、')}</div>`;
            }
        }
        
        if (result.relevant_articles && result.relevant_articles.length > 0) {
            html += `<div class="detail-item"><strong>相关法条:</strong> 第${result.relevant_articles.join('条、第')}条</div>`;
        }
        
        // 刑罚信息
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
        
        if (result.article_number) {
            html += `<div class="detail-item"><strong>法条编号:</strong> 第${result.article_number}条</div>`;
        }
        
        if (result.chapter) {
            html += `<div class="detail-item"><strong>所属章节:</strong> ${result.chapter}</div>`;
        }
        
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
    new LegalNavigator();
});