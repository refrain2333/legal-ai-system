// 知识图谱可视化器
class KnowledgeGraphVisualizer {
    constructor() {
        this.width = 1160;
        this.height = 600;
        this.svg = null;
        this.simulation = null;
        this.tooltip = null;
        this.currentData = null;
        this.allCases = []; // 新增：用于存储所有案例数据
        this.eventsInitialized = false; // 防止重复绑定事件

        // 添加缓存机制
        this.cache = {
            stats: null,
            crimes: null,
            articles: null,
            relations: new Map(),
            cases: new Map()
        };

        this.init();
        this.loadKGStats();
    }

    // 创建置信度标记的通用方法
    _createConfidenceBadge(confidence, confidence_level) {
        const confidenceClass = confidence >= 0.8 ? 'high' :
                              confidence >= 0.5 ? 'medium' : 'low';
        const confidenceText = confidence_level || confidenceClass;
        return `<span class="confidence-badge ${confidenceClass}">${confidenceText} ${(confidence * 100).toFixed(1)}%</span>`;
    }

    // 简化的tooltip方法
    showTooltip(content, x, y) {
        this.tooltip.html(content)
            .style('left', Math.min(x + 10, window.innerWidth - 200) + 'px')
            .style('top', Math.max(y - 28, 10) + 'px')
            .style('opacity', 0.95);
    }

    hideTooltip() {
        this.tooltip.style('opacity', 0);
    }

    clearAllTooltips() {
        // 清除主tooltip
        if (this.tooltip) {
            this.tooltip.style('opacity', 0);
        }

        // 清除页面上所有可能存在的tooltip元素
        d3.selectAll('.tooltip').style('opacity', 0);

        // 移除可能残留的tooltip元素
        d3.selectAll('.tooltip').filter(function() {
            return d3.select(this).style('opacity') === '0';
        }).remove();

        // 重新创建主tooltip以确保只有一个
        if (this.tooltip) {
            this.tooltip.remove();
            this._ensureTooltip();
        }
    }

    init() {
        this._createBaseSVG();
        this._ensureTooltip();

        // 绑定事件（只绑定一次）
        if (!this.eventsInitialized) {
            this.initEvents();
        }

        // 添加图例
        this.addLegend();
    }

    // 创建基础SVG元素的通用方法
    _createBaseSVG() {
        const container = d3.select('#visualization');
        container.selectAll('*').remove();

        this.svg = container
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .on('mouseleave', () => {
                if (this.tooltip) {
                    this.tooltip.style('opacity', 0);
                }
            });

        // 创建箭头标记
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 8)
            .attr('markerHeight', 8)
            .append('path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#999');
    }

    // 创建tooltip的通用方法
    _ensureTooltip() {
        if (!this.tooltip) {
            this.tooltip = d3.select('body').append('div')
                .attr('class', 'tooltip')
                .style('opacity', 0)
                .style('pointer-events', 'none')
                .style('position', 'absolute')
                .style('background', 'rgba(45, 55, 72, 0.95)')
                .style('color', 'white')
                .style('padding', '8px 12px')
                .style('border-radius', '4px')
                .style('font-size', '12px')
                .style('z-index', '1000');
        }
    }

    initSVGOnly() {
        this._createBaseSVG();
        this._ensureTooltip();
    }

    initEvents() {
        // 只初始化一次事件监听器
        if (this.eventsInitialized) {
            return;
        }

        // 添加全局事件来清除所有tooltip
        d3.select('body').on('click.tooltip', (event) => {
            this.clearAllTooltips();
        });

        // 添加ESC键清除tooltip
        d3.select('body').on('keydown.tooltip', (event) => {
            if (event.key === 'Escape') {
                this.clearAllTooltips();
            }
        });

        // 绑定搜索事件
        document.getElementById('searchBtn').addEventListener('click', () => {
            const query = document.getElementById('searchInput').value.trim();
            if (query) {
                this.loadEntityRelations(query);
            }
        });

        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = e.target.value.trim();
                if (query) {
                    this.loadEntityRelations(query);
                }
            }
        });

        this.eventsInitialized = true;
    }

    addLegend() {
        // 移除现有图例
        d3.select('#visualization .legend').remove();

        const legend = d3.select('#visualization')
            .append('div')
            .attr('class', 'legend');

        legend.append('div')
            .attr('class', 'legend-title')
            .text('图例');

        const crimeItem = legend.append('div').attr('class', 'legend-item');
        crimeItem.append('div')
            .attr('class', 'legend-circle')
            .style('background-color', '#ff6b6b');
        crimeItem.append('span').text('罪名');

        const articleItem = legend.append('div').attr('class', 'legend-item');
        articleItem.append('div')
            .attr('class', 'legend-circle')
            .style('background-color', '#4ecdc4');
        articleItem.append('span').text('法条');

        const centerItem = legend.append('div').attr('class', 'legend-item');
        centerItem.append('div')
            .attr('class', 'legend-circle')
            .style('background-color', '#feca57');
        centerItem.append('span').text('查询焦点');
    }

    async loadKGStats() {
        try {
            const response = await window.apiConfig.fetch('/api/knowledge_graph/stats');
            const data = await response.json();

            if (data.success && data.knowledge_graph_status.knowledge_graph_stats) {
                const stats = data.knowledge_graph_status.knowledge_graph_stats;
                document.getElementById('totalCrimes').textContent = stats.total_crimes || 0;
                document.getElementById('totalArticles').textContent = stats.total_articles || 0;
                document.getElementById('totalRelations').textContent = stats.total_relations || 0;
            }
        } catch (error) {
            console.error('Failed to load KG stats:', error);
        }
    }

    async loadAllCases() {
        // 注释掉不存在的API调用，避免错误
        // 这个功能暂时不需要，因为我们通过其他API获取具体案例
        this.allCases = [];
        console.log('All cases loading disabled - using direct API calls instead');
    }

    async loadEntityRelations(query) {
        console.log(`开始搜索: ${query}`);
        this.showLoading();
        document.getElementById('currentEntity').textContent = query;

        try {
            // 首先尝试查询扩展API，支持自然语言
            console.log('调用expand API...');
            const expandResponse = await window.apiConfig.fetch(`/api/knowledge_graph/expand/${encodeURIComponent(query)}`);
            const expandData = await expandResponse.json();
            console.log('expand API响应:', expandData);

            if (expandData.success && expandData.expansion_details) {
                // 从扩展结果中提取主要实体
                const expansion = expandData.expansion_details;
                const crimes = expansion.detected_entities?.crimes || [];
                const articles = expansion.detected_entities?.articles || [];
                const relatedArticles = expansion.related_articles || [];
                const relatedCrimes = expansion.related_crimes || [];

                // 检查是否有任何有效结果
                const hasResults = crimes.length > 0 || articles.length > 0 ||
                                 relatedArticles.length > 0 || relatedCrimes.length > 0;

                if (!hasResults) {
                    this.showError(`未找到"${query}"的相关法律信息`);
                    return;
                }

                // 选择最主要的实体进行可视化 - 优化版：精确匹配优先
                let primaryEntity = query;

                // 优先查找精确匹配的罪名
                if (crimes.length > 0) {
                    // 查找是否有精确匹配的罪名
                    const exactCrimeMatch = crimes.find(crime =>
                        crime === query ||
                        crime === query.replace('罪', '') ||
                        query === crime + '罪'
                    );

                    if (exactCrimeMatch) {
                        primaryEntity = exactCrimeMatch;
                    } else {
                        // 如果没有精确匹配，选择最简单的罪名（不包含特殊字符）
                        const simpleCrime = crimes.find(crime =>
                            !crime.includes('[') &&
                            !crime.includes(']') &&
                            !crime.includes('、') &&
                            !crime.includes('，')
                        );
                        primaryEntity = simpleCrime || crimes[0];
                    }
                } else if (articles.length > 0) {
                    // 对法条也做类似处理
                    const exactArticleMatch = articles.find(article =>
                        article === query ||
                        article === query.replace(/第|条/g, '') ||
                        query === `第${article}条`
                    );
                    primaryEntity = exactArticleMatch || articles[0];
                }

                console.log(`自然语言查询"${query}"解析为实体"${primaryEntity}"`);

                // 使用解析出的实体获取关系数据
                console.log('调用relations API...');
                const relationsResponse = await window.apiConfig.fetch(`/api/knowledge_graph/relations/${encodeURIComponent(primaryEntity)}`);
                const relationsData = await relationsResponse.json();
                console.log('relations API响应:', relationsData);

                if (relationsData.success) {
                    console.log('开始可视化图谱...');
                    this.visualizeGraph(relationsData.visualization_data);
                    // 显示详细搜索结果
                    this.displaySearchResults(expandData, relationsData, primaryEntity);
                    console.log('图谱可视化完成');
            } else {
                    console.log('relations API失败:', relationsData);
                    this.showError(`未找到"${primaryEntity}"的相关关系数据`);
                }
            } else {
                // 如果查询扩展失败，尝试直接作为实体查询
                const directResponse = await window.apiConfig.fetch(`/api/knowledge_graph/relations/${encodeURIComponent(query)}`);
                const directData = await directResponse.json();

                if (directData.success) {
                    this.visualizeGraph(directData.visualization_data);
                    // 对于直接查询，创建简化的扩展数据
                    const simpleExpandData = {
                        success: true,
                        original_query: query,
                        expanded_query: query,
                        expansion_details: {
                            original_query: query,
                            detected_entities: { crimes: [], articles: [] },
                            related_articles: [],
                            related_crimes: [],
                            expansion_suggestions: [],
                            expanded_keywords: []
                        }
                    };
                    this.displaySearchResults(simpleExpandData, directData, query);
                } else {
                    this.showError('未找到相关关系数据，请尝试输入具体的罪名或法条编号');
                }
            }
        } catch (error) {
            console.error('搜索过程中发生错误:', error);
            console.error('错误详情:', error.stack);
            this.showError('加载失败：' + error.message);
        }
    }

    showLoading() {
        const container = d3.select('#visualization');
        container.selectAll('*').remove();
        container.append('div')
            .attr('class', 'loading')
            .html('<h3>正在生成知识图谱...</h3><p>请稍候</p>');
    }

    showError(message) {
        const container = d3.select('#visualization');
        container.selectAll('*').remove();

        // 隐藏搜索结果面板
        document.getElementById('searchResultsPanel').style.display = 'none';

        // 显示错误信息和默认搜索建议
        const errorDiv = container.append('div')
            .attr('class', 'no-data');

        errorDiv.append('h3')
            .html(`错误：${message}`);

        errorDiv.append('p')
            .text('请尝试以下推荐查询：');

        // 添加默认搜索建议
        const suggestionsDiv = errorDiv.append('div')
            .attr('class', 'default-suggestions')
            .style('margin-top', '20px');

        const suggestions = [
            { text: '故意伤害', desc: '刑法第234条 - 常见暴力犯罪', type: 'crime', priority: 1 },
            { text: '盗窃', desc: '刑法第264条 - 侵财犯罪', type: 'crime', priority: 2 },
            { text: '诈骗', desc: '刑法第266条 - 经济犯罪', type: 'crime', priority: 3 },
            { text: '第234条', desc: '故意伤害罪 - 伤害他人身体', type: 'article', priority: 1 },
            { text: '第264条', desc: '盗窃罪 - 秘密窃取财物', type: 'article', priority: 2 },
            { text: '第266条', desc: '诈骗罪 - 虚构事实骗取财物', type: 'article', priority: 3 },
            { text: '交通肇事', desc: '刑法第133条 - 交通事故犯罪', type: 'crime', priority: 4 },
            { text: '危险驾驶', desc: '刑法第133条之一 - 危险驾驶行为', type: 'crime', priority: 5 }
        ];

        // 按优先级和类型排序显示
        const sortedSuggestions = suggestions.sort((a, b) => {
            if (a.type !== b.type) {
                return a.type === 'crime' ? -1 : 1; // 罪名在前
            }
            return a.priority - b.priority;
        });

        sortedSuggestions.forEach((suggestion, index) => {
            const suggestionBtn = suggestionsDiv.append('button')
                .attr('class', `example-btn ${suggestion.type}-suggestion`)
                .style('margin', '5px')
                .style('display', 'inline-block')
                .style('position', 'relative')
                .on('click', () => {
                    document.getElementById('searchInput').value = suggestion.text;
                    this.loadEntityRelations(suggestion.text);
                });

            // 添加优先级标识
            if (suggestion.priority <= 3) {
                suggestionBtn.append('span')
                    .style('position', 'absolute')
                    .style('top', '-5px')
                    .style('right', '-5px')
                    .style('background', '#ff6b6b')
                    .style('color', 'white')
                    .style('border-radius', '50%')
                    .style('width', '18px')
                    .style('height', '18px')
                    .style('font-size', '10px')
                    .style('display', 'flex')
                    .style('align-items', 'center')
                    .style('justify-content', 'center')
                    .style('font-weight', 'bold')
                    .text(suggestion.priority);
            }

            suggestionBtn.append('div')
                .style('font-weight', 'bold')
                .style('margin-bottom', '2px')
                .text(suggestion.text);

            suggestionBtn.append('div')
                .style('font-size', '11px')
                .style('opacity', '0.8')
                .style('color', suggestion.type === 'crime' ? '#c62828' : '#1565c0')
                .text(suggestion.desc);
        });
    }

    visualizeGraph(data) {
        console.log('=== 开始绘制图谱 ===');
        console.log('输入数据:', data);

        if (!data || !data.nodes || data.nodes.length === 0) {
            console.log('数据无效，显示错误');
            this.showError('没有找到相关关系');
            return;
        }

        console.log(`数据验证通过: ${data.nodes.length}个节点, ${data.edges?.length || 0}个边`);

        // 确保容器存在
        const container = d3.select('#visualization');
        if (container.empty()) {
            console.error('可视化容器不存在！');
            return;
        }

        // 清理容器并重建SVG（使用通用方法）
        console.log('清理容器并创建SVG');
        this._createBaseSVG();

        // 复制数据避免修改原始数据
        const nodes = data.nodes.map(d => ({...d}));
        const links = data.edges.map(d => ({...d}));

        console.log('数据处理完成:', nodes.length, '个节点,', links.length, '条边');

        // 创建力导向模拟
        this.simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2));

        console.log('力导向模拟创建完成');

        // 创建连接线
        const link = this.svg.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('class', 'link')
            .attr('marker-end', 'url(#arrowhead)')
            .style('cursor', 'pointer')
            .on('mouseover', (event, d) => {
                // 连线悬停效果
                d3.select(event.target).style('stroke-width', '4px').style('stroke', '#667eea');
            })
            .on('mouseout', (event, d) => {
                // 恢复连线样式
                d3.select(event.target).style('stroke-width', '2px').style('stroke', '#999');
            })
            .on('click', (event, d) => {
                // 连线点击事件 - 显示具体案例
                console.log('点击连线，显示案例');
                this.showRelationCases(d.source, d.target, d);
            });

        console.log('创建了', link.size(), '条连接线');

        // 创建节点
        const node = this.svg.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('class', d => `node ${d.type} ${d.id === data.center_node?.id ? 'center' : ''}`)
            .attr('r', d => d.id === data.center_node?.id ? 20 : 15)
            .style('cursor', 'pointer')
            .on('mouseover', (event, d) => {
                // 节点悬停效果
                if (this.tooltip) {
                    let tooltipContent = `<strong>${d.label}</strong><br/>类型: ${d.type === 'crime' ? '罪名' : '法条'}`;
                    if (d.confidence) {
                        tooltipContent += `<br/>置信度: ${(d.confidence * 100).toFixed(1)}%`;
                    }
                    this.tooltip.html(tooltipContent)
                        .style('left', Math.min(event.pageX + 10, window.innerWidth - 200) + 'px')
                        .style('top', Math.max(event.pageY - 28, 10) + 'px')
                        .style('opacity', 0.95);
                }
            })
            .on('mouseout', (event, d) => {
                // 隐藏提示
                if (this.tooltip) {
                    this.tooltip.style('opacity', 0);
                }
            })
            .on('click', (event, d) => {
                // 节点点击事件 - 跳转搜索
                console.log('点击节点:', d.label);
                if (d.id !== data.center_node?.id) {
                    const entityName = d.type === 'crime' ? d.label.replace('罪', '') : d.label.replace(/第|条/g, '');
                    console.log('跳转搜索:', entityName);
                    document.getElementById('searchInput').value = entityName;
                    this.loadEntityRelations(entityName);
                }
            })
            .call(this.drag());

        console.log('创建了', node.size(), '个节点');

        // 创建节点标签
        const nodeLabel = this.svg.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .attr('class', 'node-label')
            .text(d => d.label)
            .style('font-size', d => d.id === data.center_node?.id ? '14px' : '12px')
            .style('font-weight', d => d.id === data.center_node?.id ? 'bold' : 'normal');

        console.log('创建了', nodeLabel.size(), '个标签');

        // 创建连接线标签
        const linkLabel = this.svg.append('g')
            .selectAll('text')
            .data(links)
            .enter().append('text')
            .attr('class', 'link-label')
            .text(d => d.label || '')
            .style('cursor', 'pointer')
            .style('font-size', '12px')
            .style('fill', '#333')
            .style('text-anchor', 'middle')
            .style('pointer-events', 'all')
            .on('click', (event, d) => {
                event.stopPropagation();
                console.log('点击连线标签，显示案例');
                this.showRelationCases(d.source, d.target, d);
            })
            .on('mouseover', (event, d) => {
                d3.select(event.target).style('font-weight', 'bold').style('fill', '#667eea');
            })
            .on('mouseout', (event, d) => {
                d3.select(event.target).style('font-weight', 'normal').style('fill', '#333');
            });

        console.log('创建了', linkLabel.size(), '个连线标签');

        // 更新位置（简化版）
        let tickCount = 0;
        this.simulation.on('tick', () => {
            tickCount++;
            if (tickCount === 1) {
                console.log('力导向模拟开始运行');
            }

            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            linkLabel
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2);

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            nodeLabel
                .attr('x', d => d.x)
                .attr('y', d => d.y + 5);

            if (tickCount === 50) {
                console.log('力导向模拟运行稳定，节点位置:', nodes.map(d => ({id: d.id, x: d.x, y: d.y})));
            }
        });

        this.currentData = data;
        console.log('=== 图谱绘制完成 ===');

        // 添加图例
        setTimeout(() => {
            this.addLegend();
        }, 100);
    }

    displaySearchResults(expandData, relationsData, primaryEntity) {
        // 显示搜索结果面板
        const resultsPanel = document.getElementById('searchResultsPanel');
        resultsPanel.style.display = 'block';

        const expansion = expandData.expansion_details || {};

        // 构建结构化的搜索结果数据，便于集成
        const structuredResults = {
            query_info: {
                original_query: expandData.original_query || '',
                expanded_query: expandData.expanded_query || '',
                primary_entity: primaryEntity || '',
                search_timestamp: new Date().toISOString(),
                search_method: 'knowledge_graph'
            },
            detected_entities: expansion.detected_entities || { crimes: [], articles: [] },
            related_articles: (expansion.related_articles || []).map(article => ({
                article_number: article.article_number,
                article_display: article.article_display,
                confidence: article.confidence,
                case_count: article.case_count,
                integration_weight: article.confidence * 0.8 // 用于结果集成的权重
            })),
            related_crimes: (expansion.related_crimes || []).map(crime => ({
                crime_name: crime.crime_name || crime.crime_display,
                confidence: crime.confidence,
                case_count: crime.case_count,
                integration_weight: crime.confidence * 0.7 // 用于结果集成的权重
            })),
            expansion_keywords: expansion.expanded_keywords || [],
            expansion_suggestions: expansion.expansion_suggestions || [],
            visualization_ready: relationsData.success,
            search_quality_score: this.calculateSearchQuality(expansion)
        };

        // 将结构化结果存储到全局变量，便于其他模块访问
        window.knowledgeGraphResults = structuredResults;
        console.log('知识图谱搜索结果已结构化:', structuredResults);

        // 填充查询信息
        document.getElementById('originalQuery').textContent = structuredResults.query_info.original_query;
        document.getElementById('expandedQuery').textContent = structuredResults.query_info.expanded_query;
        document.getElementById('primaryEntity').textContent = structuredResults.query_info.primary_entity;

        // 填充实体检测结果
        this.displayDetectedEntities(structuredResults.detected_entities);

        // 填充相关法条
        this.displayRelatedArticles(structuredResults.related_articles);

        // 填充相关罪名
        this.displayRelatedCrimes(structuredResults.related_crimes);

        // 填充扩展建议
        this.displayExpansionSuggestions(structuredResults.expansion_suggestions);

        // 填充原始数据
        this.displayRawData({
            structuredResults,
            expandData,
            relationsData
        });
    }

    calculateSearchQuality(expansion) {
        // 计算搜索质量评分，用于结果集成
        let score = 0;

        // 检测到实体得分
        const crimes = expansion.detected_entities?.crimes || [];
        const articles = expansion.detected_entities?.articles || [];
        score += crimes.length * 0.3 + articles.length * 0.3;

        // 相关关系得分
        const relatedArticles = expansion.related_articles || [];
        const relatedCrimes = expansion.related_crimes || [];
        score += relatedArticles.length * 0.2 + relatedCrimes.length * 0.2;

        // 置信度得分
        const avgConfidence = relatedArticles.length > 0 ?
            relatedArticles.reduce((sum, art) => sum + art.confidence, 0) / relatedArticles.length : 0;
        score += avgConfidence * 0.5;

        return Math.min(score, 1.0); // 限制在1.0以内
    }

    displayDetectedEntities(entities) {
        const crimesContainer = document.getElementById('detectedCrimes');
        const articlesContainer = document.getElementById('detectedArticles');

        // 显示检测到的罪名
        if (entities.crimes && entities.crimes.length > 0) {
            crimesContainer.innerHTML = entities.crimes.map(crime =>
                `<span class="entity-tag crime-tag">${crime}</span>`
            ).join('');
        } else {
            crimesContainer.innerHTML = '<span class="entity-tag">暂无</span>';
        }

        // 显示检测到的法条
        if (entities.articles && entities.articles.length > 0) {
            articlesContainer.innerHTML = entities.articles.map(article =>
                `<span class="entity-tag article-tag">第${article}条</span>`
            ).join('');
        } else {
            articlesContainer.innerHTML = '<span class="entity-tag">暂无</span>';
        }
    }

    displayRelatedArticles(articles) {
        const container = document.getElementById('articlesList');

        if (articles && articles.length > 0) {
            container.innerHTML = articles.map(article => {
                return `
                    <div class="article-item">
                        <div class="article-item-header">
                            <span class="article-title">${article.article_display || `第${article.article_number}条`}</span>
                            ${this._createConfidenceBadge(article.confidence, article.confidence_level)}
                        </div>
                        <div class="article-meta">
                            案例数量: ${article.case_count || 0} |
                            关系类型: ${article.relation_type || '未知'} |
                            ${article.rare_crime ? '稀有罪名' : '常见罪名'}
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = '<div class="article-item">暂无相关法条</div>';
        }
    }

    displayRelatedCrimes(crimes) {
        const container = document.getElementById('crimesList');

        if (crimes && crimes.length > 0) {
            container.innerHTML = crimes.map(crime => {
                return `
                    <div class="crime-item">
                        <div class="crime-item-header">
                            <span class="crime-title">${crime.crime_display || crime.crime_name}</span>
                            ${this._createConfidenceBadge(crime.confidence, crime.confidence_level)}
                        </div>
                        <div class="crime-meta">
                            案例数量: ${crime.case_count || 0} |
                            关系类型: ${crime.relation_type || '未知'} |
                            ${crime.rare_crime ? '稀有罪名' : '常见罪名'}
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = '<div class="crime-item">暂无相关罪名</div>';
        }
    }

    displayExpansionSuggestions(suggestions) {
        const container = document.getElementById('suggestionsList');

        if (suggestions && suggestions.length > 0) {
            container.innerHTML = suggestions.map(suggestion =>
                `<div class="suggestion-item">${suggestion}</div>`
            ).join('');
        } else {
            container.innerHTML = '<div class="suggestion-item">暂无扩展建议</div>';
        }
    }

    displayRawData(data) {
        const container = document.getElementById('rawDataDisplay');
        container.textContent = JSON.stringify(data, null, 2);
    }

    async showRelationCases(sourceNode, targetNode, linkData) {
        // 使用API调用获取案例数据，而不是依赖预加载
        let crime, article;
        if (sourceNode.type === 'crime' && targetNode.type === 'article') {
            crime = sourceNode.label.replace('罪', '');
            article = targetNode.label.replace(/第|条/g, '');
        } else if (sourceNode.type === 'article' && targetNode.type === 'crime') {
            crime = targetNode.label.replace('罪', '');
            article = sourceNode.label.replace(/第|条/g, '');
        } else {
            return; // 非罪名-法条的连接
        }

        try {
            const response = await window.apiConfig.fetch(`/api/knowledge_graph/relation_cases/${encodeURIComponent(crime)}/${article}?limit=5`);
            const data = await response.json();

            if (data.success && data.cases && data.cases.length > 0) {
                // 使用全局函数显示案例
                showCasesModal(`${crime}+${article}`, 'relation', data.cases);
            } else {
                alert('未找到相关案例');
            }
        } catch (error) {
            console.error('Failed to load relation cases:', error);
            alert('加载案例失败：' + error.message);
        }
    }

    drag() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }
}

// 全局函数和事件处理

// 示例查询函数
function loadExample(entity) {
    document.getElementById('searchInput').value = entity;
    visualizer.loadEntityRelations(entity);
}

// 模态窗口相关函数
async function showCrimesList() {
    try {
        // 检查缓存
        if (visualizer.cache.crimes) {
            showModal('全部罪名列表', visualizer.cache.crimes, 'crimes');
            return;
        }

        // 显示加载状态
        const crimesCard = document.getElementById('crimesCard');
        const originalText = crimesCard.innerHTML;
        crimesCard.innerHTML = '<div class="stat-number">-</div><div class="stat-label">加载中...</div>';

        const response = await window.apiConfig.fetch('/api/knowledge_graph/crimes');
        const data = await response.json();

        if (data.success) {
            // 缓存数据
            visualizer.cache.crimes = data.crimes;
            showModal('全部罪名列表', data.crimes, 'crimes');
        } else {
            alert('获取罪名列表失败');
        }

        // 恢复原始显示
        crimesCard.innerHTML = originalText;
    } catch (error) {
        console.error('Failed to load crimes:', error);
        alert('加载罪名失败：' + error.message);

        // 恢复原始显示
        const crimesCard = document.getElementById('crimesCard');
        crimesCard.innerHTML = '<div class="stat-number" id="totalCrimes">-</div><div class="stat-label">罪名总数</div>';
    }
}

async function showArticlesList() {
    try {
        // 检查缓存
        if (visualizer.cache.articles) {
            showModal('📋 全部法条列表', visualizer.cache.articles, 'articles');
            return;
        }

        const response = await window.apiConfig.fetch('/api/knowledge_graph/articles');
        const data = await response.json();

        if (data.success) {
            // 缓存数据
            visualizer.cache.articles = data.articles;
            showModal('📋 全部法条列表', data.articles, 'articles');
        } else {
            alert('获取法条列表失败');
        }
    } catch (error) {
        console.error('Failed to load articles list:', error);
        alert('获取法条列表失败：' + error.message);
    }
}

function showModal(title, items, type) {
    document.getElementById('modalTitle').textContent = title;
    const listContainer = document.getElementById('listContainer');
    listContainer.innerHTML = '';

    // 存储原始数据用于搜索
    window.modalData = { items, type };

    // 显示所有项目
    displayModalItems(items, type);

    // 绑定搜索事件
    const searchInput = document.getElementById('modalSearchInput');
    searchInput.value = '';
    searchInput.oninput = (e) => filterModalItems(e.target.value);

    // 显示模态窗口（带动画）
    const modal = document.getElementById('listModal');
    modal.style.display = 'block';
    // 强制重排以确保动画效果
    modal.offsetHeight;
    modal.classList.add('show');
}

function displayModalItems(items, type) {
    const listContainer = document.getElementById('listContainer');
    listContainer.innerHTML = '';

    items.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'list-item';

        let title, stats;
        if (type === 'crimes') {
            title = item.crime;
            // 只显示前5个主要法条，避免显示过多
            const mainArticles = item.related_articles.slice(0, 5);
            const articlesDisplay = mainArticles.join(', ') + (item.related_articles.length > 5 ? '...' : '');
            stats = `案例数量: ${item.case_count} | 相关法条: ${articlesDisplay}`;
        } else {
            title = `第${item.article_number}条 - ${item.title}`;
            stats = `案例数量: ${item.case_count} | 章节: ${item.chapter}`;
        }

        itemDiv.innerHTML = `
            <div class="list-item-title">${title}</div>
            <div class="list-item-stats">${stats}</div>
            <div class="list-item-actions">
                <button class="view-relation-btn" type="button">
                    查看关系图
                </button>
                <button class="view-cases-btn" type="button">
                    查看案例 (${item.case_count})
                </button>
            </div>
        `;

        // 添加事件监听器
        const entityName = type === 'crimes' ? item.crime.replace('罪', '') : item.article_number;

        // 查看关系图按钮事件
        const relationBtn = itemDiv.querySelector('.view-relation-btn');
        relationBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            loadEntityRelation(entityName);
        });

        // 查看案例按钮事件
        const casesBtn = itemDiv.querySelector('.view-cases-btn');
        casesBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            showRelatedCases(entityName, type);
        });

        // 添加整行点击事件
        itemDiv.onclick = () => {
            closeModal();
            document.getElementById('searchInput').value = entityName;
            visualizer.loadEntityRelations(entityName);
        };

        listContainer.appendChild(itemDiv);
    });

    // 显示结果统计
    const resultCount = document.createElement('div');
    resultCount.style.textAlign = 'center';
    resultCount.style.padding = '10px';
    resultCount.style.color = '#666';
    resultCount.textContent = `共找到 ${items.length} 项结果`;
    listContainer.appendChild(resultCount);
}

function filterModalItems(searchTerm) {
    if (!window.modalData) return;

    const { items, type } = window.modalData;
    const filteredItems = items.filter(item => {
        if (type === 'crimes') {
            return item.crime.toLowerCase().includes(searchTerm.toLowerCase()) ||
                   item.related_articles.some(article => article.includes(searchTerm));
        } else {
            return item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                   item.article_number.includes(searchTerm) ||
                   (item.chapter && item.chapter.toLowerCase().includes(searchTerm.toLowerCase()));
        }
    });

    displayModalItems(filteredItems, type);
}

// 从案件事实中提取涉案人员
function extractCriminals(fact, existingCriminals) {
    // 只有当结构化数据真的有内容时才使用
    if (existingCriminals && existingCriminals.length > 0 && existingCriminals.some(name => name && name.trim())) {
        return existingCriminals.filter(name => name && name.trim()).join('、');
    }

    if (!fact) return '暂无';

    // 正则表达式匹配常见的人员表述模式
    const patterns = [
        /被告人([^、，。\s至]+)/g,
        /犯罪嫌疑人([^、，。\s至]+)/g,
        /上诉人([^、，。\s至]+)/g,
        /原审被告人([^、，。\s至]+)/g,
        /当事人([^、，。\s至]+)/g
    ];

    const names = new Set();

    for (const pattern of patterns) {
        let match;
        while ((match = pattern.exec(fact)) !== null) {
            let name = match[1].trim();
            // 清理名字，去除常见后缀和无效字符
            name = name.replace(/等人?$/, '')
                     .replace(/[、，。；：].*$/, '')
                     .replace(/\s+.*$/, '')
                     .replace(/在.*$/, '')
                     .replace(/至.*$/, '')
                     .trim();

            // 验证是否是有效的人名（中文姓名通常2-4个字）
            if (name && name.length >= 2 && name.length <= 4 && /^[一-龯某甲乙丙丁]+$/.test(name)) {
                names.add(name);
            }
        }
    }

    return names.size > 0 ? Array.from(names).join('、') : '暂无';
}

// 格式化刑期信息 (使用正确的数据结构)
function formatSentenceInfo(sentenceInfo, fact) {
    const parts = [];

    // 先检查结构化数据（按照数据集说明的正确格式）
    let hasValidStructuredData = false;

    if (sentenceInfo && sentenceInfo.death_penalty) {
        parts.push('死刑');
        hasValidStructuredData = true;
    } else if (sentenceInfo && sentenceInfo.life_imprisonment) {
        parts.push('无期徒刑');
        hasValidStructuredData = true;
    } else if (sentenceInfo && sentenceInfo.imprisonment_months && sentenceInfo.imprisonment_months > 0) {
        const months = sentenceInfo.imprisonment_months;  // 直接是数字，不是数组
        if (months >= 12) {
            const years = Math.floor(months / 12);
            const remainingMonths = months % 12;
            if (remainingMonths > 0) {
                parts.push(`有期徒刑${years}年${remainingMonths}个月`);
            } else {
                parts.push(`有期徒刑${years}年`);
            }
        } else {
            parts.push(`有期徒刑${months}个月`);
        }
        hasValidStructuredData = true;
    }

    if (sentenceInfo && sentenceInfo.fine_amount && sentenceInfo.fine_amount > 0) {
        parts.push(`罚金${sentenceInfo.fine_amount}元`);
        hasValidStructuredData = true;
    }

    // 如果结构化数据为空或无效，尝试从事实中提取
    if (!hasValidStructuredData && fact) {
        // 更全面的刑期匹配模式
        const sentencePatterns = [
            /判处死刑/gi,
            /判处无期徒刑/gi,
            /判处有期徒刑(\d+)年(\d+)个月/gi,
            /判处有期徒刑(\d+)年/gi,
            /判处有期徒刑(\d+)个月/gi,
            /有期徒刑(\d+)年(\d+)个月/gi,
            /有期徒刑(\d+)年/gi,
            /有期徒刑(\d+)个月/gi,
            /拘役(\d+)个月/gi,
            /罚金人?民?币?(\d+(?:\.\d+)?)万?元/gi,
            /罚金(\d+(?:\.\d+)?)万?元/gi,
            /并处罚金(\d+(?:\.\d+)?)万?元/gi
        ];

        for (const pattern of sentencePatterns) {
            let match;
            while ((match = pattern.exec(fact)) !== null) {
                const fullMatch = match[0];
                if (fullMatch.includes('死刑')) {
                    parts.push('死刑');
                    break; // 死刑是最高刑，找到就停止
                } else if (fullMatch.includes('无期徒刑')) {
                    parts.push('无期徒刑');
                    break; // 无期徒刑也是重刑，找到就停止
                } else if (match[2] && fullMatch.includes('有期徒刑')) {
                    // 有期徒刑X年X个月
                    parts.push(`有期徒刑${match[1]}年${match[2]}个月`);
                } else if (match[1] && fullMatch.includes('有期徒刑')) {
                    // 有期徒刑X年 或 有期徒刑X个月
                    if (fullMatch.includes('年')) {
                        parts.push(`有期徒刑${match[1]}年`);
                    } else {
                        parts.push(`有期徒刑${match[1]}个月`);
                    }
                } else if (match[1] && fullMatch.includes('拘役')) {
                    parts.push(`拘役${match[1]}个月`);
                } else if (match[1] && fullMatch.includes('罚金')) {
                    const amount = parseFloat(match[1]);
                    if (fullMatch.includes('万')) {
                        parts.push(`罚金${amount}万元`);
                    } else {
                        parts.push(`罚金${amount}元`);
                    }
                }
            }
        }

        // 去重复，保留最重的刑罚
        if (parts.length > 1) {
            const uniqueParts = [...new Set(parts)];
            parts.length = 0;
            parts.push(...uniqueParts);
        }
    }

    return parts.length > 0 ? parts.join('、') : '暂无';
}

// 添加新功能函数
function loadEntityRelation(entity) {
    closeModal();
    document.getElementById('searchInput').value = entity;
    visualizer.loadEntityRelations(entity);
}

async function showRelatedCases(entity, type) {
    try {
        // 根据类型确定API调用参数
        let apiUrl;
        if (type === 'crimes') {
            // 对于罪名，我们需要找到它最相关的法条来获取案例
            const response = await window.apiConfig.fetch(`/api/knowledge_graph/relations/${entity}`);
            const data = await response.json();

            if (data.success && data.visualization_data && data.visualization_data.edges && data.visualization_data.edges.length > 0) {
                // 从可视化数据中提取第一个相关法条
                const firstEdge = data.visualization_data.edges[0];
                const targetNode = data.visualization_data.nodes.find(node => node.id === firstEdge.target);
                if (targetNode && targetNode.type === 'article') {
                    // 提取法条编号（去除前缀和格式化）
                    const articleNumber = targetNode.id.replace('article_', '').replace(/第|条/g, '');
                    apiUrl = `/api/knowledge_graph/relation_cases/${entity}/${articleNumber}?limit=5`;
                } else {
                    alert('未找到相关法条信息');
                    return;
                }
            } else {
                alert('未找到相关法条信息');
                return;
            }
        } else {
            // 对于法条，我们需要找到它最相关的罪名来获取案例
            const response = await window.apiConfig.fetch(`/api/knowledge_graph/relations/${entity}`);
            const data = await response.json();

            if (data.success && data.visualization_data && data.visualization_data.edges && data.visualization_data.edges.length > 0) {
                // 从可视化数据中提取第一个相关罪名
                const firstEdge = data.visualization_data.edges[0];
                const targetNode = data.visualization_data.nodes.find(node => node.id === firstEdge.target);
                if (targetNode && targetNode.type === 'crime') {
                    // 提取罪名（去除前缀和格式化）
                    const crimeName = targetNode.id.replace('crime_', '').replace('罪', '');
                    apiUrl = `/api/knowledge_graph/relation_cases/${crimeName}/${entity}?limit=5`;
                } else {
                    alert('未找到相关罪名信息');
                    return;
                }
            } else {
                alert('未找到相关罪名信息');
                return;
            }
        }

        // 获取具体案例
        const casesResponse = await window.apiConfig.fetch(apiUrl);
        const casesData = await casesResponse.json();

        if (casesData.success && casesData.cases && casesData.cases.length > 0) {
            showCasesModal(entity, type, casesData.cases);
        } else {
            alert('未找到相关案例');
        }
    } catch (error) {
        console.error('Failed to load related cases:', error);
        alert('获取相关案例失败：' + error.message);
    }
}

function showCasesModal(entity, type, cases) {
    const modal = document.getElementById('listModal');
    const modalTitle = document.getElementById('modalTitle');
    const listContainer = document.getElementById('listContainer');

    // 隐藏搜索框
    document.getElementById('modalSearchInput').style.display = 'none';

    // 根据类型设置标题
    let title;
    if (type === 'crimes') {
        title = `${entity}罪 相关案例 (共${cases.length}个)`;
    } else if (type === 'articles') {
        title = `第${entity}条 相关案例 (共${cases.length}个)`;
    } else if (type === 'relation') {
        const [crime, article] = entity.split('+');
        title = `"${crime}罪" - "第${article}条" 关联案例 (共${cases.length}个)`;
    } else {
        title = `相关案例 (共${cases.length}个)`;
    }

    modalTitle.textContent = title;
    listContainer.innerHTML = '';

    cases.forEach((caseItem, index) => {
        const caseDiv = document.createElement('div');
        caseDiv.className = 'case-detail-item';
        caseDiv.innerHTML = `
            <div class="case-header">
                <div class="case-number">案例 ${index + 1}</div>
            </div>
            <div class="case-content">
                <div class="case-fact">
                    <strong>案件事实：</strong>
                    <p>${caseItem.fact || '案件详情暂无'}</p>
                </div>
                <div class="case-meta-info">
                    <div class="case-info-row">
                        <strong>罪名：</strong>
                        <span class="info-value">${caseItem.accusations ? caseItem.accusations.join('、') : '暂无'}</span>
                    </div>
                    <div class="case-info-row">
                        <strong>相关法条：</strong>
                        <span class="info-value">${caseItem.relevant_articles ? caseItem.relevant_articles.map(art => `第${art}条`).join('、') : '暂无'}</span>
                    </div>
                    ${caseItem.case_id ? `
                    <div class="case-info-row">
                        <strong>案例编号：</strong>
                        <span class="info-value">${caseItem.case_id}</span>
                    </div>
                    ` : ''}
                    ${(caseItem.criminals && caseItem.criminals.length > 0) ? `
                    <div class="case-info-row">
                        <strong>涉案人员：</strong>
                        <span class="info-value">${caseItem.criminals.join('、')}</span>
                    </div>
                    ` : ''}
                    ${(caseItem.sentence_info && (caseItem.sentence_info.imprisonment_months || caseItem.sentence_info.fine_amount || caseItem.sentence_info.death_penalty || caseItem.sentence_info.life_imprisonment)) ? `
                    <div class="case-info-row">
                        <strong>刑期信息：</strong>
                        <span class="info-value">${formatSentenceInfo(caseItem.sentence_info, caseItem.fact)}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
        listContainer.appendChild(caseDiv);
    });

    // 显示模态窗口（带动画）
    modal.style.display = 'block';
    // 强制重排以确保动画效果
    modal.offsetHeight;
    modal.classList.add('show');
}

function closeModal() {
    const modal = document.getElementById('listModal');
    const searchInput = document.getElementById('modalSearchInput');

    // 添加关闭动画
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
        searchInput.style.display = 'block'; // 恢复搜索框显示
        window.modalData = null;
    }, 300); // 等待动画完成
}

// 切换区块展开/折叠
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const button = event.target;

    if (section.classList.contains('collapsed')) {
        section.classList.remove('collapsed');
        button.textContent = '折叠';
    } else {
        section.classList.add('collapsed');
        button.textContent = '展开';
    }
}

// 全局事件监听器
window.addEventListener('DOMContentLoaded', function() {
    // 初始化可视化器
    window.visualizer = new KnowledgeGraphVisualizer();

    // 点击模态窗口外部关闭
    window.onclick = function(event) {
        const modal = document.getElementById('listModal');
        if (event.target === modal) {
            closeModal();
        }
    };

    // 键盘事件处理
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeModal();
        }
    });
});