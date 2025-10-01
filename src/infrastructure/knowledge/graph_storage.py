#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱存储管理
负责知识图谱数据的持久化、加载和缓存管理
"""

import pickle
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class GraphStorage:
    """知识图谱存储管理器"""

    def __init__(self, config=None):
        """
        初始化存储管理器

        Args:
            config: 配置对象，包含存储路径等信息
        """
        self.config = config

        # 默认存储路径
        if config and hasattr(config, 'KG_STORAGE_PATH'):
            self.storage_path = Path(config.KG_STORAGE_PATH)
        else:
            self.storage_path = Path("./data/processed/knowledge_graph.pkl")

        # 元数据存储路径
        self.metadata_path = self.storage_path.with_suffix('.meta.json')

        # 确保存储目录存在
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"图谱存储管理器初始化: {self.storage_path}")

    def save_graph_data(self, relation_data: Dict[str, Any], force_rebuild: bool = False) -> bool:
        """
        保存知识图谱数据

        Args:
            relation_data: 关系数据
            force_rebuild: 是否强制重建

        Returns:
            保存是否成功
        """
        try:
            # 检查是否需要保存
            if not force_rebuild and self.is_graph_available():
                existing_meta = self._load_metadata()
                if existing_meta and self._is_data_unchanged(relation_data, existing_meta):
                    logger.info("图谱数据未发生变化，跳过保存")
                    return True

            start_time = time.time()

            # 保存关系数据
            with open(self.storage_path, 'wb') as f:
                pickle.dump(relation_data, f, protocol=pickle.HIGHEST_PROTOCOL)

            # 保存元数据
            metadata = self._generate_metadata(relation_data)
            self._save_metadata(metadata)

            save_time = time.time() - start_time
            logger.info(f"知识图谱数据保存成功: {self.storage_path}, 耗时{save_time:.2f}s")
            logger.info(f"图谱规模: {metadata['total_crimes']}种罪名, {metadata['total_articles']}个法条, {metadata['total_relations']}个关系")

            return True

        except Exception as e:
            logger.error(f"保存知识图谱数据失败: {e}")
            return False

    def load_graph_data(self) -> Optional[Dict[str, Any]]:
        """
        加载知识图谱数据

        Returns:
            关系数据，如果加载失败返回None
        """
        if not self.is_graph_available():
            logger.warning(f"知识图谱文件不存在: {self.storage_path}")
            return None

        try:
            start_time = time.time()

            with open(self.storage_path, 'rb') as f:
                relation_data = pickle.load(f)

            load_time = time.time() - start_time

            # 验证数据完整性
            if not self._validate_data_integrity(relation_data):
                logger.error("知识图谱数据完整性验证失败")
                return None

            logger.info(f"知识图谱数据加载成功, 耗时{load_time:.2f}s")
            return relation_data

        except Exception as e:
            logger.error(f"加载知识图谱数据失败: {e}")
            return None

    def is_graph_available(self) -> bool:
        """
        检查知识图谱是否可用

        Returns:
            图谱文件是否存在且有效
        """
        if not self.storage_path.exists():
            return False

        # 检查文件大小（至少应该有一些内容）
        if self.storage_path.stat().st_size < 100:
            logger.warning(f"知识图谱文件过小，可能损坏: {self.storage_path}")
            return False

        return True

    def get_graph_info(self) -> Dict[str, Any]:
        """
        获取知识图谱信息

        Returns:
            图谱基本信息
        """
        info = {
            'available': self.is_graph_available(),
            'storage_path': str(self.storage_path),
            'file_size_mb': 0,
            'last_modified': None,
            'metadata': {}
        }

        if info['available']:
            # 文件大小
            file_size = self.storage_path.stat().st_size
            info['file_size_mb'] = round(file_size / (1024 * 1024), 2)

            # 最后修改时间
            timestamp = self.storage_path.stat().st_mtime
            info['last_modified'] = datetime.fromtimestamp(timestamp).isoformat()

            # 元数据
            metadata = self._load_metadata()
            if metadata:
                info['metadata'] = metadata

        return info

    def rebuild_graph(self, data_loader) -> bool:
        """
        重建知识图谱

        Args:
            data_loader: 数据加载器

        Returns:
            重建是否成功
        """
        try:
            logger.info("开始重建知识图谱...")

            # 删除现有文件
            if self.storage_path.exists():
                self.storage_path.unlink()
            if self.metadata_path.exists():
                self.metadata_path.unlink()

            # 重新构建
            from .relation_extractor import RelationExtractor

            extractor = RelationExtractor(data_loader)
            relation_data = extractor.extract_relations_from_cases()

            if relation_data.get('success', False):
                return self.save_graph_data(relation_data, force_rebuild=True)
            else:
                logger.error("关系抽取失败，无法重建图谱")
                return False

        except Exception as e:
            logger.error(f"重建知识图谱失败: {e}")
            return False

    def _generate_metadata(self, relation_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成元数据"""
        return {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'total_crimes': relation_data.get('total_crimes', 0),
            'total_articles': relation_data.get('total_articles', 0),
            'total_relations': relation_data.get('total_relations', 0),
            'data_hash': self._calculate_data_hash(relation_data),
            'extraction_summary': relation_data.get('extraction_summary', {}),
            'file_size_bytes': 0  # 将在保存后更新
        }

    def _save_metadata(self, metadata: Dict[str, Any]):
        """保存元数据"""
        try:
            # 更新文件大小
            if self.storage_path.exists():
                metadata['file_size_bytes'] = self.storage_path.stat().st_size

            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"保存元数据失败: {e}")

    def _load_metadata(self) -> Optional[Dict[str, Any]]:
        """加载元数据"""
        if not self.metadata_path.exists():
            return None

        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载元数据失败: {e}")
            return None

    def _calculate_data_hash(self, relation_data: Dict[str, Any]) -> str:
        """计算数据哈希值（用于检测数据变化）"""
        try:
            # 使用关键统计信息生成简单哈希
            key_info = {
                'total_crimes': relation_data.get('total_crimes', 0),
                'total_articles': relation_data.get('total_articles', 0),
                'total_relations': relation_data.get('total_relations', 0)
            }
            return str(hash(str(sorted(key_info.items()))))
        except:
            return str(time.time())

    def _is_data_unchanged(self, new_data: Dict[str, Any], existing_meta: Dict[str, Any]) -> bool:
        """检查数据是否未发生变化"""
        try:
            new_hash = self._calculate_data_hash(new_data)
            existing_hash = existing_meta.get('data_hash', '')
            return new_hash == existing_hash
        except:
            return False

    def _validate_data_integrity(self, relation_data: Dict[str, Any]) -> bool:
        """验证数据完整性"""
        try:
            # 检查必要字段
            required_fields = ['success', 'crime_article_mapping', 'article_crime_mapping']
            for field in required_fields:
                if field not in relation_data:
                    logger.error(f"数据缺少必要字段: {field}")
                    return False

            # 检查数据是否为空
            if not relation_data.get('success', False):
                logger.error("关系数据标记为失败状态")
                return False

            # 检查映射数据
            crime_mapping = relation_data.get('crime_article_mapping', {})
            article_mapping = relation_data.get('article_crime_mapping', {})

            if not crime_mapping and not article_mapping:
                logger.error("关系映射数据为空")
                return False

            logger.debug(f"数据完整性验证通过: {len(crime_mapping)}种罪名, {len(article_mapping)}个法条")
            return True

        except Exception as e:
            logger.error(f"数据完整性验证异常: {e}")
            return False

    def export_graph_data(self, output_path: str, format: str = 'json') -> bool:
        """
        导出知识图谱数据

        Args:
            output_path: 输出文件路径
            format: 导出格式 ('json', 'csv')

        Returns:
            导出是否成功
        """
        try:
            relation_data = self.load_graph_data()
            if not relation_data:
                logger.error("无法加载图谱数据进行导出")
                return False

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if format.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(relation_data, f, indent=2, ensure_ascii=False)

            elif format.lower() == 'csv':
                import csv
                # 导出为CSV格式（关系表）
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Crime', 'Article', 'CaseCount', 'Type'])

                    # 罪名->法条关系
                    for crime, articles in relation_data['crime_article_mapping'].items():
                        for article, count in articles.items():
                            writer.writerow([f"{crime}罪", f"第{article}条", count, "crime_to_article"])

            logger.info(f"知识图谱数据导出成功: {output_file}")
            return True

        except Exception as e:
            logger.error(f"导出知识图谱数据失败: {e}")
            return False