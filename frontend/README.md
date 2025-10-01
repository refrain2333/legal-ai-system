# 前端文件整理规范

## 📁 目录说明

```
frontend/
├── assets/
│   └── css/
│       ├── shared/     # 可复用样式
│       └── pages/      # 页面专用样式
├── js/
│   ├── components/     # 可复用组件
│   ├── pages/          # 页面专用脚本
│   ├── utils/          # 工具函数
│   └── app.js          # 主应用脚本
├── pages/              # 页面文件
└── index.html          # 首页
```

## 📋 存放内容

### assets/css/shared/
- **theme.css** - 主题变量、基础样式
- **components.css** - 可复用组件样式
- **navigation.css** - 导航栏样式（最后加载）
- **core-layout.css** - 核心布局样式
- **其他.css** - 通用功能模块样式

### assets/css/pages/
- **home.css** - 首页专用样式
- **basic-search.css** - 基础搜索页专用样式
- **其他页面.css** - 各页面专用样式

### js/components/
- 可在多个页面复用的组件
- 如：NavigationBar.js

### js/pages/
- 页面特定的业务逻辑
- 如：basic-search.js

### js/utils/
- 通用工具函数
- 如：DataFormatter.js

### pages/
- 子页面HTML文件
- 如：basic-search.html

## ⚠️ 规则

### 引用路径
- **根目录页面**: `./assets/css/shared/` `./assets/css/pages/`
- **pages子目录**: `../assets/css/shared/` `../assets/css/pages/`

### 样式加载顺序
1. theme.css（最先）
2. 共用组件样式
3. 页面专用样式
4. navigation.css（最后）

### 样式分类原则
- **shared/**: 多页面可复用的样式
- **pages/**: 单页面专用的样式

### 禁止
- 空目录
- 重复功能文件
- 混合职责文件