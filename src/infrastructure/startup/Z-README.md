# 启动模块文档

## 概述
启动模块负责管理系统启动流程，提供实时状态监控和进度展示功能。

## 文件结构
```
startup/
├── startup_manager.py   # 启动管理器核心实现
└── __init__.py          # 模块导出
```

## 核心功能
- 实时监控启动进度
- 管理多个启动步骤
- 支持状态观察者模式
- 自动错误处理
- 耗时统计

## 主要类说明

### LoadingStatus (枚举)
系统启动状态：
- `PENDING` - 等待中
- `LOADING` - 加载中  
- `SUCCESS` - 成功
- `ERROR` - 错误
- `SKIPPED` - 已跳过

### LoadingStep (数据类)
每个启动步骤的信息：
- `id` - 步骤标识
- `name` - 步骤名称
- `status` - 当前状态
- `progress` - 进度百分比
- `duration` - 耗时(秒)

### StartupManager (主类)
启动流程管理器，提供完整的启动控制。

## 使用方法

### 基本使用
```python
from src.infrastructure.startup import get_startup_manager

# 获取管理器
manager = get_startup_manager()

# 启动系统
manager.start_system(data_loader)

# 获取当前状态
status = manager.get_status()
print(f"当前进度: {status.overall_progress}%")
```

### 添加状态监听
```python
def update_ui(status):
    print(f"步骤 {status.current_step}: {status.overall_progress}%")

manager.add_observer(update_ui)
```

### 手动控制步骤
```python
# 开始步骤
manager.start_step("config_check")

# 更新进度
manager.update_step_progress("config_check", 50.0)

# 完成步骤
manager.complete_step("config_check", success=True)
```

## 预定义启动步骤

1. **config_check** - 配置检查
2. **compatibility_init** - 兼容性初始化  
3. **vectors_loading** - 向量数据加载
4. **model_loading** - AI模型加载
5. **search_engine_init** - 搜索引擎初始化
6. **health_check** - 系统健康检查

## 错误处理

```python
try:
    manager.start_system(data_loader)
except Exception as e:
    # 查看哪个步骤失败
    status = manager.get_status()
    for step in status.steps.values():
        if step.status == LoadingStatus.ERROR:
            print(f"{step.name} 失败: {step.error_message}")
```

## 性能监控

启动管理器会自动记录：
- 每个步骤的耗时
- 总体启动时间
- 内存使用情况
- 错误统计

## 示例代码

```python
# 完整启动示例
from src.infrastructure.startup import get_startup_manager
from src.infrastructure.storage.data_loader import get_data_loader

def main():
    # 初始化
    manager = get_startup_manager()
    data_loader = get_data_loader()
    
    # 添加进度监听
    def log_progress(status):
        print(f"进度: {status.overall_progress:.1f}%")
    
    manager.add_observer(log_progress)
    
    # 启动系统
    try:
        manager.start_system(data_loader)
        print("启动成功!")
    except Exception as e:
        print(f"启动失败: {e}")

if __name__ == "__main__":
    main()
```

## 注意事项

1. 线程安全：所有操作都是线程安全的
2. 状态重置：每次启动前会自动重置状态
3. 错误恢复：支持步骤级别的重试机制
4. 内存使用：状态数据占用内存较小

---
**版本**: 1.0  
**更新日期**: 2025-09-17
