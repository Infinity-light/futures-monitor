# Cytopia Workflow 统一仓库 PRD

## 项目背景

当前有两个独立的Git仓库导致版本不同步问题：
- `Cytopia-claude-code-workkit-plugin` (开发源码库) - workflow-kit v2.3.0
- `cytopia-marketplace` (独立发布库) - workflow-kit v2.2.0

用户需要采用方案A：统一仓库架构，简化维护流程。

## 需求目标

1. **合并两个仓库**：将开发代码和marketplace索引合并到单一仓库
2. **统一版本管理**：消除版本不一致问题
3. **简化远程同步**：让用户通过单一marketplace获取所有插件
4. **支持插件扩展**：方便后续添加新插件

## 功能需求

### 1. 仓库结构重组
- 重命名 `Cytopia-claude-code-workkit-plugin` → `cytopia-workflow`（更清晰）
- 将 `cytopia-marketplace` 的内容整合进统一仓库
- 保留所有现有skill代码（workflow-kit v2.3.0）

### 2. Marketplace 配置更新
- 更新 `.claude-plugin/marketplace.json`
- 使用 `source: path` 指向本地路径
- 版本号同步为 2.3.0

### 3. 目录结构规范
```
cytopia-workflow/
├── .claude-plugin/
│   └── marketplace.json          # 插件索引
├── skills/
│   └── workflow-kit/             # 核心skill代码
│       ├── skills/
│       │   ├── discovery/
│       │   ├── planning/
│       │   ├── execution/
│       │   ├── diagnosis/
│       │   ├── verification/
│       │   ├── deploy/
│       │   └── documentation-update/
│       ├── hooks/
│       ├── .claude/
│       └── CLAUDE.md
├── README.md
└── CHANGELOG.md
```

### 4. 后续扩展支持
- 新插件放在 `skills/<plugin-name>/`
- 在 `marketplace.json` 中添加条目
- 每个插件独立版本管理

## 验收标准

- [ ] 单一仓库包含完整代码和marketplace配置
- [ ] marketplace.json 版本号为 2.3.0
- [ ] 目录结构清晰，符合Claude Code插件规范
- [ ] README.md 说明安装和使用方法
- [ ] Git历史完整保留

## 技术约束

- 保持现有skill功能不变
- 不改变文件内容，只调整结构
- 兼容Claude Code的marketplace机制
