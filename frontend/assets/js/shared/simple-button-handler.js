/**
 * 法智导航 - 极简按钮处理器
 * 专门解决F12环境下按钮无响应的问题
 */

console.log('🚀 SimpleButtonHandler 开始加载');

// 全局变量存储
window.SimpleButtonHandler = {
    initialized: false,
    moduleData: {},
    currentModule: null
};

/**
 * 初始化处理器
 */
window.SimpleButtonHandler.init = function() {
    if (this.initialized) {
        console.log('⚠️ SimpleButtonHandler 已初始化，跳过');
        return;
    }

    console.log('🚀 初始化 SimpleButtonHandler');

    // 绑定全局函数
    this.bindGlobalFunctions();

    // 设置事件监听
    this.setupEventListeners();

    // 获取模块数据
    this.loadModuleData();

    this.initialized = true;
    console.log('✅ SimpleButtonHandler 初始化完成');
};

/**
 * 绑定全局函数
 */
window.SimpleButtonHandler.bindGlobalFunctions = function() {
    // 直接绑定到window对象
    window.showModuleDetailsSimple = this.showModuleDetails.bind(this);
    window.hideModuleDetailsSimple = this.hideModuleDetails.bind(this);
    window.toggleAnswerSimple = this.toggleAnswer.bind(this);

    console.log('✅ 全局函数绑定完成');
};

/**
 * 设置事件监听器
 */
window.SimpleButtonHandler.setupEventListeners = function() {
    // 移除所有现有的监听器（如果存在）
    if (this.handleButtonClick) {
        document.removeEventListener('click', this.handleButtonClick);
    }

    // 创建新的处理函数
    this.handleButtonClick = this.createButtonClickHandler();

    // 添加事件监听器
    document.addEventListener('click', this.handleButtonClick);

    console.log('✅ 事件监听器设置完成');
};

/**
 * 创建按钮点击处理函数
 */
window.SimpleButtonHandler.createButtonClickHandler = function() {
    return function(event) {
        console.log('🎯 点击事件触发，目标:', event.target);

        // 查找模块详情按钮
        const detailBtn = event.target.closest('.module-detail-btn-simple');
        if (detailBtn) {
            event.preventDefault();
            event.stopPropagation();

            const modulePath = detailBtn.getAttribute('data-module-path');
            console.log('🔍 点击模块详情按钮:', modulePath);
            console.log('🔍 window.showModuleDetailsSimple 存在:', !!window.showModuleDetailsSimple);

            if (modulePath && window.showModuleDetailsSimple) {
                console.log('🚀 调用 showModuleDetailsSimple');
                window.showModuleDetailsSimple(modulePath);
            } else {
                console.error('❌ showModuleDetailsSimple 不存在或 modulePath 为空');
            }
            return;
        }

        // 查找答案切换按钮
        const toggleBtn = event.target.closest('.toggle-answer-btn');
        if (toggleBtn) {
            event.preventDefault();
            event.stopPropagation();

            console.log('🔄 点击答案切换按钮');

            if (window.toggleAnswerSimple) {
                window.toggleAnswerSimple();
            }
            return;
        }

        // 查找关闭按钮
        const closeBtn = event.target.closest('.close-btn-simple');
        if (closeBtn) {
            event.preventDefault();
            event.stopPropagation();

            console.log('🙈 点击关闭按钮');

            if (window.hideModuleDetailsSimple) {
                window.hideModuleDetailsSimple();
            }
            return;
        }
    }.bind(this);
};

/**
 * 加载模块数据
 */
window.SimpleButtonHandler.loadModuleData = function() {
    try {
        // 从多个可能的来源获取数据
        this.moduleData =
            window.StateManager?.get?.('stage4Modules') ||
            window.stage4Modules ||
            window.currentSearchData?.stage4 ||
            {};

        console.log('📊 加载模块数据:', Object.keys(this.moduleData));
    } catch (error) {
        console.warn('⚠️ 加载模块数据失败:', error);
        this.moduleData = {};
    }
};

/**
 * 显示模块详情
 */
window.SimpleButtonHandler.showModuleDetails = function(searchPath) {
    console.log('🔍 显示模块详情:', searchPath);

    try {
        // 确保有数据
        if (!this.moduleData || Object.keys(this.moduleData).length === 0) {
            this.loadModuleData();
        }

        // 获取模块数据
        const moduleData = this.moduleData[searchPath];
        if (!moduleData) {
            console.error('❌ 模块数据未找到:', searchPath);
            this.showError('模块数据不可用');
            return;
        }

        // 获取或创建面板
        let panel = document.getElementById('simple-module-panel');
        if (!panel) {
            panel = this.createPanel();
            document.body.appendChild(panel);
        }

        // 重新绑定关闭按钮事件（防止事件丢失）
        this.rebindCloseButton(panel);

        // 填充内容
        this.fillPanelContent(panel, moduleData, searchPath);

        // 显示面板
        panel.style.display = 'block';
        panel.style.position = 'fixed'; // 确保是固定定位
        panel.style.zIndex = '10000'; // 确保在最上层

        // 记录当前模块
        this.currentModule = searchPath;

        console.log('✅ 模块详情显示成功');

    } catch (error) {
        console.error('❌ 显示模块详情失败:', error);
    }
};

/**
 * 重新绑定关闭按钮事件
 */
window.SimpleButtonHandler.rebindCloseButton = function(panel) {
    const closeBtn = panel.querySelector('.close-btn-simple');
    if (closeBtn) {
        // 移除旧的事件监听器
        closeBtn.removeEventListener('click', this.closeHandler);

        // 创建新的事件处理器
        this.closeHandler = (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.hideModuleDetails();
        };

        // 添加新的事件监听器
        closeBtn.addEventListener('click', this.closeHandler);
    }
};

/**
 * 隐藏模块详情
 */
window.SimpleButtonHandler.hideModuleDetails = function() {
    console.log('🙈 隐藏模块详情');

    try {
        const panel = document.getElementById('simple-module-panel');
        if (panel) {
            panel.style.display = 'none';
            // 不移除面板，只是隐藏，这样可以重复使用
        }

        this.currentModule = null;
        console.log('✅ 模块详情已隐藏');

    } catch (error) {
        console.error('❌ 隐藏模块详情失败:', error);
    }
};

/**
 * 切换答案显示
 */
window.SimpleButtonHandler.toggleAnswer = function() {
    console.log('🔄 切换答案显示');

    try {
        const answerContent = document.getElementById('ai-answer-content');
        const toggleBtn = document.getElementById('toggle-answer-btn');

        if (!answerContent) {
            console.warn('⚠️ 答案内容未找到');
            return;
        }

        const isExpanded = answerContent.classList.contains('expanded');

        if (isExpanded) {
            // 收起
            answerContent.classList.remove('expanded');
            answerContent.classList.add('collapsed');
            answerContent.style.maxHeight = '100px';

            if (toggleBtn) {
                toggleBtn.innerHTML = '<i class="fas fa-chevron-down me-1"></i>展开完整回答';
            }
        } else {
            // 展开
            answerContent.classList.remove('collapsed');
            answerContent.classList.add('expanded');
            answerContent.style.maxHeight = 'none';

            if (toggleBtn) {
                toggleBtn.innerHTML = '<i class="fas fa-chevron-up me-1"></i>收起回答';
            }
        }

        console.log('✅ 答案切换成功');

    } catch (error) {
        console.error('❌ 切换答案失败:', error);
    }
};

/**
 * 创建面板
 */
window.SimpleButtonHandler.createPanel = function() {
    const panel = document.createElement('div');
    panel.id = 'simple-module-panel';
    panel.className = 'simple-module-panel';
    panel.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 80%;
        max-width: 800px;
        max-height: 80vh;
        background: white;
        border: 2px solid #007bff;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 10000;
        display: none;
        flex-direction: column;
    `;

    panel.innerHTML = `
        <div class="simple-panel-header" style="
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
            background: #f8f9fa;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <h5 id="simple-panel-title" style="margin: 0; color: #495057;">模块详情</h5>
            <button class="close-btn-simple" style="
                background: none;
                border: 1px solid #6c757d;
                color: #6c757d;
                padding: 4px 8px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            ">关闭</button>
        </div>
        <div id="simple-panel-content" style="
            padding: 20px;
            overflow-y: auto;
            flex: 1;
        ">
            加载中...
        </div>
    `;

    return panel;
};

/**
 * 填充面板内容
 */
window.SimpleButtonHandler.fillPanelContent = function(panel, moduleData, searchPath) {
    const titleElement = panel.querySelector('#simple-panel-title');
    const contentElement = panel.querySelector('#simple-panel-content');

    // 设置标题
    const displayName = this.getDisplayName(searchPath);
    titleElement.textContent = `模块详情: ${displayName}`;

    // 设置内容
    const articles = moduleData.output_data?.articles || [];
    const cases = moduleData.output_data?.cases || [];
    const processingTime = Math.round(moduleData.processing_time_ms || 0);

    contentElement.innerHTML = `
        <div style="margin-bottom: 20px;">
            <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                <span style="padding: 4px 8px; background: ${moduleData.status === 'success' ? '#d4edda' : '#f8d7da'}; color: ${moduleData.status === 'success' ? '#155724' : '#721c24'}; border-radius: 4px; font-size: 12px;">
                    ${moduleData.status}
                </span>
                <span style="padding: 4px 8px; background: #e9ecef; color: #495057; border-radius: 4px; font-size: 12px;">
                    耗时: ${processingTime}ms
                </span>
            </div>
        </div>

        ${articles.length > 0 ? `
            <div style="margin-bottom: 20px;">
                <h6 style="color: #495057; margin-bottom: 10px;">相关法条 (${articles.length}条)</h6>
                ${articles.slice(0, 5).map((article, index) => `
                    <div style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 10px; margin-bottom: 8px;">
                        <div style="font-weight: 600; color: #007bff; margin-bottom: 5px;">
                            #${index + 1} ${article.title || article.id}
                        </div>
                        <div style="color: #6c757d; font-size: 12px; margin-bottom: 5px;">
                            相似度: ${((article.similarity || 0) * 100).toFixed(1)}%
                        </div>
                        <div style="color: #495057; font-size: 13px; line-height: 1.4;">
                            ${(article.content || '').substring(0, 150)}${(article.content || '').length > 150 ? '...' : ''}
                        </div>
                    </div>
                `).join('')}
                ${articles.length > 5 ? `<div style="text-align: center; color: #6c757d; font-size: 12px;">还有 ${articles.length - 5} 条法条...</div>` : ''}
            </div>
        ` : ''}

        ${cases.length > 0 ? `
            <div style="margin-bottom: 20px;">
                <h6 style="color: #495057; margin-bottom: 10px;">相关案例 (${cases.length}个)</h6>
                ${cases.slice(0, 3).map((case_item, index) => `
                    <div style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 10px; margin-bottom: 8px;">
                        <div style="font-weight: 600; color: #28a745; margin-bottom: 5px;">
                            #${index + 1} ${case_item.title || case_item.id}
                        </div>
                        <div style="color: #6c757d; font-size: 12px; margin-bottom: 5px;">
                            相似度: ${((case_item.similarity || 0) * 100).toFixed(1)}%
                        </div>
                        ${case_item.sentence_result ? `
                            <div style="color: #dc3545; font-size: 12px; margin-bottom: 5px;">
                                判决: ${case_item.sentence_result}
                            </div>
                        ` : ''}
                        <div style="color: #495057; font-size: 13px; line-height: 1.4;">
                            ${(case_item.content || '').substring(0, 100)}${(case_item.content || '').length > 100 ? '...' : ''}
                        </div>
                    </div>
                `).join('')}
                ${cases.length > 3 ? `<div style="text-align: center; color: #6c757d; font-size: 12px;">还有 ${cases.length - 3} 个案例...</div>` : ''}
            </div>
        ` : ''}

        ${!articles.length && !cases.length ? `
            <div style="text-align: center; color: #6c757d; padding: 20px;">
                该模块暂无详细数据
            </div>
        ` : ''}
    `;
};

/**
 * 显示错误信息
 */
window.SimpleButtonHandler.showError = function(message) {
    let panel = document.getElementById('simple-module-panel');
    if (!panel) {
        panel = this.createPanel();
        document.body.appendChild(panel);
    }

    const titleElement = panel.querySelector('#simple-panel-title');
    const contentElement = panel.querySelector('#simple-panel-content');

    titleElement.textContent = '错误';
    contentElement.innerHTML = `
        <div style="text-align: center; padding: 20px; color: #dc3545;">
            <div style="font-size: 18px; margin-bottom: 10px; font-weight: bold;">注意</div>
            <div>${message}</div>
        </div>
    `;

    panel.style.display = 'block';
};

/**
 * 获取显示名称
 */
window.SimpleButtonHandler.getDisplayName = function(searchPath) {
    const nameMap = {
        'semantic_search.vector_search': '向量搜索',
        'semantic_search.keyword_search': '关键词搜索',
        'semantic_search.hybrid_search': '混合搜索',
        'enhanced_semantic_search.query2doc': 'Query2Doc增强',
        'enhanced_semantic_search.hyde': 'HyDE增强',
        'knowledge_graph_search': '知识图谱搜索',
        'llm_enhanced_search': 'LLM增强搜索'
    };
    return nameMap[searchPath] || searchPath;
};

// 自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.SimpleButtonHandler.init();
    });
} else {
    window.SimpleButtonHandler.init();
}

// 额外的安全网 - 确保在页面加载完成后初始化
window.addEventListener('load', () => {
    setTimeout(() => {
        window.SimpleButtonHandler.init();
    }, 1000);
});

// 全局函数，可以直接使用
function showSimpleModuleDetails(modulePath) {
    if (window.SimpleButtonHandler) {
        window.SimpleButtonHandler.showModuleDetails(modulePath);
    }
}

function hideSimpleModuleDetails() {
    if (window.SimpleButtonHandler) {
        window.SimpleButtonHandler.hideModuleDetails();
    }
}

console.log('🚀 SimpleButtonHandler 加载完成');