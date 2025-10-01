/**
 * 统一导航栏组件
 * 在三个页面间提供快速跳转
 */
class NavigationBar {
    constructor() {
        this.currentPage = this.getCurrentPage();
        this.init();
    }

    getCurrentPage() {
        const pathname = window.location.pathname;
        if (pathname.includes('basic-search')) return 'basic-search';
        if (pathname.includes('complete-flow')) return 'complete-flow';
        if (pathname.includes('knowledge-graph')) return 'knowledge-graph';
        if (pathname.includes('about')) return 'about';
        return 'home'; // 默认首页
    }

    init() {
        this.render();
        this.bindEvents();
    }

    render() {
        // 根据当前页面位置确定正确的路径
        const currentPath = window.location.pathname;
        const isInPagesFolder = currentPath.includes('/pages/');

        let homeHref, completeFlowHref, basicSearchHref, knowledgeGraphHref, aboutHref;

        if (isInPagesFolder) {
            // 在pages文件夹内
            homeHref = '../index.html';
            completeFlowHref = './complete-flow.html';
            basicSearchHref = './basic-search.html';
            knowledgeGraphHref = './knowledge-graph.html';
            aboutHref = './about.html';
        } else {
            // 在根目录
            homeHref = './index.html';
            completeFlowHref = './pages/complete-flow.html';
            basicSearchHref = './pages/basic-search.html';
            knowledgeGraphHref = './pages/knowledge-graph.html';
            aboutHref = './pages/about.html';
        }

        const navHtml = `
            <nav class="main-navigation">
                <div class="nav-container">
                    <div class="nav-brand">
                        <i class="fas fa-balance-scale"></i>
                        <span>法智导航</span>
                    </div>
                    <div class="nav-links">
                        <a href="${homeHref}" class="nav-link ${this.currentPage === 'home' ? 'active' : ''}" data-page="home">
                            <span>首页</span>
                        </a>
                        <a href="${completeFlowHref}" class="nav-link ${this.currentPage === 'complete-flow' ? 'active' : ''}" data-page="complete-flow">
                            <span>完整流程</span>
                        </a>
                        <a href="${basicSearchHref}" class="nav-link ${this.currentPage === 'basic-search' ? 'active' : ''}" data-page="basic-search">
                            <span>基础搜索</span>
                        </a>
                        <a href="${knowledgeGraphHref}" class="nav-link ${this.currentPage === 'knowledge-graph' ? 'active' : ''}" data-page="knowledge-graph">
                            <span>知识图谱</span>
                        </a>
                        <a href="${aboutHref}" class="nav-link ${this.currentPage === 'about' ? 'active' : ''}" data-page="about">
                            <span>关于法智导航</span>
                        </a>
                    </div>
                    <div class="nav-tools">
                        <button class="nav-tool-btn" id="systemStatus" title="系统状态">
                            <i class="fas fa-circle text-success"></i>
                        </button>
                        <button class="nav-tool-btn" id="settingsBtn" title="设置">
                            <i class="fas fa-cog"></i>
                        </button>
                    </div>
                </div>
            </nav>
        `;

        // 修改插入逻辑，确保没有额外空白
        document.body.insertAdjacentHTML('afterbegin', navHtml);

        // 添加导航栏存在标识
        document.body.classList.add('has-navigation');

        // 移除可能的空白文本节点
        const textNodes = Array.from(document.body.childNodes)
            .filter(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim() === '');
        textNodes.forEach(node => node.remove());
    }

    bindEvents() {
        // 延迟绑定事件，确保DOM完全加载
        setTimeout(() => {
            // 页面跳转事件
            document.querySelectorAll('.nav-link').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const targetPage = e.currentTarget.getAttribute('data-page');
                    this.navigateTo(targetPage);
                });
            });

            // 系统状态检查
            this.checkSystemStatus();

            // 设置按钮事件
            const settingsBtn = document.getElementById('settingsBtn');
            if (settingsBtn) {
                settingsBtn.addEventListener('click', () => this.handleSettings());
            }
        }, 100);
    }

    navigateTo(page) {
        // 根据当前页面位置确定正确的路径
        const currentPath = window.location.pathname;
        const isInPagesFolder = currentPath.includes('/pages/');

        let pageUrls;
        if (isInPagesFolder) {
            // 在pages文件夹内
            pageUrls = {
                'home': '../index.html',
                'complete-flow': './complete-flow.html',
                'basic-search': './basic-search.html',
                'knowledge-graph': './knowledge-graph.html',
                'about': './about.html'
            };
        } else {
            // 在根目录
            pageUrls = {
                'home': './index.html',
                'complete-flow': './pages/complete-flow.html',
                'basic-search': './pages/basic-search.html',
                'knowledge-graph': './pages/knowledge-graph.html',
                'about': './pages/about.html'
            };
        }

        if (pageUrls[page]) {
            console.log(`导航到: ${page} -> ${pageUrls[page]}`);
            window.location.href = pageUrls[page];
        } else {
            console.error(`未知页面: ${page}`);
        }
    }

    async checkSystemStatus() {
        try {
            const response = await fetch('http://127.0.0.1:5006/health');
            const statusIcon = document.querySelector('#systemStatus i');

            if (response.ok) {
                statusIcon.className = 'fas fa-circle text-success';
                statusIcon.parentElement.title = '系统正常';
            } else {
                statusIcon.className = 'fas fa-circle text-warning';
                statusIcon.parentElement.title = '系统异常';
            }
        } catch (error) {
            const statusIcon = document.querySelector('#systemStatus i');
            statusIcon.className = 'fas fa-circle text-danger';
            statusIcon.parentElement.title = '系统离线';
        }
    }

    handleSettings() {
        // 在基础搜索页面，设置按钮用于切换详细加载面板
        if (this.currentPage === 'basic-search') {
            const loadingDetails = document.getElementById('loadingDetails');

            if (loadingDetails) {
                // 切换详细加载面板的显示
                const isDetailsVisible = loadingDetails.style.display !== 'none';

                if (isDetailsVisible) {
                    // 隐藏详情面板
                    loadingDetails.style.display = 'none';
                    loadingDetails.classList.add('hidden');
                } else {
                    // 显示详情面板，但不显示系统状态栏
                    loadingDetails.style.display = 'block';
                    loadingDetails.classList.remove('hidden');

                    // 触发详细状态更新
                    if (window.legalNavigator && typeof window.legalNavigator.updateSystemStatusDisplay === 'function') {
                        window.legalNavigator.updateSystemStatusDisplay();
                    }
                }
            }
        } else if (this.currentPage === 'complete-flow') {
            // 在完整流程页面，设置按钮用于切换简单模式和调试模式
            console.log('🔧 点击设置按钮 - 切换模式');

            // 查找页面中的模式切换元素
            const simpleMode = document.querySelector('input[name="viewMode"][value="simple"]');
            const debugMode = document.querySelector('input[name="viewMode"][value="debug"]');

            if (simpleMode && debugMode) {
                // 获取当前模式
                const currentSimple = simpleMode.checked;
                console.log('🔄 当前模式 - 简单模式:', currentSimple);

                // 切换模式
                if (currentSimple) {
                    debugMode.checked = true;
                    console.log('✅ 切换到调试模式');
                } else {
                    simpleMode.checked = true;
                    console.log('✅ 切换到简单模式');
                }

                // 触发模式变更事件
                const event = new Event('change', { bubbles: true });
                const checkedElement = simpleMode.checked ? simpleMode : debugMode;
                checkedElement.dispatchEvent(event);

                // 如果有全局的模式切换函数，也调用它
                if (typeof window.toggleMode === 'function') {
                    window.toggleMode();
                }

                // 手动触发显示模式更新
                const newMode = simpleMode.checked ? 'simple' : 'debug';
                console.log('🎯 新模式:', newMode);

                // 调用页面的模式切换函数
                if (typeof window.updateDisplayMode === 'function') {
                    window.updateDisplayMode(newMode);
                }
            } else {
                console.warn('⚠️ 未找到模式切换元素');
                console.log('simpleMode:', simpleMode);
                console.log('debugMode:', debugMode);
            }
        } else {
            // 其他页面的设置功能可以在这里添加
            console.log('设置功能 - 当前页面:', this.currentPage);
        }
    }
}

// 自动初始化导航栏
document.addEventListener('DOMContentLoaded', () => {
    new NavigationBar();
});