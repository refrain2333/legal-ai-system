/**
 * 结果渲染器 - 统一处理搜索结果的显示逻辑
 */
class ResultRenderer {
    constructor() {
        this.isInitialized = false;
    }

    /**
     * 初始化结果渲染器
     */
    initialize() {
        if (this.isInitialized) return;

        this.setupEventListeners();
        this.isInitialized = true;

        console.log('✅ ResultRenderer初始化完成');
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

        // 监听搜索完成事件
        window.EventBus.on(window.AppEvents.SEARCH_COMPLETE, (data) => {
            if (data.results) {
                this.displayResults(data.results);
            }
        });
    }

    /**
     * 显示搜索结果
     */
    displayResults(results) {
        console.log('🎨 渲染搜索结果:', results.length, '条');

        if (!results || results.length === 0) {
            this.showNoResults();
            return;
        }

        // 分离法条和案例
        const articles = results.filter(result => result.type === 'article');
        const cases = results.filter(result => result.type === 'case');

        // 显示结果容器
        this.showResultsContainer();

        // 渲染法条结果
        if (articles.length > 0) {
            this.renderArticles(articles);
        }

        // 渲染案例结果
        if (cases.length > 0) {
            this.renderCases(cases);
        }
    }

    /**
     * 显示结果容器
     */
    showResultsContainer() {
        window.DOMManager.updateVisibility({
            'searchResults': true
        });
    }

    /**
     * 渲染法条结果
     */
    renderArticles(articles) {
        console.log('📖 渲染法条结果:', articles.length, '条');

        const container = window.DOMManager.get('articles-results-container');
        const section = window.DOMManager.get('articles-results-section');

        if (!container || !section) {
            console.error('❌ 法条结果容器未找到');
            return;
        }

        // 清空容器
        container.innerHTML = '';

        // 创建结果项
        articles.forEach(article => {
            const resultElement = this.createResultElement(article, 'article');
            if (resultElement) {
                container.appendChild(resultElement);
            }
        });

        // 显示法条区域
        section.style.display = 'block';
    }

    /**
     * 渲染案例结果
     */
    renderCases(cases) {
        console.log('📁 渲染案例结果:', cases.length, '条');

        const container = window.DOMManager.get('cases-results-container');
        const section = window.DOMManager.get('cases-results-section');

        if (!container || !section) {
            console.error('❌ 案例结果容器未找到');
            return;
        }

        // 清空容器
        container.innerHTML = '';

        // 创建结果项
        cases.forEach(case_item => {
            const resultElement = this.createResultElement(case_item, 'case');
            if (resultElement) {
                container.appendChild(resultElement);
            }
        });

        // 显示案例区域
        section.style.display = 'block';
    }

    /**
     * 创建结果元素
     */
    createResultElement(item, type) {
        const template = window.DOMManager.getTemplate('result-item-template');
        if (!template) {
            console.error('❌ 结果项模板未找到');
            return null;
        }

        const resultItem = template.content.cloneNode(true);

        // 获取模板元素
        const titleElement = resultItem.querySelector('.result-title');
        const similarityElement = resultItem.querySelector('.result-similarity');
        const textElement = resultItem.querySelector('.result-text');
        const sourceElement = resultItem.querySelector('.result-source');
        const itemElement = resultItem.querySelector('.result-item');

        // 填充数据
        if (titleElement) {
            titleElement.textContent = this.formatTitle(item, type);
        }

        if (similarityElement) {
            const similarity = ((item.similarity || 0) * 100).toFixed(1);
            similarityElement.textContent = `相似度: ${similarity}%`;
        }

        if (textElement) {
            textElement.textContent = this.formatContent(item.content);
        }

        if (sourceElement) {
            sourceElement.textContent = type === 'article' ? '法条' : '案例';
        }

        // 添加类型样式
        if (itemElement) {
            itemElement.classList.add(`result-type-${type}`);
            itemElement.classList.add('clickable-result');

            // 添加点击事件
            itemElement.addEventListener('click', () => {
                window.showItemDetail(item, type);
            });

            // 添加相似度等级样式
            const similarity = item.similarity || 0;
            if (similarity >= 0.8) {
                itemElement.classList.add('similarity-high');
            } else if (similarity >= 0.6) {
                itemElement.classList.add('similarity-medium');
            } else {
                itemElement.classList.add('similarity-low');
            }
        }

        return resultItem;
    }

    /**
     * 格式化标题
     */
    formatTitle(item, type) {
        if (type === 'article') {
            return item.title || `第${item.article_number || '?'}条`;
        } else if (type === 'case') {
            return item.title || item.case_id || `案例${item.id || '?'}`;
        }
        return item.title || '未知标题';
    }

    /**
     * 格式化内容
     */
    formatContent(content) {
        if (!content) return '暂无内容';

        // 截取前200字符
        const maxLength = 200;
        if (content.length > maxLength) {
            return content.substring(0, maxLength) + '...';
        }

        return content;
    }

    /**
     * 显示无结果状态
     */
    showNoResults() {
        console.log('❌ 显示无结果状态');

        const container = window.DOMManager.get('searchResults');
        if (container) {
            container.innerHTML = `
                <div class="no-results">
                    <div class="no-results-icon">
                        <i class="fas fa-search fa-3x"></i>
                    </div>
                    <h5>未找到相关结果</h5>
                    <p>建议：</p>
                    <ul>
                        <li>尝试使用不同的关键词</li>
                        <li>使用更通用的法律术语</li>
                        <li>检查拼写是否正确</li>
                    </ul>
                </div>
            `;
            container.style.display = 'block';
        }
    }

    /**
     * 显示模块详情结果
     */
    displayModuleResults(moduleName, moduleData) {
        console.log('🔍 显示模块详情结果:', moduleName);

        if (!moduleData || !moduleData.output_data) {
            console.warn('⚠️ 模块数据无效');
            return;
        }

        const outputData = moduleData.output_data;
        const articles = outputData.articles || [];
        const cases = outputData.cases || [];

        // 更新模块详情面板中的结果
        this.updateModuleDetailResults(articles, cases);
    }

    /**
     * 更新模块详情中的结果
     */
    updateModuleDetailResults(articles, cases) {
        // 更新法条结果
        const articlesSection = document.getElementById('articles-section');
        const articlesContainer = document.getElementById('articles-container');
        const articlesCountText = document.getElementById('articles-count-text');

        if (articles.length > 0 && articlesSection && articlesContainer && articlesCountText) {
            articlesSection.style.display = 'block';
            articlesCountText.textContent = articles.length;

            // 清空并填充法条
            articlesContainer.innerHTML = '';
            articles.forEach(article => {
                const element = this.createSimpleResultElement(article, 'article');
                if (element) {
                    articlesContainer.appendChild(element);
                }
            });
        } else if (articlesSection) {
            articlesSection.style.display = 'none';
        }

        // 更新案例结果
        const casesSection = document.getElementById('cases-section');
        const casesContainer = document.getElementById('cases-container');
        const casesCountText = document.getElementById('cases-count-text');

        if (cases.length > 0 && casesSection && casesContainer && casesCountText) {
            casesSection.style.display = 'block';
            casesCountText.textContent = cases.length;

            // 清空并填充案例
            casesContainer.innerHTML = '';
            cases.forEach(case_item => {
                const element = this.createSimpleResultElement(case_item, 'case');
                if (element) {
                    casesContainer.appendChild(element);
                }
            });
        } else if (casesSection) {
            casesSection.style.display = 'none';
        }

        // 更新无结果显示
        const noResultsMessage = document.getElementById('no-results-message');
        if (noResultsMessage) {
            const hasResults = articles.length > 0 || cases.length > 0;
            noResultsMessage.style.display = hasResults ? 'none' : 'block';
        }
    }

    /**
     * 创建简单结果元素（用于模块详情）
     */
    createSimpleResultElement(item, type) {
        const div = document.createElement('div');
        div.className = 'result-item-simple clickable-result';

        const similarity = ((item.similarity || 0) * 100).toFixed(1);
        const title = this.formatTitle(item, type);
        const content = this.formatContent(item.content);

        div.innerHTML = `
            <div class="result-header-simple">
                <span class="result-title-simple">${title}</span>
                <span class="result-similarity-simple">${similarity}%</span>
            </div>
            <div class="result-content-simple">${content}</div>
        `;

        // 添加点击事件
        div.addEventListener('click', () => {
            window.showItemDetail(item, type);
        });

        return div;
    }

    /**
     * 显示实时模块结果
     */
    displayRealtimeModuleResult(moduleName, moduleData) {
        console.log('⚡ 显示实时模块结果:', moduleName);

        const container = window.DOMManager.get('realtime-results-container');
        const modulesContainer = window.DOMManager.get('realtime-modules-results');

        if (!container || !modulesContainer) {
            console.error('❌ 实时结果容器未找到');
            return;
        }

        // 显示实时结果容器
        container.style.display = 'block';

        // 创建或更新模块卡片
        let moduleCard = document.getElementById(`realtime-module-${moduleName}`);
        if (!moduleCard) {
            moduleCard = this.createRealtimeModuleCard(moduleName, moduleData);
            if (moduleCard) {
                modulesContainer.appendChild(moduleCard);
            }
        } else {
            this.updateRealtimeModuleCard(moduleCard, moduleData);
        }
    }

    /**
     * 创建实时模块卡片
     */
    createRealtimeModuleCard(moduleName, moduleData) {
        const template = window.DOMManager.getTemplate('realtime-module-card-template');
        if (!template) {
            console.error('❌ 实时模块卡片模板未找到');
            return null;
        }

        const cardElement = template.content.cloneNode(true);
        const card = cardElement.querySelector('.realtime-module-card');

        if (card) {
            card.id = `realtime-module-${moduleName}`;
            this.updateRealtimeModuleCard(card, moduleData);
        }

        return cardElement;
    }

    /**
     * 更新实时模块卡片
     */
    updateRealtimeModuleCard(card, moduleData) {
        // 获取显示名称和状态
        const displayName = window.DataFormatter ?
            window.DataFormatter.getPathDisplayName(moduleData.module_name || '') :
            moduleData.module_name || '未知模块';

        const statusIcon = moduleData.status === 'success' ? '成功' : '失败';
        const statusClass = moduleData.status === 'success' ? 'success' : 'error';
        const resultsCount = moduleData.results_count || 0;
        const processingTime = Math.round(moduleData.processing_time_ms || 0);

        // 更新卡片内容
        const elements = {
            '.module-status-icon': statusIcon,
            '.module-name': displayName,
            '.module-time': `${processingTime}ms`,
            '.module-results-count': `找到 ${resultsCount} 条结果`
        };

        Object.entries(elements).forEach(([selector, content]) => {
            const element = card.querySelector(selector);
            if (element) {
                element.textContent = content;
            }
        });

        // 更新状态样式
        const header = card.querySelector('.realtime-module-header');
        if (header) {
            header.className = `realtime-module-header ${statusClass}`;
        }

        // 更新状态指示器
        const successIndicator = card.querySelector('.success-indicator');
        const errorIndicator = card.querySelector('.error-indicator');
        const successMessage = card.querySelector('.success-message');
        const errorMessage = card.querySelector('.error-message');

        if (moduleData.status === 'success') {
            if (successIndicator) successIndicator.style.display = 'block';
            if (errorIndicator) errorIndicator.style.display = 'none';
            if (successMessage) successMessage.textContent = `模块执行成功，${resultsCount}条相关法律文档已找到`;
        } else {
            if (successIndicator) successIndicator.style.display = 'none';
            if (errorIndicator) errorIndicator.style.display = 'block';
            if (errorMessage) errorMessage.textContent = '模块执行失败，请检查系统状态';
        }

        // 更新时间戳
        const completionTime = card.querySelector('.completion-time');
        if (completionTime && moduleData.timestamp) {
            completionTime.textContent = new Date(moduleData.timestamp).toLocaleTimeString();
        }
    }

    /**
     * 清空所有结果
     */
    clearResults() {
        console.log('🧹 清空所有结果');

        // 清空主要结果容器
        const containers = [
            'articles-results-container',
            'cases-results-container',
            'realtime-modules-results'
        ];

        containers.forEach(containerId => {
            const container = window.DOMManager.get(containerId);
            if (container) {
                container.innerHTML = '';
            }
        });

        // 隐藏结果区域
        window.DOMManager.updateVisibility({
            'searchResults': false,
            'articles-results-section': false,
            'cases-results-section': false,
            'realtime-results-container': false
        });
    }

    /**
     * 清理资源
     */
    destroy() {
        this.clearResults();
        console.log('🧹 ResultRenderer已清理');
    }
}

// 创建并导出单例
if (!window.ResultRenderer) {
    window.ResultRenderer = new ResultRenderer();
}