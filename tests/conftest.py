"""
pytest配置文件
"""

import pytest
import asyncio
from pathlib import Path
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_legal_text():
    """示例法律文本"""
    return {
        "law": {
            "id": "law_001",
            "title": "合同法第一百零七条",
            "content": "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
            "category": "合同法"
        },
        "case": {
            "id": "case_001", 
            "title": "房屋租赁合同违约案",
            "content": "原告与被告签订房屋租赁合同，被告未按约定支付租金，构成违约。",
            "category": "合同纠纷"
        }
    }


@pytest.fixture
def sample_query():
    """示例查询文本"""
    return "房屋租赁合同违约责任"


@pytest.fixture
def mock_embedding():
    """模拟向量表示"""
    import numpy as np
    return np.random.rand(768).astype(np.float32)