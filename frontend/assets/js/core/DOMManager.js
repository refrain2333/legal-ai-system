/**
 * DOM缓存管理器 - 减少重复DOM查询，提升性能
 */
class DOMManager {
    constructor() {
        this.cache = new Map();
        this.templates = new Map();
        this.initialized = false;
    }

    /**
     * 初始化缓存所有常用DOM元素
     */
    initialize() {
        if (this.initialized) return;

        // 缓存核心元素
        const coreElements = {
            // 搜索相关
            'searchQuery': 'searchQuery',
            'searchBtn': 'searchBtn',
            'clearBtn': 'clearBtn',

            // 状态显示
            'websocketStatus': 'websocketStatus',
            'websocket-icon': 'websocket-icon',
            'websocket-text': 'websocket-text',
            'search-btn-icon': 'search-btn-icon',
            'search-btn-text': 'search-btn-text',

            // 面板容器
            'performancePanel': 'performancePanel',
            'searchResults': 'searchResults',
            'errorPanel': 'errorPanel',
            'errorContent': 'errorContent',
            'module-detail-panel': 'module-detail-panel',

            // 阶段相关
            'stage1': 'stage1',
            'stage2': 'stage2',
            'stage3': 'stage3',
            'stage4': 'stage4',
            'stage5': 'stage5',

            // 结果容器
            'articles-results-section': 'articles-results-section',
            'cases-results-section': 'cases-results-section',
            'articles-results-container': 'articles-results-container',
            'cases-results-container': 'cases-results-container',

            // 实时结果
            'realtime-results-container': 'realtime-results-container',
            'realtime-modules-results': 'realtime-modules-results'
        };

        // 批量缓存元素
        this.cacheElements(coreElements);

        // 缓存阶段详细元素
        this.cacheStageElements();

        // 缓存性能监控元素
        this.cachePerformanceElements();

        // 缓存模板
        this.cacheTemplates();

        this.initialized = true;
        console.log('✅ DOMManager初始化完成，缓存了', this.cache.size, '个元素');
    }

    /**
     * 批量缓存元素
     */
    cacheElements(elementMap) {
        Object.entries(elementMap).forEach(([key, id]) => {
            const element = document.getElementById(id);
            if (element) {
                this.cache.set(key, element);
            } else {
                console.warn(`⚠️ 元素未找到: ${id}`);
            }
        });
    }

    /**
     * 缓存阶段相关元素
     */
    cacheStageElements() {
        for (let i = 1; i <= 5; i++) {
            const stageElements = {
                [`stage${i}-result`]: `stage${i}-result`,
                [`stage${i}-time`]: `stage${i}-time`,
                [`stage${i}-details`]: i === 4 ? `stage${i}-details-inline` : `stage${i}-details`
            };
            this.cacheElements(stageElements);
        }
    }

    /**
     * 缓存性能监控元素
     */
    cachePerformanceElements() {
        const perfElements = {
            'debugTotalTime': 'debugTotalTime',
            'debugApiTime': 'debugApiTime',
            'debugServerTime': 'debugServerTime',
            'debugFrontendTime': 'debugFrontendTime',
            'debugApiPercent': 'debugApiPercent',
            'debugServerPercent': 'debugServerPercent',
            'debugFrontendPercent': 'debugFrontendPercent',
            'debugTimerStatus': 'debugTimerStatus',
            'debug-status-icon': 'debug-status-icon',
            'debug-status-text': 'debug-status-text',
            'debug-status-time': 'debug-status-time'
        };
        this.cacheElements(perfElements);
    }

    /**
     * 缓存模板元素
     */
    cacheTemplates() {
        const templateIds = [
            'result-item-template',
            'realtime-module-card-template',
            'fusion-detail-template',
            'module-detail-template',
            'keyword-tag-template',
            'log-entry-template'
        ];

        templateIds.forEach(id => {
            const template = document.getElementById(id);
            if (template) {
                this.templates.set(id, template);
            }
        });
    }

    /**
     * 获取缓存的元素
     */
    get(key) {
        return this.cache.get(key);
    }

    /**
     * 获取模板
     */
    getTemplate(templateId) {
        return this.templates.get(templateId);
    }

    /**
     * 批量更新文本内容
     */
    updateTexts(updates) {
        Object.entries(updates).forEach(([key, text]) => {
            const element = this.get(key);
            if (element) {
                element.textContent = text;
            }
        });
    }

    /**
     * 批量更新可见性
     */
    updateVisibility(updates) {
        Object.entries(updates).forEach(([key, isVisible]) => {
            const element = this.get(key);
            if (element) {
                element.style.display = isVisible ? 'block' : 'none';
            }
        });
    }

    /**
     * 批量更新CSS类
     */
    updateClasses(updates) {
        Object.entries(updates).forEach(([key, className]) => {
            const element = this.get(key);
            if (element) {
                element.className = className;
            }
        });
    }

    /**
     * 使用模板创建元素
     */
    createFromTemplate(templateId, data = {}) {
        const template = this.getTemplate(templateId);
        if (!template) {
            console.error(`模板不存在: ${templateId}`);
            return null;
        }

        const clone = template.content.cloneNode(true);

        // 如果提供了数据，填充到模板中
        if (Object.keys(data).length > 0) {
            this.fillTemplateData(clone, data);
        }

        return clone;
    }

    /**
     * 填充模板数据
     */
    fillTemplateData(element, data) {
        Object.entries(data).forEach(([selector, value]) => {
            const target = element.querySelector(selector);
            if (target && value !== undefined) {
                target.textContent = value;
            }
        });
    }

    /**
     * 清理缓存（页面卸载时调用）
     */
    destroy() {
        this.cache.clear();
        this.templates.clear();
        this.initialized = false;
    }
}

// 创建并导出单例
const domManagerInstance = new DOMManager();

// 直接将实例绑定到全局对象
window.DOMManager = domManagerInstance;

// 验证绑定是否成功
const domVerifyMethods = ['get', 'getTemplate', 'updateTexts', 'updateVisibility', 'updateClasses', 'initialize'];
const domMissingMethods = domVerifyMethods.filter(method => typeof window.DOMManager[method] !== 'function');

if (domMissingMethods.length > 0) {
    console.error('❌ DOMManager方法绑定失败:', domMissingMethods);
} else {
    console.log('✅ DOMManager单例创建并绑定完成，所有关键方法可用');
}