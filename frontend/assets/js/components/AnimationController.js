/**
 * 动画控制器 - 负责阶段动画效果和状态转换
 * 遵循项目规范：不使用emoji，专业界面设计
 */
class AnimationController {
    constructor() {
        this.animationQueue = [];
        this.isAnimating = false;
        this.defaultDuration = 300; // 默认动画时长
        this.stageTransitionDelay = 150; // 阶段切换延迟

        // 动画效果配置
        this.animations = {
            fadeIn: 'fadeIn 0.3s ease-in',
            slideIn: 'slideInRight 0.3s ease-out',
            pulse: 'pulse 1.5s infinite',
            bounce: 'bounceIn 0.5s ease-out',
            shake: 'shake 0.5s ease-out'
        };

        // 状态颜色配置
        this.statusColors = {
            pending: '#6c757d',
            running: '#3b82f6',
            success: '#1e40af',
            error: '#dc3545',
            warning: '#f59e0b'
        };
    }

    /**
     * 启动渐进式显示动画
     * @param {Object} traceData - 完整的trace数据
     * @param {Object} stageRenderers - 各阶段的渲染函数
     */
    startProgressiveDisplay(traceData, stageRenderers) {
        if (!traceData) {
            return;
        }

        // 清空之前的动画队列
        this.animationQueue = [];

        // 构建动画序列
        const sequence = [];

        // 阶段1: 分类
        if (traceData.classification && stageRenderers.stage1) {
            sequence.push({
                delay: 500,
                action: () => {
                    const result = stageRenderers.stage1(traceData.classification);
                    if (result) {
                        this.updateStageWithAnimation('stage1', 'success', result.message, result.time);
                        if (result.details) {
                            setTimeout(() => this._showStageDetails('stage1-details', result.details), 200);
                        }
                    }
                }
            });
        }

        // 阶段2: 提取
        if (traceData.extraction && stageRenderers.stage2) {
            sequence.push({
                delay: 800,
                action: () => {
                    const result = stageRenderers.stage2(traceData.extraction);
                    if (result) {
                        this.updateStageWithAnimation('stage2', 'success', result.message, result.time);
                        if (result.details) {
                            setTimeout(() => this._showStageDetails('stage2-details', result.details), 200);
                        }
                    }
                }
            });
        }

        // 阶段3: 路由
        if (traceData.routing && stageRenderers.stage3) {
            sequence.push({
                delay: 1200,
                action: () => {
                    const result = stageRenderers.stage3(traceData.routing);
                    if (result) {
                        this.updateStageWithAnimation('stage3', 'success', result.message, result.time);
                        if (result.details) {
                            setTimeout(() => this._showStageDetails('stage3-details', result.details), 200);
                        }
                    }
                }
            });
        }

        // 阶段4: 搜索
        if (traceData.searches && stageRenderers.stage4) {
            sequence.push({
                delay: 1600,
                action: () => {
                    const result = stageRenderers.stage4(traceData.searches);
                    if (result) {
                        this.updateStageWithAnimation('stage4', 'success', result.message, result.time);
                        if (result.details) {
                            // 立即显示详情，不使用延迟，以免影响按钮响应
                            this._showStageDetails('stage4-details-inline', result.details);
                        }
                    }
                }
            });
        }

        // 阶段5: 融合
        if (traceData.fusion && stageRenderers.stage5) {
            sequence.push({
                delay: 2000,
                action: () => {
                    const result = stageRenderers.stage5(traceData.fusion);
                    if (result) {
                        this.updateStageWithAnimation('stage5', 'success', result.message, result.time);
                        if (result.details) {
                            setTimeout(() => this._showStageDetails('stage5-details', result.details), 200);
                        }
                    }
                }
            });
        }

        // 执行动画序列
        this.executeAnimationSequence(sequence);
    }

    /**
     * 执行动画序列
     * @param {Array} sequence - 动画序列
     */
    executeAnimationSequence(sequence) {
        sequence.forEach((item, index) => {
            setTimeout(() => {
                try {
                    item.action();
                } catch (error) {
                    console.error(`动画序列执行错误 (步骤${index + 1}):`, error);
                }
            }, item.delay);
        });
    }

    /**
     * 带动画效果地更新阶段状态
     * @param {string} stageId - 阶段ID
     * @param {string} status - 状态 (pending/running/success/error)
     * @param {string} message - 显示消息
     * @param {number} timeMs - 处理时间
     */
    updateStageWithAnimation(stageId, status, message, timeMs = 0) {
        const stageElement = document.getElementById(stageId);
        const resultElement = document.getElementById(`${stageId}-result`);
        const timeElement = document.getElementById(`${stageId}-time`);

        if (!stageElement || !resultElement || !timeElement) {
            console.warn(`❌ 找不到阶段元素 ${stageId}`);
            return;
        }

        // 添加过渡动画
        stageElement.style.transition = 'all 0.3s ease';

        // 更新状态样式
        stageElement.className = `stage ${status}`;

        // 更新内容
        const newMessage = message || `阶段 ${stageId} ${this.getStatusText(status)}`;
        const newTime = timeMs > 0 ? `耗时: ${Math.round(timeMs)}ms` : '计算中...';

        resultElement.textContent = newMessage;
        timeElement.textContent = newTime;

        // 添加状态指示动画
        this.addStatusAnimation(stageElement, status);

        // 添加完成时的强调动画
        if (status === 'success') {
            this.addSuccessAnimation(stageElement);
        } else if (status === 'error') {
            this.addErrorAnimation(stageElement);
        } else if (status === 'running') {
            this.addRunningAnimation(stageElement);
        }

        console.log(`✅ AnimationController: 成功更新阶段 ${stageId} 为 ${status} 状态`);
    }

    /**
     * 添加状态指示动画
     * @param {Element} element - 目标元素
     * @param {string} status - 状态
     */
    addStatusAnimation(element, status) {
        // 清除之前的动画
        element.style.animation = '';

        // 根据状态添加对应动画
        switch (status) {
            case 'running':
                element.style.animation = this.animations.pulse;
                break;
            case 'success':
                // 成功时的放大效果
                element.style.transform = 'scale(1.02)';
                setTimeout(() => {
                    element.style.transform = 'scale(1)';
                }, 300);
                break;
            case 'error':
                element.style.animation = this.animations.shake;
                setTimeout(() => {
                    element.style.animation = '';
                }, 500);
                break;
        }
    }

    /**
     * 添加成功动画
     * @param {Element} element - 目标元素
     */
    addSuccessAnimation(element) {
        // 添加成功的闪烁效果
        const originalBoxShadow = element.style.boxShadow;

        element.style.boxShadow = '0 0 20px rgba(40, 167, 69, 0.5)';

        setTimeout(() => {
            element.style.boxShadow = originalBoxShadow;
        }, 600);
    }

    /**
     * 添加错误动画
     * @param {Element} element - 目标元素
     */
    addErrorAnimation(element) {
        // 添加错误的红色边框闪烁
        const originalBorder = element.style.border;

        element.style.border = '2px solid #dc3545';

        setTimeout(() => {
            element.style.border = originalBorder;
        }, 800);
    }

    /**
     * 添加运行中动画
     * @param {Element} element - 目标元素
     */
    addRunningAnimation(element) {
        // 添加运行中的渐变背景动画
        element.style.background = 'linear-gradient(90deg, #eff6ff 0%, #dbeafe 50%, #eff6ff 100%)';
        element.style.backgroundSize = '200% 100%';
        element.style.animation = 'gradientShift 2s ease-in-out infinite';
    }

    /**
     * 显示阶段详细信息
     * @param {string} detailsId - 详情容器ID
     * @param {string} detailsHtml - 详情HTML内容
     */
    _showStageDetails(detailsId, detailsHtml) {
        const detailsElement = document.getElementById(detailsId);
        if (!detailsElement) {
            return;
        }

        // 设置内容
        detailsElement.innerHTML = detailsHtml;

        // 添加展开动画
        detailsElement.style.opacity = '0';
        detailsElement.style.maxHeight = '0';
        detailsElement.style.overflow = 'hidden';
        detailsElement.style.transition = 'all 0.3s ease';
        detailsElement.style.display = 'block';

        // 触发动画
        setTimeout(() => {
            detailsElement.style.opacity = '1';
            detailsElement.style.maxHeight = '1000px'; // 足够大的高度
        }, 50);

        console.log(`AnimationController: 显示详情 ${detailsId}`);
    }

    /**
     * 隐藏阶段详细信息
     * @param {string} detailsId - 详情容器ID
     */
    hideStageDetails(detailsId) {
        const detailsElement = document.getElementById(detailsId);
        if (!detailsElement) return;

        detailsElement.style.transition = 'all 0.3s ease';
        detailsElement.style.opacity = '0';
        detailsElement.style.maxHeight = '0';

        setTimeout(() => {
            detailsElement.style.display = 'none';
        }, 300);
    }

    /**
     * 重置所有阶段动画
     */
    resetAllStages() {
        for (let i = 1; i <= 5; i++) {
            const stageElement = document.getElementById(`stage${i}`);
            if (stageElement) {
                stageElement.style.animation = '';
                stageElement.style.transform = '';
                stageElement.style.boxShadow = '';
                stageElement.style.border = '';
                stageElement.className = 'stage pending';
            }

            // 隐藏详情
            const detailsId = i === 4 ? `stage${i}-details-inline` : `stage${i}-details`;
            this.hideStageDetails(detailsId);
        }

        console.log('AnimationController: 重置所有阶段动画');
    }

    /**
     * 获取状态文本
     * @param {string} status - 状态
     * @returns {string} 状态文本
     */
    getStatusText(status) {
        const statusTexts = {
            pending: '等待中',
            running: '处理中',
            success: '已完成',
            error: '失败',
            warning: '警告'
        };
        return statusTexts[status] || status;
    }

    /**
     * 创建加载动画
     * @param {Element} container - 容器元素
     * @param {string} message - 加载消息
     */
    createLoadingAnimation(container, message = '正在处理...') {
        if (!container) return;

        const loadingHtml = `
            <div class="loading-animation">
                <div class="loading-spinner"></div>
                <div class="loading-message">${message}</div>
            </div>
        `;

        container.innerHTML = loadingHtml;
    }

    /**
     * 移除加载动画
     * @param {Element} container - 容器元素
     */
    removeLoadingAnimation(container) {
        if (!container) return;

        const loadingElement = container.querySelector('.loading-animation');
        if (loadingElement) {
            loadingElement.style.opacity = '0';
            setTimeout(() => {
                if (loadingElement.parentNode) {
                    loadingElement.parentNode.removeChild(loadingElement);
                }
            }, 300);
        }
    }

    /**
     * 高亮显示元素
     * @param {string} elementId - 元素ID
     * @param {number} duration - 高亮持续时间
     */
    highlightElement(elementId, duration = 2000) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const originalBackground = element.style.background;
        element.style.background = 'rgba(255, 193, 7, 0.3)';
        element.style.transition = 'background 0.3s ease';

        setTimeout(() => {
            element.style.background = originalBackground;
        }, duration);
    }

    /**
     * 添加脉冲动画到指定元素
     * @param {string} elementId - 元素ID
     * @param {number} duration - 动画持续时间
     */
    addPulseAnimation(elementId, duration = 3000) {
        const element = document.getElementById(elementId);
        if (!element) return;

        element.style.animation = this.animations.pulse;

        setTimeout(() => {
            element.style.animation = '';
        }, duration);
    }

    /**
     * 平滑滚动到指定元素
     * @param {string} elementId - 元素ID
     * @param {number} offset - 滚动偏移量
     */
    smoothScrollTo(elementId, offset = 0) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    }
}

// 添加必要的CSS动画到页面
const animationStyles = `
<style>
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
    20%, 40%, 60%, 80% { transform: translateX(5px); }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideInRight {
    from { transform: translateX(30px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes bounceIn {
    0% { transform: scale(0.3); opacity: 0; }
    50% { transform: scale(1.05); }
    70% { transform: scale(0.9); }
    100% { transform: scale(1); opacity: 1; }
}

.loading-animation {
    text-align: center;
    padding: 20px;
    transition: opacity 0.3s ease;
}

.loading-spinner {
    border: 3px solid #f3f3f3;
    border-radius: 50%;
    border-top: 3px solid #3b82f6;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
    margin: 0 auto 10px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.loading-message {
    color: #6c757d;
    font-size: 14px;
}
</style>
`;

// 在页面加载时添加动画样式
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        document.head.insertAdjacentHTML('beforeend', animationStyles);
    });
} else {
    document.head.insertAdjacentHTML('beforeend', animationStyles);
}