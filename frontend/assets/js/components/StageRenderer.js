/**
 * 阶段渲染器 - 负责渲染各个搜索阶段的详细信息
 * 遵循项目规范：专业界面，不使用emoji，注重逻辑展示
 */
class StageRenderer {
    constructor() {
        this.initialized = false;
        this.dataFormatter = null;
        
        // 安全地初始化DataFormatter
        try {
            if (window.DataFormatter && typeof window.DataFormatter === 'function') {
                this.dataFormatter = new window.DataFormatter();
            } else if (window.DataFormatter && typeof window.DataFormatter === 'object') {
                this.dataFormatter = window.DataFormatter;
            }
        } catch (error) {
            console.warn('⚠️ DataFormatter初始化失败:', error);
            this.dataFormatter = null;
        }
        
        this.initialized = true;
        console.log('✅ StageRenderer构造函数完成');
    }

    /**
     * 初始化渲染器（保持向后兼容）
     */
    init() {
        // 这个方法保持向后兼容，但实际初始化在构造函数中完成
        if (!this.initialized) {
            this.constructor();
        }
        console.log('StageRenderer: 初始化完成');
    }

    /**
     * 渲染阶段1: LLM问题分类
     * @param {Object} classTrace - 分类阶段的trace数据
     * @returns {string} 渲染的HTML内容
     */
    renderStage1(classTrace) {
        if (!classTrace || !classTrace.output_data) {
            return '<div class="text-muted">等待分类数据...</div>';
        }

        const classData = classTrace.output_data;
        const inputData = classTrace.input_data || {};
        const debugInfo = classTrace.debug_info || {};
        const confidence = (classData.confidence * 100).toFixed(1);
        const isLegal = classData.is_criminal_law;

        return `
            <div class="stage-analysis-card">
                <div class="analysis-header">
                    <h6>LLM问题分类详情</h6>
                    <div class="analysis-badges">
                        <div class="badge-group">
                            <span class="classification-badge ${isLegal ? 'legal-positive' : 'legal-negative'}">
                                <i class="fas ${isLegal ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                                ${isLegal ? '刑法相关' : '非刑法问题'}
                            </span>
                        </div>
                    </div>
                </div>

                <div class="analysis-content">
                    <!-- 决策结果显示 -->
                    <div class="decision-result-simple">
                        <div class="decision-display">
                            <div class="decision-main">
                                <div class="decision-icon ${isLegal ? 'positive' : 'negative'}">
                                    ${isLegal ? '<span style="font-size: 24px;">✅</span>' : '<span style="font-size: 24px;">❌</span>'}
                                </div>
                                <div class="decision-text">
                                    ${isLegal ? '确认：属于刑事法律问题' : '判定：非刑事法律问题'}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- LLM分析思路 -->
                    ${classData.reasoning ? `
                        <div class="thinking-process">
                            <h7>LLM分析思路</h7>
                            <div class="reasoning-box">
                                <div class="reasoning-text">${classData.reasoning}</div>
                            </div>
                        </div>
                    ` : ''}

                    <!-- 犯罪指标分析 -->
                    ${classData.crime_indicators ? `
                        <div class="crime-indicators">
                            <h7>智能犯罪指标检测</h7>
                            <div class="indicators-detail">
                                ${this.renderCrimeIndicators(classData.crime_indicators)}
                            </div>
                        </div>
                    ` : ''}

                    <!-- 技术详情 -->
                    <div class="technical-details">
                        <h7>技术详情</h7>
                        <div class="tech-info-grid-optimized">
                            <!-- 第一行：核心信息 -->
                            <div class="tech-row">
                                <div class="tech-info-item primary">
                                    <div class="info-label">LLM模型</div>
                                    <div class="info-value model-name">${debugInfo.llm_model || '智能分析'}</div>
                                </div>
                                <div class="tech-info-item primary">
                                    <div class="info-label">处理时间</div>
                                    <div class="info-value processing-time">${Math.round(classTrace.processing_time_ms || 0)}ms</div>
                                </div>
                                <div class="tech-info-item primary">
                                    <div class="info-label">分析方法</div>
                                    <div class="info-value method-name">语义理解+规则匹配</div>
                                </div>
                                <div class="tech-info-item primary">
                                    <div class="info-label">状态</div>
                                    <div class="info-value status-${classTrace.status}">${this.getStatusText(classTrace.status)}</div>
                                </div>
                            </div>

                            <!-- 第二行：Token信息 -->
                            <div class="tech-row secondary">
                                <div class="tech-info-item secondary">
                                    <div class="info-label">提示词Tokens</div>
                                    <div class="info-value">${debugInfo.prompt_tokens || 0}</div>
                                </div>
                                <div class="tech-info-item secondary">
                                    <div class="info-label">回复Tokens</div>
                                    <div class="info-value">${debugInfo.response_tokens || 0}</div>
                                </div>
                                <div class="tech-info-item secondary">
                                    <div class="info-label">LLM响应时间</div>
                                    <div class="info-value processing-time">${Math.round(debugInfo.llm_response_time_ms || 0)}ms</div>
                                </div>
                                <div class="tech-info-item secondary">
                                    <div class="info-label">配置温度</div>
                                    <div class="info-value">${debugInfo.config_temperature || 0.1}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 渲染阶段2: 结构化信息提取
     * @param {Object} extractTrace - 提取阶段的trace数据
     * @returns {string} 渲染的HTML内容
     */
    renderStage2(extractTrace) {
        if (!extractTrace || !extractTrace.output_data) {
            return '<div class="text-muted">等待提取数据...</div>';
        }

        const extractData = extractTrace.output_data;
        const debugInfo = extractTrace.debug_info || {};
        const crimes = extractData.identified_crimes || [];
        const keywords = extractData.bm25_keywords || [];

        // 🚨 临时调试：输出接收到的数据 - 完成调试后可删除
        // console.log('🔍 Stage2 Debug - extractData keys:', Object.keys(extractData));
        // console.log('🔍 Stage2 Debug - query2doc_enhanced:', extractData.query2doc_enhanced);
        // console.log('🔍 Stage2 Debug - hyde_hypothetical:', extractData.hyde_hypothetical);
        // console.log('🔍 Stage2 Debug - full extractData:', extractData);

        return `
            <div class="stage-analysis-card">
                <div class="analysis-header">
                    <h6>结构化信息提取详情</h6>
                    <div class="analysis-badges">
                        <span class="badge bg-primary">${crimes.length} 个罪名</span>
                        <span class="badge bg-info">${keywords.length} 个关键词</span>
                    </div>
                </div>

                <div class="analysis-content">
                    <!-- Query2doc语义增强 -->
                    ${extractData.query2doc_enhanced ? `
                        <div class="enhancement-section">
                            <h7>Query2doc语义增强</h7>
                            <div class="enhancement-content">
                                <div class="enhancement-box query2doc">
                                    <div class="enhancement-header">
                                        <span class="enhancement-badge">AI语义扩展</span>
                                        <span class="enhancement-length">${extractData.query2doc_enhanced.length} 字符</span>
                                    </div>
                                    <div class="enhancement-text">
                                        ${extractData.query2doc_enhanced.length > 200 ?
                                            extractData.query2doc_enhanced.substring(0, 200) + '...' :
                                            extractData.query2doc_enhanced}
                                    </div>
                                    ${extractData.query2doc_enhanced.length > 200 ? `
                                        <button class="btn btn-sm btn-link expand-btn" onclick="toggleEnhancementText(this, '${this.escapeHtml(extractData.query2doc_enhanced)}')">
                                            展开全文
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    ` : ''}

                    <!-- HyDE假设回答 -->
                    ${extractData.hyde_hypothetical ? `
                        <div class="enhancement-section">
                            <h7>HyDE假设回答生成</h7>
                            <div class="enhancement-content">
                                <div class="enhancement-box hyde">
                                    <div class="enhancement-header">
                                        <span class="enhancement-badge hyde-badge">假设回答</span>
                                        <span class="enhancement-length">${extractData.hyde_hypothetical.length} 字符</span>
                                    </div>
                                    <div class="enhancement-text">
                                        ${extractData.hyde_hypothetical.length > 200 ?
                                            extractData.hyde_hypothetical.substring(0, 200) + '...' :
                                            extractData.hyde_hypothetical}
                                    </div>
                                    ${extractData.hyde_hypothetical.length > 200 ? `
                                        <button class="btn btn-sm btn-link expand-btn" onclick="toggleEnhancementText(this, '${this.escapeHtml(extractData.hyde_hypothetical)}')">
                                            展开全文
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    ` : ''}

                    <!-- 罪名识别结果详情 -->
                    ${crimes.length > 0 ? `
                        <div class="extraction-section">
                            <h7>AI识别罪名详情</h7>
                            <div class="crimes-detailed-container">
                                ${crimes.map((crime, index) => {
                                    const confidence = crime.confidence ? (crime.confidence * 100).toFixed(1) : null;
                                    const relevance = crime.relevance ? (crime.relevance * 100).toFixed(1) : null;
                                    return `
                                        <div class="crime-detailed-card">
                                            <div class="crime-header">
                                                <div class="crime-rank">#${index + 1}</div>
                                                <div class="crime-name-detailed">${crime.crime_name || crime}</div>
                                                ${confidence || relevance ? `
                                                    <div class="crime-scores">
                                                        ${confidence ? `
                                                            <span class="confidence-score" title="识别置信度">
                                                                ${confidence}%
                                                            </span>
                                                        ` : ''}
                                                        ${relevance ? `
                                                            <span class="relevance-score" title="相关度">
                                                                ${relevance}%
                                                            </span>
                                                        ` : ''}
                                                    </div>
                                                ` : ''}
                                            </div>
                                            ${crime.article_number ? `
                                                <div class="crime-article">
                                                    <span class="article-label">相关法条:</span>
                                                    <span class="article-number">${crime.article_number}</span>
                                                </div>
                                            ` : ''}
                                            ${crime.description ? `
                                                <div class="crime-description">
                                                    <span class="desc-label">描述:</span>
                                                    <span class="desc-text">${crime.description}</span>
                                                </div>
                                            ` : ''}
                                            ${crime.reasoning ? `
                                                <div class="crime-reasoning">
                                                    <span class="reasoning-label">识别依据:</span>
                                                    <div class="reasoning-text">${crime.reasoning}</div>
                                                </div>
                                            ` : ''}
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- BM25关键词权重分析 -->
                    ${keywords.length > 0 ? `
                        <div class="extraction-section">
                            <h7>BM25关键词权重分析</h7>
                            <div class="keywords-weight-container">
                                <div class="keywords-grid">
                                    ${keywords.map((kw, index) => {
                                        if (typeof kw === 'object' && kw.keyword && kw.weight !== undefined) {
                                            const weight = (kw.weight * 100).toFixed(1);
                                            const weightLevel = this.getWeightLevel(kw.weight);
                                            return `
                                                <div class="keyword-weight-item ${weightLevel}">
                                                    <div class="keyword-text">${kw.keyword}</div>
                                                    <div class="keyword-weight">
                                                        <div class="weight-bar">
                                                            <div class="weight-fill" style="width: ${weight}%"></div>
                                                        </div>
                                                        <span class="weight-value">${weight}%</span>
                                                    </div>
                                                    <div class="keyword-rank">排名 #${index + 1}</div>
                                                </div>
                                            `;
                                        }
                                        return `
                                            <div class="keyword-weight-item basic">
                                                <div class="keyword-text">${kw}</div>
                                                <div class="keyword-weight">
                                                    <span class="weight-value">基础权重</span>
                                                </div>
                                                <div class="keyword-rank">排名 #${index + 1}</div>
                                            </div>
                                        `;
                                    }).join('')}
                                </div>

                                <!-- 权重统计 -->
                                <div class="weight-stats">
                                    <div class="stat-item">
                                        <span class="stat-label">高权重词:</span>
                                        <span class="stat-value">${keywords.filter(kw => kw.weight >= 0.8).length}</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-label">中权重词:</span>
                                        <span class="stat-value">${keywords.filter(kw => kw.weight >= 0.6 && kw.weight < 0.8).length}</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-label">平均权重:</span>
                                        <span class="stat-value">${keywords.length > 0 ? (keywords.reduce((sum, kw) => sum + (kw.weight || 0), 0) / keywords.length * 100).toFixed(1) : 0}%</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ` : ''}


                    <!-- 提取过程摘要 -->
                    <div class="extraction-summary">
                        <h7>提取过程摘要</h7>
                        <div class="summary-grid">
                            <div class="summary-item">
                                <div class="summary-icon">
                                    <i class="fas fa-gavel"></i>
                                </div>
                                <div class="summary-content">
                                    <div class="summary-title">罪名识别</div>
                                    <div class="summary-desc">${crimes.length > 0 ? `识别到${crimes.length}个相关罪名` : '未识别到明确罪名'}</div>
                                </div>
                            </div>
                            <div class="summary-item">
                                <div class="summary-icon">
                                    <i class="fas fa-key"></i>
                                </div>
                                <div class="summary-content">
                                    <div class="summary-title">关键词提取</div>
                                    <div class="summary-desc">BM25算法提取${keywords.length}个关键词</div>
                                </div>
                            </div>
                            ${extractData.query2doc_enhanced ? `
                            <div class="summary-item">
                                <div class="summary-icon">
                                    <i class="fas fa-magic"></i>
                                </div>
                                <div class="summary-content">
                                    <div class="summary-title">Query2doc增强</div>
                                    <div class="summary-desc">语义增强${extractData.query2doc_enhanced.length}字符</div>
                                </div>
                            </div>
                            ` : ''}
                            ${extractData.hyde_hypothetical ? `
                            <div class="summary-item">
                                <div class="summary-icon">
                                    <i class="fas fa-lightbulb"></i>
                                </div>
                                <div class="summary-content">
                                    <div class="summary-title">HyDE假设回答</div>
                                    <div class="summary-desc">生成假设回答${extractData.hyde_hypothetical.length}字符</div>
                                </div>
                            </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- 技术详情 -->
                    <div class="technical-details">
                        <h7>技术详情</h7>
                        <div class="tech-info-grid">
                            <div class="tech-info-item">
                                <div class="info-label">提取方法</div>
                                <div class="info-value method-name">LLM + NLP混合</div>
                            </div>
                            <div class="tech-info-item">
                                <div class="info-label">处理时间</div>
                                <div class="info-value processing-time">${Math.round(extractTrace.processing_time_ms || 0)}ms</div>
                            </div>
                            <div class="tech-info-item">
                                <div class="info-label">罪名数量</div>
                                <div class="info-value">${crimes.length}</div>
                            </div>
                            <div class="tech-info-item">
                                <div class="info-label">关键词数量</div>
                                <div class="info-value">${keywords.length}</div>
                            </div>
                            <div class="tech-info-item">
                                <div class="info-label">状态</div>
                                <div class="info-value status-${extractTrace.status}">${this.getStatusText(extractTrace.status)}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 获取权重等级
     * @param {number} weight - 权重值 (0-1)
     * @returns {string} 权重等级
     */
    getWeightLevel(weight) {
        if (weight >= 0.8) return 'high';
        if (weight >= 0.6) return 'medium';
        return 'low';
    }

    /**
     * 渲染阶段3: 路由决策
     * @param {Object} routingTrace - 路由阶段的trace数据
     * @returns {string} 渲染的HTML内容
     */
    renderStage3(routingTrace) {
        if (!routingTrace || !routingTrace.output_data) {
            return '<div class="text-muted">等待路由数据...</div>';
        }

        const routingData = routingTrace.output_data;
        const selectedPaths = routingData.selected_paths || [];
        const availablePaths = routingData.available_paths || [];
        const confidence = routingData.routing_confidence || 0;

        return `
            <div class="stage-analysis-card">
                <div class="analysis-header">
                    <h6>智能路由决策详情</h6>
                    <div class="analysis-badges">
                        <div class="badge-group">
                            <span class="routing-paths-badge">
                                <i class="fas fa-route"></i>
                                ${selectedPaths.length} 条路径
                            </span>
                            <span class="routing-algorithm-badge">
                                <i class="fas fa-brain"></i>
                                智能路由
                            </span>
                        </div>
                    </div>
                </div>

                <div class="analysis-content">
                    <!-- 路径选择结果 -->
                    <div class="routing-reasoning">
                        <h7>选择的搜索路径</h7>
                        <div class="routing-paths-grid-optimized">
                            ${selectedPaths.map(path => {
                                const displayName = this.getPathDisplayName(path);
                                return `
                                    <div class="path-status-card active">
                                        <div class="path-icon">
                                            <i class="fas fa-check-circle"></i>
                                        </div>
                                        <div class="path-name">${displayName}</div>
                                        <div class="path-status">已选择</div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>

                    <!-- 未选择的路径 -->
                    ${availablePaths.length > selectedPaths.length ? `
                        <div class="routing-reasoning">
                            <h7>未选择的路径</h7>
                            <div class="routing-paths-grid-optimized">
                                ${availablePaths.filter(path => !selectedPaths.includes(path)).map(path => {
                                    const displayName = this.getPathDisplayName(path);
                                    return `
                                        <div class="path-status-card inactive">
                                            <div class="path-icon">
                                                <i class="fas fa-times-circle"></i>
                                            </div>
                                            <div class="path-name">${displayName}</div>
                                            <div class="path-status">已跳过</div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- 决策推理 -->
                    ${routingData.reasoning ? `
                        <div class="thinking-process">
                            <h7>决策推理</h7>
                            <div class="reasoning-box">
                                ${routingData.reasoning}
                            </div>
                        </div>
                    ` : ''}

                    <!-- 技术详情 -->
                    <div class="technical-details">
                        <h7>技术详情</h7>
                        <div class="tech-info-grid">
                            <div class="tech-info-item">
                                <div class="info-label">路由算法</div>
                                <div class="info-value method-name">智能策略选择</div>
                            </div>
                            <div class="tech-info-item">
                                <div class="info-label">处理时间</div>
                                <div class="info-value processing-time">${Math.round(routingTrace.processing_time_ms || 0)}ms</div>
                            </div>
                            <div class="tech-info-item">
                                <div class="info-label">并发路径</div>
                                <div class="info-value">${selectedPaths.length}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 渲染阶段4: 多路搜索执行
     * @param {Object} searches - 搜索结果数据
     * @returns {string} 渲染的HTML内容
     */
    renderStage4(searches) {
        if (!searches || Object.keys(searches).length === 0) {
            return '<div class="text-muted">等待搜索数据...</div>';
        }

        return `
            <div class="stage-analysis-card">
                <div class="analysis-header">
                    <h6>多路搜索执行详情</h6>
                    <div class="analysis-badges">
                        <span class="badge bg-primary">${Object.keys(searches).length} 个模块</span>
                        <span class="badge bg-success">${Object.values(searches).filter(s => s.status === 'success').length} 个成功</span>
                    </div>
                </div>

                <div class="analysis-content">
                    <!-- 模块概览 -->
                    <div class="modules-overview-grid">
                        ${Object.entries(searches).map(([searchPath, moduleData]) => {
                            const displayName = this.getPathDisplayName(searchPath);
                            const articlesCount = moduleData.output_data?.articles?.length || 0;
                            const casesCount = moduleData.output_data?.cases?.length || 0;
                            const processingTime = Math.round(moduleData.processing_time_ms || 0);

                            return `
                                 <div class="module-overview-card ${moduleData.status}"
                                      data-module-path="${searchPath}">
                                     <div class="module-header">
                                        <div class="module-status-icon">
                                            ${moduleData.status === 'success' ? '<i class="fas fa-check-circle text-success"></i>' : '<i class="fas fa-times-circle text-danger"></i>'}
                                        </div>
                                        <div class="module-name">${displayName}</div>
                                        </div>
                                    <div class="module-metrics">
                                        <div class="metric-item">
                                            <div class="metric-label">法条</div>
                                            <div class="metric-value">${articlesCount}</div>
                                        </div>
                                        <div class="metric-item">
                                            <div class="metric-label">案例</div>
                                            <div class="metric-value">${casesCount}</div>
                                        </div>
                                        <div class="metric-item">
                                            <div class="metric-label">耗时</div>
                                            <div class="metric-value">${processingTime}ms</div>
                                        </div>
                                    </div>
                                    ${moduleData.error_message ? `
                                        <div class="module-error">
                                            <i class="fas fa-exclamation-triangle"></i>
                                            ${moduleData.error_message}
                                        </div>
                                    ` : ''}
                                </div>
                            `;
                        }).join('')}
                    </div>

                    <!-- 搜索统计 -->
                    <div class="technical-details">
                        <h7>搜索统计</h7>
                        <div class="tech-info-grid">
                            <div class="tech-info-item">
                                <div class="info-label">总模块数</div>
                                <div class="info-value">${Object.keys(searches).length}</div>
                            </div>
                            <div class="tech-info-item">
                                <div class="info-label">成功模块</div>
                                <div class="info-value status-success">${Object.values(searches).filter(s => s.status === 'success').length}</div>
                            </div>
                            <div class="tech-info-item">
                                <div class="info-label">失败模块</div>
                                <div class="info-value status-error">${Object.values(searches).filter(s => s.status === 'error').length}</div>
                            </div>
                            <div class="tech-info-item">
                                <div class="info-label">总耗时</div>
                                <div class="info-value processing-time">${Math.round(Object.values(searches).reduce((sum, s) => sum + (s.processing_time_ms || 0), 0))}ms</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 渲染阶段5: 结果融合与AI回答
     * @param {Object} fusionTrace - 融合阶段的trace数据
     * @returns {string} 渲染的HTML内容
     */
    renderStage5(fusionTrace) {
        if (!fusionTrace || !fusionTrace.output_data) {
            return '<div class="text-muted">等待融合数据...</div>';
        }

        const fusionData = fusionTrace.output_data;
        const finalAnswer = fusionData.final_answer || '';
        const finalResults = fusionData.final_results || [];
        const confidence = fusionData.final_confidence || 0;
        const algorithm = fusionData.fusion_algorithm || 'Enhanced RRF';

        return `
            <div class="stage-analysis-card">
                <div class="analysis-header">
                    <h6>结果融合与AI回答详情</h6>
                    <div class="analysis-badges">
                        <div class="badge-group">
                            <span class="fusion-algorithm-badge">
                                <i class="fas fa-atom"></i>
                                ${algorithm}
                            </span>
                            <span class="results-count-badge">
                                <i class="fas fa-list"></i>
                                ${finalResults.length} 个结果
                            </span>
                        </div>
                    </div>
                </div>

                <div class="analysis-content">
                    <!-- AI生成的回答 -->
                    ${finalAnswer ? `
                        <div class="extraction-section">
                            <h7>AI生成回答</h7>
                            <div class="ai-answer-container">
                                <div class="answer-content expanded markdown-content" id="ai-answer-content">
                                    ${this.renderMarkdown(finalAnswer)}
                                </div>
                                ${finalAnswer.length > 200 ? `
                                    <button class="btn btn-sm btn-outline-secondary mt-2 toggle-answer-btn" id="toggle-answer-btn" data-action="toggle-answer">
                                        <i class="fas fa-chevron-up me-1" id="toggle-answer-icon"></i>
                                        <span id="toggle-answer-text">收起回答</span>
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    ` : ''}

                    <!-- 融合结果列表 -->
                    ${finalResults.length > 0 ? `
                        <div class="extraction-section">
                            <h7>融合后的最终结果</h7>
                            <div class="fusion-results-container">
                                ${finalResults.slice(0, 10).map((result, index) => {
                                    const rank = index + 1;
                                    const type = result.type || 'unknown';
                                    const title = result.title || result.id || `结果${rank}`;
                                    const similarity = ((result.similarity || 0) * 100).toFixed(1);
                                    const fusionScore = result.fusion_score ?
                                                      (result.fusion_score * 100).toFixed(1) :
                                                      similarity;

                                    return `
                                        <div class="fusion-result-item"
                                             onclick="selectFusionResult(${rank}, '${type}', ${JSON.stringify(result).replace(/"/g, '&quot;')})"
                                             style="cursor: pointer;">
                                            <div class="result-header">
                                                <div class="result-rank">#${rank}</div>
                                                <div class="result-type-badge ${type}">
                                                    ${type === 'article' ? '法条' : '案例'}
                                                </div>
                                                <div class="result-title">${title}</div>
                                                <div class="result-scores">
                                                    <span class="fusion-score" title="融合分数">
                                                        ${fusionScore}%
                                                    </span>
                                                    <span class="similarity-score" title="原始相似度">
                                                        ${similarity}%
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- 融合算法详情 -->
                    <div class="technical-details">
                        <h7>融合技术详情</h7>
                        <div class="tech-info-grid tech-info-grid-6">
                            <div class="tech-info-item tech-info-item-compact">
                                <div class="info-label">融合算法</div>
                                <div class="info-value method-name">${algorithm}</div>
                            </div>
                            <div class="tech-info-item tech-info-item-compact">
                                <div class="info-label">处理时间</div>
                                <div class="info-value processing-time">${Math.round(fusionTrace.processing_time_ms || 0)}ms</div>
                            </div>
                            <div class="tech-info-item tech-info-item-compact">
                                <div class="info-label">结果数量</div>
                                <div class="info-value">${finalResults.length}</div>
                            </div>
                            <div class="tech-info-item tech-info-item-compact">
                                <div class="info-label">回答长度</div>
                                <div class="info-value">${finalAnswer.length} 字符</div>
                            </div>
                            <div class="tech-info-item tech-info-item-compact">
                                <div class="info-label">输入源</div>
                                <div class="info-value">${fusionData.input_sources_count || 0}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 融合结果详情面板（隐藏状态） -->
            <div id="fusion-detail-panel" class="search-pipeline" style="display: none;">
                <div class="panel-header">
                    <h5>融合结果详细信息</h5>
                    <button class="btn btn-sm btn-secondary" onclick="hideFusionDetails()">
                        <i class="fas fa-times"></i> 关闭
                    </button>
                </div>
                <div id="fusion-detail-content"></div>
            </div>
        `;
    }

    /**
     * 渲染犯罪指标
     * @param {Object} indicators - 犯罪指标数据
     * @returns {string} HTML内容
     */
    renderCrimeIndicators(indicators) {
        if (!indicators) return '';

        let html = '';

        if (indicators.violence_indicators && indicators.violence_indicators.length > 0) {
            html += `
                <div class="indicator-category">
                    <div class="indicator-title violence">暴力指标</div>
                    <div class="indicator-items">
                        ${indicators.violence_indicators.map(indicator =>
                            `<div class="indicator-tag violence">${indicator}</div>`
                        ).join('')}
                    </div>
                </div>
            `;
        }

        if (indicators.legal_terms && indicators.legal_terms.length > 0) {
            html += `
                <div class="indicator-category">
                    <div class="indicator-title legal">法律术语</div>
                    <div class="indicator-items">
                        ${indicators.legal_terms.map(term =>
                            `<div class="indicator-tag legal">${term}</div>`
                        ).join('')}
                    </div>
                </div>
            `;
        }

        if (indicators.severity_indicators && indicators.severity_indicators.length > 0) {
            html += `
                <div class="indicator-category">
                    <div class="indicator-title severity">严重程度</div>
                    <div class="indicator-items">
                        ${indicators.severity_indicators.map(indicator =>
                            `<div class="indicator-tag severity">${indicator}</div>`
                        ).join('')}
                    </div>
                </div>
            `;
        }

        return html;
    }

    /**
     * 获取路径显示名称
     * @param {string} path - 路径名
     * @returns {string} 显示名称
     */
    getPathDisplayName(path) {
        const pathNames = {
            // 完整的模块名称映射 (与后端保持一致)
            'knowledge_graph_search': '知识图谱搜索',
            'query2doc_enhanced_search': 'Query2doc增强搜索', 
            'hyde_enhanced_search': 'HyDE增强搜索',
            'bm25_hybrid_search': 'BM25混合搜索',
            'basic_semantic_search': '基础语义搜索',
            'llm_enhanced_search': 'LLM增强搜索',
            'general_ai_search': '通用AI搜索',
            
            // 简化版本名称映射 (向后兼容)
            'knowledge_graph': '知识图谱搜索',
            'query2doc': 'Query2doc增强搜索',
            'hyde': 'HyDE增强搜索',
            'bm25_hybrid': 'BM25混合搜索',
            'basic_semantic': '基础语义搜索',
            'llm_enhanced': 'LLM增强搜索',
            'general_ai': '通用AI搜索'
        };
        
        // 先尝试完整匹配
        if (pathNames[path]) {
            return pathNames[path];
        }
        
        // 尝试匹配简化版本（去掉_search后缀）
        const simplifiedPath = path.replace('_search', '');
        if (pathNames[simplifiedPath]) {
            return pathNames[simplifiedPath];
        }
        
        // 尝试匹配完整版本（添加_search后缀）
        const fullPath = path.endsWith('_search') ? path : path + '_search';
        if (pathNames[fullPath]) {
            return pathNames[fullPath];
        }
        
        // 都没找到，返回原始路径
        return path;
    }

    /**
     * 获取状态文本
     * @param {string} status - 状态
     * @returns {string} 状态文本
     */
    getStatusText(status) {
        const statusTexts = {
            'success': '成功',
            'error': '失败',
            'pending': '等待中',
            'running': '运行中',
            'skipped': '已跳过'
        };
        return statusTexts[status] || status;
    }

    /**
     * HTML转义
     * @param {string} text - 需要转义的文本
     * @returns {string} 转义后的文本
     */
    escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /**
     * 格式化置信度显示
     * @param {number} confidence - 置信度（0-1）
     * @returns {string} 格式化后的置信度
     */
    formatConfidence(confidence) {
        if (typeof confidence !== 'number') return '0%';
        return `${(confidence * 100).toFixed(1)}%`;
    }

    /**
     * 获取置信度等级样式类
     * @param {number} confidence - 置信度（0-1）
     * @returns {string} 样式类名
     */
    getConfidenceClass(confidence) {
        const percent = confidence * 100;
        if (percent >= 90) return 'confidence-very-high';
        if (percent >= 80) return 'confidence-high';
        if (percent >= 60) return 'confidence-medium';
        return 'confidence-low';
    }

    /**
     * 渲染Markdown文本为HTML
     * @param {string} markdownText - Markdown格式的文本
     * @returns {string} 渲染后的HTML
     */
    renderMarkdown(markdownText) {
        if (!markdownText) return '';

        try {
            // 检查marked库是否已加载
            if (typeof marked !== 'undefined') {
                // 配置marked选项
                marked.setOptions({
                    breaks: true,        // 支持换行符转换为<br>
                    gfm: true,          // 启用GitHub风格的Markdown
                    sanitize: false,    // 不清理HTML（我们信任AI回答内容）
                    smartLists: true,   // 智能列表处理
                    smartypants: true   // 智能标点符号
                });

                return marked.parse(markdownText);
            } else {
                // marked库未加载，使用简单的文本处理
                return this.simpleMarkdownRender(markdownText);
            }
        } catch (error) {
            console.warn('Markdown渲染失败，回退到简单处理:', error);
            return this.simpleMarkdownRender(markdownText);
        }
    }

    /**
     * 简单的Markdown渲染（fallback）
     * @param {string} text - 文本内容
     * @returns {string} 处理后的HTML
     */
    simpleMarkdownRender(text) {
        if (!text) return '';

        return text
            // 处理代码块
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            // 处理内联代码
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // 处理粗体
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/__(.*?)__/g, '<strong>$1</strong>')
            // 处理斜体
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/_(.*?)_/g, '<em>$1</em>')
            // 处理链接
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
            // 处理标题
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            // 处理列表
            .replace(/^\* (.+)$/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            // 处理换行
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(.*)$/gm, '<p>$1</p>')
            // 清理多余的空段落
            .replace(/<p><\/p>/g, '')
            .replace(/<p>(<h[1-6]>.*<\/h[1-6]>)<\/p>/g, '$1')
            .replace(/<p>(<ul>.*<\/ul>)<\/p>/g, '$1')
            .replace(/<p>(<pre>.*<\/pre>)<\/p>/g, '$1');
    }

    /**
     * 渲染搜索模块详细信息
     * @param {string} moduleName - 模块名称
     * @param {Object} moduleData - 模块数据
     * @returns {string} HTML内容
     */
    renderModuleDetails(moduleName, moduleData) {
        if (!moduleData) {
            return '<div class="text-muted">模块数据不可用</div>';
        }

        const displayName = this.getPathDisplayName(moduleName);
        const articles = moduleData.output_data?.articles || [];
        const cases = moduleData.output_data?.cases || [];
        const searchMeta = moduleData.output_data?.search_meta || {};
        const processingTime = Math.round(moduleData.processing_time_ms || 0);

        return `
            <div class="module-details-container">
                <div class="module-details-header">
                    <div class="details-title">
                        <h5>${displayName} - 详细结果</h5>
                        <span class="module-status-badge ${moduleData.status}">${moduleData.status === 'success' ? '成功' : '失败'}</span>
                    </div>
                    <div class="details-meta">
                        <span class="meta-item">
                            <i class="fas fa-clock"></i>
                            处理时间: ${processingTime}ms
                        </span>
                    </div>
                </div>

                <div class="module-details-content">
                    <!-- 搜索元数据 -->
                    ${Object.keys(searchMeta).length > 0 ? `
                        <div class="detail-section">
                            <h6>搜索配置</h6>
                            <div class="search-meta-grid">
                                ${Object.entries(searchMeta).map(([key, value]) => `
                                    <div class="meta-item-detail">
                                        <div class="meta-label">${this.formatMetaLabel(key)}</div>
                                        <div class="meta-value">${this.formatMetaValue(value)}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- 法条结果 -->
                    ${articles.length > 0 ? `
                        <div class="detail-section">
                            <h6>相关法条 (${articles.length}条)</h6>
                            <div class="results-list">
                                ${articles.map((article, index) => `
                                    <div class="result-item">
                                        <div class="result-header">
                                            <div class="result-rank">#${index + 1}</div>
                                            <div class="result-title">${article.title || article.id}</div>
                                            <div class="result-similarity">
                                                相似度: ${((article.similarity || 0) * 100).toFixed(1)}%
                                            </div>
                                        </div>
                                        <div class="result-content">
                                            ${article.content ? (article.content.length > 200 ?
                                                article.content.substring(0, 200) + '...' :
                                                article.content) : '内容不可用'}
                                        </div>
                                        ${article.source ? `
                                            <div class="result-source">
                                                <i class="fas fa-tag"></i>
                                                来源: ${article.source}
                                            </div>
                                        ` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : '<div class="no-results">未找到相关法条</div>'}

                    <!-- 案例结果 -->
                    ${cases.length > 0 ? `
                        <div class="detail-section">
                            <h6>相关案例 (${cases.length}个)</h6>
                            <div class="results-list">
                                ${cases.map((case_item, index) => `
                                    <div class="result-item">
                                        <div class="result-header">
                                            <div class="result-rank">#${index + 1}</div>
                                            <div class="result-title">${case_item.title || case_item.id}</div>
                                            <div class="result-similarity">
                                                相似度: ${((case_item.similarity || 0) * 100).toFixed(1)}%
                                            </div>
                                        </div>
                                        <div class="result-content">
                                            ${case_item.content ? (case_item.content.length > 200 ?
                                                case_item.content.substring(0, 200) + '...' :
                                                case_item.content) : '内容不可用'}
                                        </div>
                                        ${case_item.sentence_result ? `
                                            <div class="sentence-result">
                                                <i class="fas fa-gavel"></i>
                                                判决结果: ${case_item.sentence_result}
                                            </div>
                                        ` : ''}
                                        ${case_item.source ? `
                                            <div class="result-source">
                                                <i class="fas fa-tag"></i>
                                                来源: ${case_item.source}
                                            </div>
                                        ` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : '<div class="no-results">未找到相关案例</div>'}

                    <!-- 调试信息 -->
                    ${moduleData.debug_info && Object.keys(moduleData.debug_info).length > 0 ? `
                        <div class="detail-section debug-info">
                            <h6>调试信息</h6>
                            <div class="debug-content">
                                ${Object.entries(moduleData.debug_info).map(([key, value]) => `
                                    <div class="debug-item">
                                        <span class="debug-key">${key}:</span>
                                        <span class="debug-value">${JSON.stringify(value)}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * 格式化元数据标签
     * @param {string} key - 元数据键
     * @returns {string} 格式化后的标签
     */
    formatMetaLabel(key) {
        const labelMap = {
            'method': '搜索方法',
            'total_results': '结果总数',
            'avg_similarity': '平均相似度',
            'enhanced_query': '增强查询',
            'hypothetical_answer': '假设回答',
            'keywords_count': '关键词数量',
            'vector_similarity_only': '仅向量相似度',
            'no_enhancement': '无增强',
            'used_enhancement': '使用增强',
            'detected_crimes': '检测到的犯罪',
            'kg_paths_used': '知识图谱路径'
        };
        return labelMap[key] || key;
    }

    /**
     * 格式化元数据值
     * @param {any} value - 元数据值
     * @returns {string} 格式化后的值
     */
    formatMetaValue(value) {
        if (typeof value === 'boolean') {
            return value ? '是' : '否';
        }
        if (typeof value === 'number' && value < 1 && value > 0) {
            return (value * 100).toFixed(1) + '%';
        }
        if (Array.isArray(value)) {
            return value.join(', ');
        }
        return String(value);
    }
}

// 添加融合结果相关的CSS样式
const stageRendererStyles = `
<style>
/* 决策图标样式 */
.decision-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    margin-bottom: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.decision-icon.positive {
    background: linear-gradient(135deg, #d4edda, #c3e6cb);
    border: 3px solid #28a745;
}

.decision-icon.negative {
    background: linear-gradient(135deg, #f8d7da, #f5c6cb);
    border: 3px solid #dc3545;
}

.decision-icon i {
    font-size: 24px;
}

/* 模块状态图标样式 */
.module-status-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    margin-bottom: 8px;
}

.module-overview-card.success .module-status-icon {
    background: linear-gradient(135deg, #d4edda, #c3e6cb);
}

.module-overview-card.error .module-status-icon {
    background: linear-gradient(135deg, #f8d7da, #f5c6cb);
}

.module-status-icon i {
    font-size: 18px;
}

/* 阶段1 优化样式 */
.badge-group {
    display: flex;
    gap: 12px;
    align-items: center;
}

.confidence-badge-enhanced {
    background: linear-gradient(135deg, #007bff, #0056b3);
    color: white;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
    display: flex;
    align-items: center;
    gap: 4px;
}

.classification-badge {
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
    /* transition: all 0.3s ease; 移除过渡动画 */
}

.classification-badge.legal-positive {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
}

.classification-badge.legal-negative {
    background: linear-gradient(135deg, #ffc107, #fd7e14);
    color: #212529;
    box-shadow: 0 2px 4px rgba(255, 193, 7, 0.3);
}

.classification-badge i {
    font-size: 14px;
}

/* 技术详情优化布局 */
.tech-info-grid-optimized {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 12px;
}

.tech-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}

.tech-row.secondary {
    padding-top: 8px;
    border-top: 1px solid #e9ecef;
}

.tech-info-item {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 12px;
    text-align: center;
    /* transition: all 0.3s ease; 移除过渡动画 */
}

.tech-info-item.primary {
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    border: 1px solid #dee2e6;
}

.tech-info-item.secondary {
    background: #ffffff;
    border: 1px solid #e9ecef;
    opacity: 0.9;
}

/* 移除技术信息项悬停动画 */

.tech-info-item .info-label {
    font-size: 11px;
    font-weight: 600;
    color: #6c757d;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

.tech-info-item .info-value {
    font-size: 14px;
    font-weight: 600;
    color: #495057;
}

.tech-info-item.primary .info-value {
    color: #212529;
    font-weight: 700;
}

.tech-info-item .info-value.model-name {
    color: #007bff;
}

.tech-info-item .info-value.processing-time {
    color: #28a745;
}

.tech-info-item .info-value.method-name {
    color: #6f42c1;
}

/* 阶段3 路由决策样式 */
.routing-paths-badge {
    background: linear-gradient(135deg, #6f42c1, #8e5ec6);
    color: white;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 2px 4px rgba(111, 66, 193, 0.3);
}

.routing-paths-badge i {
    font-size: 14px;
}

.routing-paths-grid-optimized {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-top: 12px;
}

.path-status-card {
    background: linear-gradient(145deg, #ffffff, #f8f9fa);
    border-radius: 12px;
    padding: 16px 12px;
    text-align: center;
    /* transition: all 0.3s ease; 移除过渡动画 */
    border: 1px solid #e9ecef;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* 移除路径状态卡片悬停动画 */

.path-status-card.active {
    border-color: #28a745;
    background: linear-gradient(145deg, #f8fff9, #e8f5e8);
}

.path-status-card.inactive {
    border-color: #6c757d;
    background: linear-gradient(145deg, #f8f9fa, #e9ecef);
    opacity: 0.7;
}

.path-icon {
    margin-bottom: 8px;
}

.path-status-card.active .path-icon i {
    color: #28a745;
    font-size: 18px;
}

.path-status-card.inactive .path-icon i {
    color: #6c757d;
    font-size: 18px;
}

.path-name {
    font-weight: 600;
    font-size: 14px;
    color: #212529;
    margin-bottom: 6px;
    word-break: break-word;
    line-height: 1.3;
}

.path-status {
    font-size: 11px;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 12px;
    display: inline-block;
}

.path-status-card.active .path-status {
    background: #d4edda;
    color: #155724;
}

.path-status-card.inactive .path-status {
    background: #e2e3e5;
    color: #6c757d;
}

/* 响应式布局 */
@media (max-width: 1200px) {
    .routing-paths-grid-optimized {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (max-width: 768px) {
    .routing-paths-grid-optimized {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 480px) {
    .routing-paths-grid-optimized {
        grid-template-columns: 1fr;
    }
}

/* 阶段2 罪名识别详情样式 */
.crimes-detailed-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 10px;
}

.crime-detailed-card {
    background: #fff;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;
    border-left: 4px solid #dc3545;
}

.crime-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
}

.crime-rank {
    background: #dc3545;
    color: white;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
}

.crime-name-detailed {
    flex: 1;
    font-weight: 600;
    font-size: 15px;
    color: #dc3545;
}

.crime-scores {
    display: flex;
    gap: 8px;
}

.confidence-score, .relevance-score {
    background: #e9ecef;
    color: #495057;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
}

.confidence-score {
    background: #d4edda;
    color: #155724;
}

.relevance-score {
    background: #d1ecf1;
    color: #0c5460;
}

.crime-article, .crime-description, .crime-reasoning {
    margin-top: 8px;
    font-size: 13px;
    line-height: 1.4;
}

.article-label, .desc-label, .reasoning-label {
    font-weight: 600;
    color: #6c757d;
}

.article-number {
    color: #007bff;
    font-weight: 600;
}

.desc-text {
    color: #495057;
}

.reasoning-text {
    margin-top: 4px;
    color: #495057;
    font-style: italic;
}

/* 关键词权重分析样式 */
.keywords-weight-container {
    margin-top: 10px;
}

.keywords-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 15px;
}

.keyword-weight-item {
    background: linear-gradient(145deg, #ffffff, #f8f9fa);
    padding: 16px 12px;
    border-radius: 12px;
    border: 1px solid #e9ecef;
    text-align: center;
    /* transition: all 0.3s ease; 移除过渡动画 */
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* 移除悬停动画以提升性能 */

.keyword-weight-item.high {
    border-color: #28a745;
    background: linear-gradient(145deg, #f8fff9, #e8f5e8);
}

.keyword-weight-item.medium {
    border-color: #6f42c1;
    background: linear-gradient(145deg, #faf8ff, #f3e8ff);
}

.keyword-weight-item.low {
    border-color: #ffc107;
    background: linear-gradient(145deg, #fffef8, #fff3cd);
}

.keyword-weight-item.basic {
    border-color: #6c757d;
    background: linear-gradient(145deg, #f8f9fa, #e9ecef);
}

.keyword-text {
    font-weight: 600;
    font-size: 14px;
    color: #212529;
    margin-bottom: 8px;
    word-break: break-word;
}

.keyword-weight {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 6px;
}

.weight-bar {
    height: 8px;
    background: #e9ecef;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
}

.weight-fill {
    height: 100%;
    background: linear-gradient(90deg, #28a745, #20c997);
    border-radius: 4px;
    /* transition: width 1s ease-out; 移除过渡动画 */
    position: relative;
}

.keyword-weight-item.high .weight-fill {
    background: linear-gradient(90deg, #28a745, #20c997);
}

.keyword-weight-item.medium .weight-fill {
    background: linear-gradient(90deg, #6f42c1, #8e5ec6);
}

.keyword-weight-item.low .weight-fill {
    background: linear-gradient(90deg, #ffc107, #ffb700);
}

.weight-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    /* animation: shimmer 2s infinite; 移除动画 */
}

/* 移除动画关键帧
@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
} */

.weight-value {
    font-size: 12px;
    font-weight: 600;
    color: #495057;
}

.keyword-rank {
    font-size: 11px;
    color: #6c757d;
    font-weight: 500;
}

/* 修复阶段2容器高度问题 */
.stage-analysis-card {
    min-height: auto !important;
    height: auto !important;
    overflow: visible !important;
}

.stage-details-inline {
    max-height: none !important;
    height: auto !important;
    overflow: visible !important;
}

/* 响应式布局：小屏幕时改为3列 */
@media (max-width: 1200px) {
    .keywords-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (max-width: 768px) {
    .keywords-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 480px) {
    .keywords-grid {
        grid-template-columns: 1fr;
    }
}
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

.keyword-weight-item.low {
    border-left-color: #dc3545;
    background: #fef8f8;
}

.keyword-text {
    font-weight: 600;
    font-size: 14px;
    color: #495057;
    margin-bottom: 6px;
}

.keyword-weight {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}

.weight-bar {
    flex: 1;
    height: 6px;
    background: #e9ecef;
    border-radius: 3px;
    overflow: hidden;
}

.weight-fill {
    height: 100%;
    background: linear-gradient(90deg, #1e40af, #475569, #dc3545);
    /* transition: width 0.3s ease; 移除过渡动画 */
}

.weight-value {
    font-size: 11px;
    font-weight: bold;
    color: #495057;
    min-width: 40px;
    text-align: right;
}

.keyword-rank {
    font-size: 10px;
    color: #6c757d;
    text-transform: uppercase;
}

.weight-stats {
    display: flex;
    justify-content: space-around;
    background: #f8f9fa;
    padding: 10px;
    border-radius: 6px;
    border: 1px solid #e9ecef;
}

.stat-item {
    text-align: center;
}

.stat-label {
    display: block;
    font-size: 11px;
    color: #6c757d;
    font-weight: 600;
    text-transform: uppercase;
}

.stat-value {
    display: block;
    font-size: 16px;
    font-weight: bold;
    color: #495057;
    margin-top: 2px;
}

/* 扩展关键词样式 */
.expanded-keywords-container {
    margin-top: 10px;
}

.expanded-keywords-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 10px;
}

.expanded-keyword-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    background: #e8f5e8;
    border: 1px solid #c3e6c3;
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 12px;
}

.expanded-text {
    color: #155724;
    font-weight: 500;
}

.expanded-tag {
    background: #28a745;
    color: white;
    padding: 1px 4px;
    border-radius: 6px;
    font-size: 9px;
    font-weight: bold;
    text-transform: uppercase;
}

.expansion-info {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #e3f2fd;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
    color: #1565c0;
}

.expansion-info i {
    color: #2196f3;
}

/* 提取过程摘要样式 */
.extraction-summary {
    margin: 20px 0;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
}

.summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-top: 10px;
}

.summary-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px;
    background: white;
    border-radius: 6px;
    border: 1px solid #e9ecef;
}

.summary-icon {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #007bff;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
}

.summary-content {
    flex: 1;
}

.summary-title {
    font-weight: 600;
    font-size: 13px;
    color: #495057;
    margin-bottom: 2px;
}

.summary-desc {
    font-size: 11px;
    color: #6c757d;
    line-height: 1.3;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .keywords-grid {
        grid-template-columns: 1fr;
        gap: 8px;
    }

    .weight-stats {
        flex-direction: column;
        gap: 8px;
    }

    .stat-item {
        display: flex;
        justify-content: space-between;
        text-align: left;
    }

    .summary-grid {
        grid-template-columns: 1fr;
        gap: 10px;
    }

    .crime-header {
        flex-wrap: wrap;
        gap: 8px;
    }

    .crime-scores {
        width: 100%;
        justify-content: flex-start;
    }
}
.enhancement-section {
    margin: 15px 0;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    overflow: hidden;
}

.enhancement-content {
    padding: 0;
}

.enhancement-box {
    background: #f8f9fa;
    padding: 15px;
}

.enhancement-box.query2doc {
    border-left: 4px solid #007bff;
}

.enhancement-box.hyde {
    border-left: 4px solid #6f42c1;
    background: #faf8ff;
}

.enhancement-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.enhancement-badge {
    background: #007bff;
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: bold;
}

.hyde-badge {
    background: #6f42c1;
}

.enhancement-length {
    font-size: 11px;
    color: #6c757d;
    background: #e9ecef;
    padding: 2px 6px;
    border-radius: 4px;
}

.enhancement-text {
    line-height: 1.6;
    color: #495057;
    margin-bottom: 8px;
}

.expand-btn {
    padding: 2px 8px !important;
    font-size: 11px;
    color: #007bff;
    text-decoration: none;
}

.expand-btn:hover {
    text-decoration: underline;
}

/* 犯罪预览chips */
.crimes-preview {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 8px;
}

.crime-preview-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    background: #e3f2fd;
    border: 1px solid #bbdefb;
    padding: 4px 8px;
    border-radius: 16px;
    font-size: 12px;
}

.crime-preview-chip.more {
    background: #f5f5f5;
    border-color: #ddd;
    color: #666;
}

.crime-name {
    font-weight: 500;
    color: #1976d2;
}

.crime-confidence {
    background: #1976d2;
    color: white;
    padding: 1px 4px;
    border-radius: 8px;
    font-size: 10px;
    font-weight: bold;
}

/* 推理过程优化 */
.reasoning-box {
    background: #fff;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 12px;
}

.reasoning-text {
    line-height: 1.6;
    color: #495057;
}

/* 技术详情网格优化 */
.tech-info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-top: 10px;
}

.tech-info-item {
    background: #f8f9fa;
    padding: 8px 12px;
    border-radius: 6px;
    border-left: 3px solid #007bff;
}

.info-label {
    font-size: 11px;
    color: #6c757d;
    font-weight: 600;
    text-transform: uppercase;
    margin-bottom: 2px;
}

.info-value {
    font-size: 13px;
    color: #495057;
    font-weight: 500;
}

.model-name {
    color: #007bff;
    font-weight: 600;
}

.processing-time {
    color: #28a745;
    font-weight: 600;
}

.method-name {
    color: #6f42c1;
}

/* 融合结果样式 */
.fusion-results-container {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #e9ecef;
    border-radius: 6px;
}

.fusion-result-item {
    padding: 12px;
    border-bottom: 1px solid #f8f9fa;
    /* transition: background-color 0.2s ease; 移除过渡动画 */
}

/* 移除融合结果项悬停效果 */

.fusion-result-item:last-child {
    border-bottom: none;
}

.result-header {
    display: flex;
    align-items: center;
    gap: 10px;
}

.result-rank {
    font-weight: bold;
    color: #495057;
    min-width: 30px;
}

.result-type-badge {
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: bold;
    text-transform: uppercase;
}

.result-type-badge.article {
    background-color: #e3f2fd;
    color: #1976d2;
}

.result-type-badge.case {
    background-color: #f3e5f5;
    color: #7b1fa2;
}

.result-title {
    flex: 1;
    font-weight: 500;
    color: #495057;
}

.result-scores {
    display: flex;
    gap: 8px;
}

.fusion-score, .similarity-score {
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: bold;
}

.fusion-score {
    background-color: #e8f5e8;
    color: #2e7d32;
}

.similarity-score {
    background-color: #e3f2fd;
    color: #1565c0;
}

/* AI回答容器 */
.ai-answer-container {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 15px;
    margin: 10px 0;
}

.answer-content {
    line-height: 1.6;
    color: #495057;
}

/* 面板头部 */
.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid #e9ecef;
}

/* 置信度等级样式 */
.confidence-very-high { color: #28a745; }
.confidence-high { color: #20c997; }
.confidence-medium { color: #475569; }
.confidence-low { color: #dc3545; }

/* 响应式设计 */
@media (max-width: 768px) {
    .tech-info-grid {
        grid-template-columns: 1fr;
        gap: 8px;
    }

    .result-header {
        flex-wrap: wrap;
        gap: 5px;
    }

    .result-scores {
        width: 100%;
        justify-content: flex-end;
    }

    .fusion-results-container {
        max-height: 300px;
    }

    .enhancement-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 5px;
    }
}

/* Markdown内容样式 */
.markdown-content {
    line-height: 1.6;
    color: #374151;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
    color: #1f2937;
    margin: 16px 0 8px 0;
    font-weight: 600;
}

.markdown-content h1 { font-size: 18px; }
.markdown-content h2 { font-size: 16px; }
.markdown-content h3 { font-size: 14px; }
.markdown-content h4 { font-size: 13px; }

.markdown-content p {
    margin: 8px 0;
    word-wrap: break-word;
}

.markdown-content ul,
.markdown-content ol {
    margin: 8px 0;
    padding-left: 20px;
}

.markdown-content li {
    margin: 4px 0;
}

.markdown-content code {
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
    color: #1e293b;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Courier New', Consolas, monospace;
    font-size: 12px;
    border: 1px solid #cbd5e1;
}

.markdown-content pre {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
    margin: 12px 0;
    overflow-x: auto;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.markdown-content pre code {
    background: transparent;
    border: none;
    padding: 0;
    color: #1e293b;
    font-size: 12px;
}

.markdown-content strong {
    font-weight: 700;
    color: #1f2937;
}

.markdown-content em {
    font-style: italic;
    color: #4b5563;
}

.markdown-content a {
    color: #3b82f6;
    text-decoration: none;
    border-bottom: 1px solid rgba(59, 130, 246, 0.3);
    /* transition: all 0.2s ease; 移除过渡动画 */
}

.markdown-content a:hover {
    color: #1d4ed8;
    border-bottom-color: #1d4ed8;
}

.markdown-content blockquote {
    border-left: 4px solid #3b82f6;
    margin: 12px 0;
    padding: 8px 16px;
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border-radius: 0 6px 6px 0;
    color: #1e40af;
}

.markdown-content table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    font-size: 12px;
}

.markdown-content th,
.markdown-content td {
    border: 1px solid #d1d5db;
    padding: 6px 12px;
    text-align: left;
}

.markdown-content th {
    background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
    font-weight: 600;
    color: #374151;
}
</style>
`;

// 创建并导出单例 - 强制重新创建确保可用性
try {
    console.log('📝 开始创建StageRenderer实例...');
    const stageRendererInstance = new StageRenderer();
    
    // 直接绑定到全局对象
    if (typeof window !== 'undefined') {
        window.StageRenderer = stageRendererInstance;
        
        // 验证绑定是否成功
        const stageRendererMethods = ['renderStage1', 'renderStage2', 'renderStage3', 'renderStage4', 'renderStage5'];
        const missingMethods = stageRendererMethods.filter(method =>
            typeof window.StageRenderer[method] !== 'function'
        );

        if (missingMethods.length > 0) {
            console.error('❌ StageRenderer方法绑定失败:', missingMethods);
        } else {
            console.log('✅ StageRenderer单例创建并绑定完成，所有渲染方法可用');
        }
    }
} catch (error) {
    console.error('❌ StageRenderer创建失败:', error);
}

// 在页面加载时添加样式
const addStyles = () => {
    if (document.head && !document.getElementById('stage-renderer-styles')) {
        const styleElement = document.createElement('style');
        styleElement.id = 'stage-renderer-styles';
        styleElement.textContent = stageRendererStyles;
        document.head.appendChild(styleElement);
        console.log('✅ StageRenderer样式已添加');
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addStyles);
} else {
    addStyles();
}