/**
/**
 * 数据格式化器 - 负责格式化和转换数据
 * 基于debug-interfaces.ts的类型定义
 */

class DataFormatter {
    constructor() {
        this.pathDisplayNames = {
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

        this.statusDisplayNames = {
            'success': '成功',
            'error': '失败',
            'pending': '等待中',
            'running': '运行中',
            'skipped': '已跳过'
        };

        this.moduleTypeDescriptions = {
            'classification': 'LLM问题分类模块',
            'extraction': '结构化信息提取模块',
            'routing': '智能路由决策模块',
            'search': '多路搜索执行模块',
            'fusion': '结果融合模块'
        };
    }

    /**
     * 获取路径显示名称
     */
    getPathDisplayName(path) {
        // 先尝试完整匹配
        if (this.pathDisplayNames[path]) {
            return this.pathDisplayNames[path];
        }
        
        // 尝试匹配简化版本（去掉_search后缀）
        const simplifiedPath = path.replace('_search', '');
        if (this.pathDisplayNames[simplifiedPath]) {
            return this.pathDisplayNames[simplifiedPath];
        }
        
        // 尝试匹配完整版本（添加_search后缀）
        const fullPath = path.endsWith('_search') ? path : path + '_search';
        if (this.pathDisplayNames[fullPath]) {
            return this.pathDisplayNames[fullPath];
        }
        
        // 都没找到，返回原始路径
        return path;
    }

    /**
     * 获取状态显示名称
     */
    getStatusDisplayName(status) {
        return this.statusDisplayNames[status] || status;
    }

    /**
     * 获取模块类型描述
     */
    getModuleTypeDescription(moduleType) {
        return this.moduleTypeDescriptions[moduleType] || moduleType;
    }

    /**
     * 格式化置信度显示
     */
    formatConfidence(confidence) {
        if (typeof confidence !== 'number') return '0%';
        return `${(confidence * 100).toFixed(1)}%`;
    }

    /**
     * 格式化处理时间
     */
    formatProcessingTime(timeMs) {
        if (typeof timeMs !== 'number') return '0ms';
        return `${Math.round(timeMs)}ms`;
    }

    /**
     * 格式化字符数
     */
    formatCharacterCount(text) {
        if (typeof text !== 'string') return '0 字符';
        return `${text.length} 字符`;
    }

    /**
     * 获取置信度等级
     */
    getConfidenceLevel(confidence) {
        const percent = confidence * 100;
        if (percent >= 90) return 'very-high';
        if (percent >= 80) return 'high';
        if (percent >= 70) return 'medium';
        return 'low';
    }

    /**
     * 获取权重等级
     */
    getWeightLevel(weight) {
        if (weight >= 0.8) return 'high';
        if (weight >= 0.6) return 'medium';
        return 'low';
    }

    /**
     * 获取权重等级文本
     */
    getWeightLevelText(level) {
        const texts = {
            'high': '高权重',
            'medium': '中权重',
            'low': '低权重',
            'basic': '基础权重'
        };
        return texts[level] || '未知权重';
    }

    /**
     * 格式化模块执行结果
     */
    formatModuleResult(moduleTrace) {
        if (!moduleTrace) return null;

        const status = moduleTrace.status;
        const processingTime = this.formatProcessingTime(moduleTrace.processing_time_ms);
        const confidence = moduleTrace.confidence_score ? 
                          this.formatConfidence(moduleTrace.confidence_score) : null;

        return {
            status: status,
            statusText: this.getStatusDisplayName(status),
            processingTime: processingTime,
            confidence: confidence,
            isSuccess: status === 'success',
            hasError: status === 'error',
            errorMessage: moduleTrace.error_message
        };
    }

    /**
     * 格式化搜索结果统计
     */
    formatSearchStats(searches) {
        if (!searches) return null;

        const total = Object.keys(searches).length;
        const successful = Object.values(searches).filter(s => s.status === 'success').length;
        const failed = total - successful;
        const totalTime = Object.values(searches).reduce((sum, s) => sum + (s.processing_time_ms || 0), 0);

        return {
            total: total,
            successful: successful,
            failed: failed,
            successRate: total > 0 ? ((successful / total) * 100).toFixed(1) : '0',
            totalTime: this.formatProcessingTime(totalTime),
            averageTime: total > 0 ? this.formatProcessingTime(totalTime / total) : '0ms'
        };
    }

    /**
     * 格式化融合结果统计
     */
    formatFusionStats(fusionTrace) {
        if (!fusionTrace || !fusionTrace.output_data) return null;

        const fusionData = fusionTrace.output_data;
        
        return {
            algorithm: fusionData.fusion_algorithm || 'RRF',
            sourcesCount: fusionData.input_sources_count || 0,
            totalResults: fusionData.total_input_results || 0,
            finalResults: fusionData.final_results_count || 0,
            finalConfidence: this.formatConfidence(fusionData.final_confidence || 0),
            answerLength: this.formatCharacterCount(fusionData.final_answer || ''),
            efficiency: this.formatConfidence(fusionData.fusion_efficiency || 0.85)
        };
    }

    /**
     * 格式化性能指标
     */
    formatPerformanceMetrics(trace) {
        if (!trace) return null;

        return {
            totalDuration: this.formatProcessingTime(trace.total_duration_ms || 0),
            stagesCompleted: trace.summary?.stages_completed || 0,
            successfulModules: trace.summary?.successful_modules || 0,
            highestConfidence: this.formatConfidence(trace.summary?.highest_confidence || 0)
        };
    }

    /**
     * 格式化关键词权重数据
     */
    formatKeywordWeights(keywords) {
        if (!Array.isArray(keywords)) return [];

        return keywords.map((kw, index) => {
            if (typeof kw === 'object' && kw.keyword && kw.weight !== undefined) {
                return {
                    rank: index + 1,
                    text: kw.keyword,
                    weight: (kw.weight * 100).toFixed(1),
                    weightLevel: this.getWeightLevel(kw.weight),
                    weightLevelText: this.getWeightLevelText(this.getWeightLevel(kw.weight)),
                    hasWeight: true,
                    rawWeight: kw.weight
                };
            } else {
                return {
                    rank: index + 1,
                    text: typeof kw === 'string' ? kw : String(kw),
                    weightLevelText: this.getWeightLevelText('basic'),
                    weightLevel: 'basic',
                    hasWeight: false
                };
            }
        });
    }

    /**
     * 格式化罪名识别结果
     */
    formatIdentifiedCrimes(crimes) {
        if (!Array.isArray(crimes)) return [];

        return crimes.map((crime, index) => {
            const confidence = crime.confidence || crime.relevance || 0;
            const confidencePercent = confidence * 100;

            return {
                rank: index + 1,
                name: crime.crime_name || '未知罪名',
                confidence: confidencePercent.toFixed(1),
                confidenceLevel: this.getConfidenceLevel(confidence),
                article: crime.article_number,
                description: crime.description,
                reasoning: crime.reasoning,
                hasArticle: !!crime.article_number,
                hasDescription: !!crime.description,
                hasReasoning: !!crime.reasoning
            };
        });
    }

    /**
     * 格式化增强内容
     */
    formatEnhancedContent(content, type) {
        if (!content) return null;

        const methods = {
            'query2doc': '基于上下文语义扩展生成',
            'hyde': 'HyDE (Hypothetical Document Embeddings) 生成'
        };

        const badges = {
            'query2doc': 'AI生成',
            'hyde': 'HyDE技术'
        };

        const icons = {
            'query2doc': '📝 增强查询内容',
            'hyde': '💡 假设回答内容'
        };

        return {
            type: icons[type] || '📄 增强内容',
            length: this.formatCharacterCount(content),
            text: content,
            method: methods[type] || '智能生成',
            badge: badges[type] || 'AI技术',
            preview: content.length > 300 ? content.substring(0, 300) + '...' : content,
            isLong: content.length > 300
        };
    }

    /**
     * 格式化技术详情
     */
    formatTechnicalDetails(moduleTrace, additionalInfo = {}) {
        const items = [];

        // 基础信息
        if (additionalInfo.method) {
            items.push({
                label: '处理方法：',
                value: additionalInfo.method,
                class: 'method-name'
            });
        }

        // 处理时间
        items.push({
            label: '处理时间：',
            value: this.formatProcessingTime(moduleTrace.processing_time_ms),
            class: 'processing-time'
        });

        // 状态
        items.push({
            label: '模块状态：',
            value: this.getStatusDisplayName(moduleTrace.status),
            class: `status-${moduleTrace.status}`
        });

        // 置信度
        if (moduleTrace.confidence_score) {
            items.push({
                label: '置信度：',
                value: this.formatConfidence(moduleTrace.confidence_score)
            });
        }

        // 额外信息
        Object.entries(additionalInfo).forEach(([key, value]) => {
            if (key !== 'method' && value) {
                items.push({
                    label: `${key}：`,
                    value: String(value)
                });
            }
        });

        return items;
    }

    /**
     * 检查数据完整性
     */
    validateTraceData(trace) {
        const issues = [];

        if (!trace) {
            issues.push('缺少完整的trace数据');
            return { isValid: false, issues };
        }

        if (!trace.request_id) {
            issues.push('缺少请求ID');
        }

        if (!trace.user_query) {
            issues.push('缺少用户查询');
        }

        if (!trace.total_duration_ms) {
            issues.push('缺少总耗时信息');
        }

        return {
            isValid: issues.length === 0,
            issues: issues
        };
    }

    /**
     * 生成调试摘要
     */
    generateDebugSummary(trace) {
        const validation = this.validateTraceData(trace);
        if (!validation.isValid) {
            return {
                status: 'error',
                message: '数据不完整',
                issues: validation.issues
            };
        }

        const stages = [];
        if (trace.classification) stages.push('问题分类');
        if (trace.extraction) stages.push('信息提取');
        if (trace.routing) stages.push('路由决策');
        if (trace.searches) stages.push('多路搜索');
        if (trace.fusion) stages.push('结果融合');

        const searchStats = this.formatSearchStats(trace.searches);
        const performance = this.formatPerformanceMetrics(trace);

        return {
            status: 'success',
            requestId: trace.request_id,
            query: trace.user_query,
            stagesCompleted: stages,
            searchStats: searchStats,
            performance: performance,
            totalStages: stages.length,
            processingMode: trace.processing_mode || 'standard'
        };
    }
}