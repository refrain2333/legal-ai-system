#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证运行器 (临时工具)
一键运行所有数据验证，生成综合报告

使用方法:
python tools/data_validation/quick_validation_runner.py

注意: 这是一个临时验证工具，完成验证后可以删除
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入验证模块
from tools.data_validation.vector_format_checker import VectorFormatChecker
from tools.data_validation.data_integrity_checker import DataIntegrityChecker

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickValidationRunner:
    """快速验证运行器"""
    
    def __init__(self, data_root: Path = None):
        """初始化验证器"""
        self.data_root = data_root or project_root / "data" / "processed"
        self.output_dir = project_root / "tools" / "data_validation"
        
        # 初始化各个检查器
        self.format_checker = VectorFormatChecker(self.data_root)
        self.integrity_checker = DataIntegrityChecker(self.data_root)
        
        # 验证结果
        self.results = {}
        
    def run_all_validations(self) -> Dict[str, Any]:
        """运行所有验证"""
        print("🚀 " + "=" * 60)
        print("🚀 法智导航数据验证套件 - 快速验证")
        print("🚀 " + "=" * 60)
        print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 数据路径: {self.data_root}")
        
        overall_start_time = time.time()
        
        # 1. 向量格式检查
        print(f"\n" + "🔍" * 20 + " 步骤 1: 向量格式检查 " + "🔍" * 20)
        format_start_time = time.time()
        
        try:
            self.results['format_check'] = self.format_checker.check_all_vectors()
            format_duration = time.time() - format_start_time
            print(f"✅ 向量格式检查完成 (耗时: {format_duration:.2f}秒)")
        except Exception as e:
            format_duration = time.time() - format_start_time
            print(f"❌ 向量格式检查失败: {e}")
            self.results['format_check'] = {'error': str(e), 'duration': format_duration}
        
        # 2. 数据完整性检查
        print(f"\n" + "🔗" * 20 + " 步骤 2: 数据完整性检查 " + "🔗" * 20)
        integrity_start_time = time.time()
        
        try:
            self.results['integrity_check'] = self.integrity_checker.check_all_integrity()
            integrity_duration = time.time() - integrity_start_time
            print(f"✅ 数据完整性检查完成 (耗时: {integrity_duration:.2f}秒)")
        except Exception as e:
            integrity_duration = time.time() - integrity_start_time
            print(f"❌ 数据完整性检查失败: {e}")
            self.results['integrity_check'] = {'error': str(e), 'duration': integrity_duration}
        
        # 3. 生成综合报告
        print(f"\n" + "📋" * 20 + " 步骤 3: 生成综合报告 " + "📋" * 20)
        
        overall_duration = time.time() - overall_start_time
        self.results['overall_summary'] = self._generate_overall_summary(overall_duration)
        
        # 4. 保存报告
        self._save_reports()
        
        print(f"\n🎉 所有验证完成! 总耗时: {overall_duration:.2f}秒")
        
        return self.results
    
    def _generate_overall_summary(self, total_duration: float) -> Dict[str, Any]:
        """生成综合总结"""
        print("📊 生成综合分析报告...")
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_duration': total_duration,
            'validation_status': 'unknown',
            'critical_issues': [],
            'warnings': [],
            'recommendations': [],
            'statistics': {}
        }
        
        critical_issues = []
        warnings = []
        recommendations = []
        
        # 分析格式检查结果
        format_result = self.results.get('format_check', {})
        if 'error' in format_result:
            critical_issues.append(f"向量格式检查失败: {format_result['error']}")
        else:
            format_summary = format_result.get('summary', {})
            if format_summary.get('failed_files', 0) > 0:
                critical_issues.append("部分向量文件格式错误")
            
            format_issues = format_summary.get('issues_found', [])
            for issue in format_issues:
                if any(keyword in issue for keyword in ['维度', 'NaN', 'Inf', '缺少字段']):
                    critical_issues.append(f"格式问题: {issue}")
                else:
                    warnings.append(f"格式警告: {issue}")
        
        # 分析完整性检查结果
        integrity_result = self.results.get('integrity_check', {})
        if 'error' in integrity_result:
            critical_issues.append(f"数据完整性检查失败: {integrity_result['error']}")
        else:
            integrity_summary = integrity_result.get('summary', {})
            if integrity_summary.get('overall_status') == 'critical':
                critical_issues.extend(integrity_summary.get('critical_issues', []))
            elif integrity_summary.get('overall_status') == 'warning':
                warnings.extend(integrity_summary.get('warnings', []))
        
        # 确定整体状态
        if critical_issues:
            summary['validation_status'] = 'failed'
            validation_emoji = "❌"
            status_text = "验证失败 - 发现关键问题"
        elif warnings:
            summary['validation_status'] = 'warning'
            validation_emoji = "⚠️"
            status_text = "验证通过但有警告"
        else:
            summary['validation_status'] = 'passed'
            validation_emoji = "✅"
            status_text = "验证完全通过"
        
        summary['critical_issues'] = critical_issues
        summary['warnings'] = warnings
        
        # 生成统计信息
        statistics = self._collect_statistics()
        summary['statistics'] = statistics
        
        # 生成建议
        recommendations = self._generate_comprehensive_recommendations(critical_issues, warnings)
        summary['recommendations'] = recommendations
        
        # 打印总结
        print(f"\n" + "=" * 60)
        print(f"📋 综合验证结果")
        print(f"=" * 60)
        print(f"{validation_emoji} 验证状态: {status_text}")
        print(f"⏱️ 总耗时: {total_duration:.2f}秒")
        
        if statistics:
            print(f"\n📊 数据统计:")
            for key, value in statistics.items():
                print(f"   {key}: {value}")
        
        if critical_issues:
            print(f"\n🚨 关键问题 ({len(critical_issues)}个):")
            for issue in critical_issues:
                print(f"   - {issue}")
        
        if warnings:
            print(f"\n⚠️ 警告 ({len(warnings)}个):")
            for warning in warnings:
                print(f"   - {warning}")
        
        if recommendations:
            print(f"\n💡 建议:")
            for rec in recommendations:
                print(f"   - {rec}")
        
        return summary
    
    def _collect_statistics(self) -> Dict[str, Any]:
        """收集统计信息"""
        stats = {}
        
        # 从格式检查收集统计
        format_result = self.results.get('format_check', {})
        if 'articles' in format_result and 'cases' in format_result:
            # 文件大小统计
            articles_size = format_result['articles'].get('file_size_mb', 0)
            cases_size = format_result['cases'].get('file_size_mb', 0)
            stats['向量文件总大小(MB)'] = f"{articles_size + cases_size:.2f}"
            
            # 向量数量统计
            if 'checks' in format_result['articles'] and 'count_consistency' in format_result['articles']['checks']:
                articles_count = format_result['articles']['checks']['count_consistency'].get('total_count', 0)
                stats['法条数量'] = articles_count
            
            if 'checks' in format_result['cases'] and 'count_consistency' in format_result['cases']['checks']:
                cases_count = format_result['cases']['checks']['count_consistency'].get('total_count', 0)
                stats['案例数量'] = cases_count
                stats['总文档数量'] = articles_count + cases_count
        
        # 从完整性检查收集统计
        integrity_result = self.results.get('integrity_check', {})
        if 'file_consistency' in integrity_result:
            consistency = integrity_result['file_consistency']
            if consistency.get('articles', {}).get('count_match') and consistency.get('cases', {}).get('count_match'):
                stats['数据一致性'] = "✅ 一致"
            else:
                stats['数据一致性'] = "❌ 不一致"
        
        return stats
    
    def _generate_comprehensive_recommendations(self, critical_issues: List[str], warnings: List[str]) -> List[str]:
        """生成综合建议"""
        recommendations = []
        
        if critical_issues:
            recommendations.append("🚨 优先处理关键问题，这些问题可能导致系统无法正常运行")
            
            if any("格式错误" in issue or "格式检查失败" in issue for issue in critical_issues):
                recommendations.append("重新运行数据向量化流程，确保生成正确格式的向量文件")
            
            if any("完整性检查失败" in issue for issue in critical_issues):
                recommendations.append("检查数据文件是否损坏，可能需要重新生成数据")
            
            if any("数量不一致" in issue or "ID映射" in issue for issue in critical_issues):
                recommendations.append("重新同步向量数据和原始数据，确保数据对应关系正确")
        
        elif warnings:
            recommendations.append("⚠️ 处理警告项以提升数据质量")
            
            if any("零向量" in warning for warning in warnings):
                recommendations.append("检查导致零向量的原始文档，重新处理这些文档")
            
            if any("内容为空" in warning for warning in warnings):
                recommendations.append("补充缺失的文档内容或从数据集中移除空文档")
        
        else:
            recommendations.append("🎉 数据验证通过，系统可以正常使用")
            recommendations.append("定期运行此验证工具以确保数据质量")
        
        # 通用建议
        recommendations.append("💾 建议备份当前数据状态")
        if critical_issues or warnings:
            recommendations.append("📝 记录发现的问题，用于改进数据处理流程")
        
        return recommendations
    
    def _save_reports(self):
        """保存验证报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存完整JSON报告
        json_file = self.output_dir / f"complete_validation_report_{timestamp}.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
            print(f"📄 完整报告已保存: {json_file}")
        except Exception as e:
            print(f"⚠️ 保存JSON报告失败: {e}")
        
        # 生成人类可读的文本报告
        text_file = self.output_dir / f"validation_summary_{timestamp}.txt"
        try:
            with open(text_file, 'w', encoding='utf-8') as f:
                self._write_text_report(f, timestamp)
            print(f"📄 摘要报告已保存: {text_file}")
        except Exception as e:
            print(f"⚠️ 保存文本报告失败: {e}")
    
    def _write_text_report(self, file, timestamp: str):
        """写入文本报告"""
        file.write("法智导航数据验证报告\n")
        file.write("=" * 50 + "\n\n")
        file.write(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"数据路径: {self.data_root}\n\n")
        
        overall_summary = self.results.get('overall_summary', {})
        
        file.write("验证结果:\n")
        file.write("-" * 20 + "\n")
        status = overall_summary.get('validation_status', 'unknown')
        if status == 'passed':
            file.write("✅ 验证通过\n")
        elif status == 'warning':
            file.write("⚠️ 验证通过但有警告\n")
        else:
            file.write("❌ 验证失败\n")
        
        file.write(f"总耗时: {overall_summary.get('total_duration', 0):.2f}秒\n\n")
        
        # 统计信息
        statistics = overall_summary.get('statistics', {})
        if statistics:
            file.write("数据统计:\n")
            file.write("-" * 20 + "\n")
            for key, value in statistics.items():
                file.write(f"{key}: {value}\n")
            file.write("\n")
        
        # 关键问题
        critical_issues = overall_summary.get('critical_issues', [])
        if critical_issues:
            file.write("关键问题:\n")
            file.write("-" * 20 + "\n")
            for issue in critical_issues:
                file.write(f"- {issue}\n")
            file.write("\n")
        
        # 警告
        warnings = overall_summary.get('warnings', [])
        if warnings:
            file.write("警告:\n")
            file.write("-" * 20 + "\n")
            for warning in warnings:
                file.write(f"- {warning}\n")
            file.write("\n")
        
        # 建议
        recommendations = overall_summary.get('recommendations', [])
        if recommendations:
            file.write("建议:\n")
            file.write("-" * 20 + "\n")
            for rec in recommendations:
                file.write(f"- {rec}\n")
            file.write("\n")
        
        file.write("=" * 50 + "\n")
        file.write("报告结束\n")


def main():
    """主函数"""
    try:
        print("🏁 启动快速验证...")
        
        runner = QuickValidationRunner()
        results = runner.run_all_validations()
        
        # 根据验证结果设置退出码
        overall_summary = results.get('overall_summary', {})
        status = overall_summary.get('validation_status', 'unknown')
        
        if status == 'failed':
            print(f"\n❌ 验证失败，请查看报告解决问题")
            sys.exit(1)
        elif status == 'warning':
            print(f"\n⚠️ 验证通过但有警告，建议优化")
            sys.exit(0)
        else:
            print(f"\n✅ 验证完全通过，数据状态良好")
            sys.exit(0)
        
    except KeyboardInterrupt:
        print(f"\n🛑 用户中断验证")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 验证过程出现异常: {e}")
        logger.exception("Quick validation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()