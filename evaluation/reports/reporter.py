#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评估报告生成器
生成详细的评估报告
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)


class EvaluationReporter:
    """评估报告生成器"""
    
    def __init__(self, results: Dict[str, Any]):
        """
        初始化报告生成器
        
        Args:
            results: 评估结果数据
        """
        self.results = results
        self.report_lines = []
    
    def generate_text_report(self) -> str:
        """
        生成文本格式的报告
        
        Returns:
            报告文本
        """
        self.report_lines = []
        
        # 标题
        self._add_header()
        
        # 概要信息
        self._add_summary_section()
        
        # 详细指标
        self._add_metrics_section()
        
        # 按查询类型的结果
        self._add_type_specific_results()
        
        # 建议和结论
        self._add_recommendations()
        
        return '\n'.join(self.report_lines)
    
    def _add_header(self):
        """添加报告头部"""
        self.report_lines.extend([
            "=" * 80,
            "法律搜索系统评估报告",
            "=" * 80,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"评估开始: {self.results.get('start_time', 'N/A')}",
            f"评估结束: {self.results.get('end_time', 'N/A')}",
            f"总耗时: {self.results.get('duration_seconds', 0):.2f} 秒",
            f"测试查询数: {self.results.get('test_queries_count', 0)}",
            "",
        ])
    
    def _add_summary_section(self):
        """添加摘要部分"""
        summary = self.results.get('summary', {})
        
        self.report_lines.extend([
            "-" * 80,
            "执行摘要",
            "-" * 80,
            f"综合得分: {summary.get('overall_score', 0):.2%}",
            "",
            "关键指标:",
        ])
        
        for metric, value in summary.get('key_metrics', {}).items():
            self.report_lines.append(f"  - {metric}: {value:.4f}")
        
        if summary.get('strengths'):
            self.report_lines.extend(["", "优势:"])
            for strength in summary['strengths']:
                self.report_lines.append(f"  + {strength}")
        
        if summary.get('weaknesses'):
            self.report_lines.extend(["", "待改进:"])
            for weakness in summary['weaknesses']:
                self.report_lines.append(f"  - {weakness}")
        
        self.report_lines.append("")
    
    def _add_metrics_section(self):
        """添加详细指标部分"""
        metrics = self.results.get('metrics', {})
        overall = metrics.get('overall', {})
        
        self.report_lines.extend([
            "-" * 80,
            "总体性能指标",
            "-" * 80,
        ])
        
        # 按K值组织指标
        for k in [1, 3, 5, 10]:
            k_metrics = {
                key: value for key, value in overall.items()
                if f'@{k}_' in key
            }
            
            if k_metrics:
                self.report_lines.append(f"\n@{k} 指标:")
                for metric_name, value in sorted(k_metrics.items()):
                    clean_name = metric_name.replace(f'@{k}_', ' ').replace('_', ' ').title()
                    self.report_lines.append(f"  {clean_name}: {value:.4f}")
        
        # 其他指标
        other_metrics = {
            key: value for key, value in overall.items()
            if '@' not in key and 'semantic' not in key
        }
        
        if other_metrics:
            self.report_lines.append("\n其他指标:")
            for metric_name, value in sorted(other_metrics.items()):
                clean_name = metric_name.replace('_', ' ').title()
                self.report_lines.append(f"  {clean_name}: {value:.4f}")
        
        self.report_lines.append("")
    
    def _add_type_specific_results(self):
        """添加按查询类型的结果"""
        metrics_by_type = self.results.get('metrics', {}).get('by_type', {})
        
        self.report_lines.extend([
            "-" * 80,
            "分类评估结果",
            "-" * 80,
        ])
        
        type_names = {
            'article_to_cases': '法条→案例搜索',
            'case_to_articles': '案例→法条搜索',
            'crime_keywords': '罪名关键词搜索',
            'crime_consistency': '罪名一致性评估',
            'mixed': '混合搜索'
        }
        
        for query_type, type_metrics in metrics_by_type.items():
            type_name = type_names.get(query_type, query_type)
            self.report_lines.extend([
                "",
                f"【{type_name}】",
                "-" * 40,
            ])
            
            # 特殊处理罪名一致性评估显示
            if query_type == 'crime_consistency':
                # 优先显示案例级覆盖率指标
                priority_metrics = ['case_coverage_rate_mean', 'overall_case_coverage_rate', 
                                  'total_covered_cases', 'total_all_cases']
                traditional_metrics = ['consistency_precision_mean', 'consistency_recall_mean', 
                                     'consistency_jaccard_mean']
                
                metric_names = {
                    'case_coverage_rate_mean': '案例覆盖率(平均)',
                    'overall_case_coverage_rate': '案例覆盖率(整体)',
                    'total_covered_cases': '覆盖案例数',
                    'total_all_cases': '总案例数',
                    'consistency_precision_mean': '传统精确率',
                    'consistency_recall_mean': '传统召回率', 
                    'consistency_jaccard_mean': 'Jaccard系数'
                }
                
                # 显示核心指标
                self.report_lines.append("  🎯 核心指标（案例级覆盖率）:")
                for metric in priority_metrics:
                    if metric in type_metrics:
                        clean_name = metric_names.get(metric, metric)
                        value = type_metrics[metric]
                        if 'total_' in metric:
                            self.report_lines.append(f"    {clean_name}: {int(value)}")
                        else:
                            self.report_lines.append(f"    {clean_name}: {value:.4f} ({value*100:.1f}%)")
                
                # 显示传统指标（参考）
                self.report_lines.append("  📊 传统指标（参考）:")
                for metric in traditional_metrics:
                    if metric in type_metrics:
                        clean_name = metric_names.get(metric, metric)
                        value = type_metrics[metric]
                        self.report_lines.append(f"    {clean_name}: {value:.4f} ({value*100:.1f}%)")
                
                # 显示查询数量
                if 'total_queries' in type_metrics:
                    queries_count = int(type_metrics['total_queries'])
                    self.report_lines.append(f"  📝 测试查询数量: {queries_count}")
            else:
                # 其他类型使用通用指标展示
                key_metrics = ['precision@5_mean', 'recall@5_mean', 'f1@5_mean',
                              'average_precision_mean', 'semantic_accuracy']
                
                for metric in key_metrics:
                    if metric in type_metrics:
                        clean_name = metric.replace('@5_mean', '').replace('_', ' ').title()
                        value = type_metrics[metric]
                        self.report_lines.append(f"  {clean_name}: {value:.4f}")
        
        self.report_lines.append("")
    
    def _add_recommendations(self):
        """添加建议部分"""
        summary = self.results.get('summary', {})
        recommendations = summary.get('recommendations', [])
        
        if recommendations:
            self.report_lines.extend([
                "-" * 80,
                "改进建议",
                "-" * 80,
            ])
            
            for i, rec in enumerate(recommendations, 1):
                self.report_lines.append(f"{i}. {rec}")
        
        self.report_lines.extend([
            "",
            "=" * 80,
            "报告结束",
            "=" * 80,
        ])
    
    def save_text_report(self, output_path: Path = None) -> Path:
        """
        保存文本报告
        
        Args:
            output_path: 输出路径
            
        Returns:
            保存的文件路径
        """
        if output_path is None:
            import sys
            from pathlib import Path
            # 添加evaluation目录到路径
            eval_root = Path(__file__).resolve().parent.parent
            if str(eval_root) not in sys.path:
                sys.path.insert(0, str(eval_root))
            from config.eval_settings import RESULTS_DIR
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = RESULTS_DIR / f"evaluation_report_{timestamp}.txt"
        
        report_text = self.generate_text_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        logger.info(f"文本报告已保存到: {output_path}")
        return output_path
    
    def generate_json_report(self) -> Dict[str, Any]:
        """
        生成JSON格式的报告
        
        Returns:
            报告字典
        """
        return {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'evaluation_duration': self.results.get('duration_seconds', 0),
                'total_queries': self.results.get('test_queries_count', 0)
            },
            'summary': self.results.get('summary', {}),
            'metrics': self.results.get('metrics', {}),
            'detailed_results': self._summarize_detailed_results()
        }
    
    def _summarize_detailed_results(self) -> Dict[str, Any]:
        """
        汇总详细结果
        
        Returns:
            汇总的详细结果
        """
        detailed = self.results.get('detailed_results', {})
        summary = {}
        
        for query_type, results in detailed.items():
            # 统计成功和失败的查询
            success_count = sum(1 for r in results if not r.get('error'))
            error_count = sum(1 for r in results if r.get('error'))
            
            # 计算平均响应时间
            response_times = [r.get('response_time', 0) for r in results if r.get('response_time')]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            summary[query_type] = {
                'total_queries': len(results),
                'successful': success_count,
                'errors': error_count,
                'avg_response_time': avg_response_time
            }
        
        return summary
    
    def save_json_report(self, output_path: Path = None) -> Path:
        """
        保存JSON报告
        
        Args:
            output_path: 输出路径
            
        Returns:
            保存的文件路径
        """
        if output_path is None:
            import sys
            from pathlib import Path
            # 添加evaluation目录到路径  
            eval_root = Path(__file__).resolve().parent.parent
            if str(eval_root) not in sys.path:
                sys.path.insert(0, str(eval_root))
            from config.eval_settings import RESULTS_DIR
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = RESULTS_DIR / f"evaluation_report_{timestamp}.json"
        
        report_json = self.generate_json_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_json, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON报告已保存到: {output_path}")
        return output_path