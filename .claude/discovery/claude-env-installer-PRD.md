# PRD: Claude 环境安装程序 GUI 版

## 一、需求理解（为什么）

### 目标
构建一个跨平台的 GUI 工具，帮助用户一键安装 Claude Code 所需的开发环境，并提供便捷的方式启动和管理 cc-switch。

### 交付物清单

- [ ] **Dashboard 仪表盘**
  - [ ] 环境依赖检测（Node.js / Git / Python / UV）
  - [ ] Claude 生态组件状态（Claude Code / MCP / Skills）
  - [ ] 系统信息展示
  - [ ] 一键安装缺失组件

- [ ] **CC Switch 页面**
  - [ ] Claude Code 安装状态检测
  - [ ] 一键安装 Claude Code
  - [ ] 打开 cc-switch（下载/启动）

- [ ] **IDE 启动器**
  - [ ] 检测已安装的 IDE（VS Code / Cursor / Trae）
  - [ ] 启动 IDE 并打开指定目录

- [ ] **工作区管理**
  - [ ] 创建/删除工作区
  - [ ] 关联默认 IDE
  - [ ] 快速打开工作区

### 用户动线

#### 动线 1: 首次使用（从零开始）
```
用户打开应用
    ↓
Dashboard 显示环境检测中...
    ↓
环境检测完成，显示缺失组件（如 Node.js / Git）
    ↓
点击"一键安装缺失组件"
    ↓
安装进度实时显示
    ↓
环境安装完成
    ↓
切换到 CC Switch 页面
    ↓
点击"安装 Claude Code"
    ↓
Claude Code 安装完成
    ↓
提示：是否下载 cc-switch 进行高级管理？
    ↓
下载并启动 cc-switch
```

#### 动线 2: 日常开发
```
用户打开应用
    ↓
Dashboard 显示所有环境已就绪 ✓
    ↓
切换到工作区页面
    ↓
选择工作区 → 点击打开
    ↓
自动启动默认 IDE 并打开项目
```

#### 动线 3: 管理 Claude 生态
```
用户打开应用
    ↓
CC Switch 页面显示 Claude Code 已安装
    ↓
点击"打开 cc-switch"
    ↓
启动 cc-switch 应用（如未安装则先下载）
    ↓
在 cc-switch 中管理 Provider / MCP / Skills
```

### 边界条件

**包含**:
- 基础环境检测与安装（Node.js / Git / Python / UV）
- Claude Code 安装
- cc-switch 下载与启动集成
- IDE 检测与启动
- 工作区管理

**不包含**:
- Provider 管理（由 cc-switch 负责）
- MCP 管理（由 cc-switch 负责）
- Skills 管理（由 cc-switch 负责）
- 用量统计（由 cc-switch 负责）
- 账号切换（由 cc-switch 负责）

---

## 二、调研结论（是什么）

### 2.1 模块拆解

#### M1: 环境依赖检测
**深度分析**:
- Node.js: 检查 `node --version`，检测 nvm 安装
- Git: 检查 `git --version`
- Python: 检查 `python --version` 或 `python3 --version`
- UV: 检查 `uv --version`

**广度对比**:
| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 命令行检测 | 准确，跨平台 | 需要执行命令 | 采用 |
| 注册表检测 | Windows 快 | 不跨平台 | 辅助 |
| 路径检测 | 简单 | 不完整 | 辅助 |

**推荐方案**: 以命令行检测为主，路径检测为辅助

#### M2: Claude Code 安装
**深度分析**:
- 官方安装方式: `npm install -g @anthropic-ai/claude-code`
- 需要前置: Node.js >= 18, Git
- 国内网络可能需要镜像

**广度对比**:
| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| npm 官方源 | 最新版本 | 国内慢 | 默认 |
| npm 淘宝镜像 | 国内快 | 可能延迟 | 备选 |
| 离线安装包 | 无需网络 | 版本旧 | 不支持 |

**推荐方案**: npm 官方源 + 国内镜像自动回退

#### M3: cc-switch 集成
**深度分析**:
- cc-switch 是独立的 Tauri 应用
- 最新版本发布在 GitHub Releases
- Windows: `.msi` 或 `.exe` 安装包

**广度对比**:
| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 内置下载 | 一键获取 | 体积大 | 采用 |
| 提示用户自行下载 | 简单 | 体验差 | 不采用 |
| 命令行集成 | 轻量 | 功能少 | 不采用 |

**推荐方案**: 检测本地是否已安装，如未安装则从 GitHub 下载最新版

#### M4: IDE 检测与启动
**深度分析**:
- VS Code: 注册表 + `code` 命令
- Cursor: 注册表 + `%LOCALAPPDATA%\Programs\cursor\`
- Trae: 注册表 + `%LOCALAPPDATA%\Programs\Trae\`

**推荐方案**: 注册表检测 + 常见路径检测

### 2.2 技术架构选择

基于 cc-switch 的调研，采用以下架构:

```
Frontend (Vue 3 + TypeScript)
    ↓ Tauri IPC
Backend (Rust)
    ↓
系统命令 / 文件系统 / 注册表
```

**选择理由**:
1. 与 cc-switch 一致的技术栈，便于未来集成
2. Tauri 轻量（~15MB vs Electron ~200MB）
3. Rust 系统能力强，适合环境检测

---

## 三、实现方案（怎么办）

### 3.1 系统架构

```
┌─────────────────────────────────────────────┐
│                 Frontend                     │
│  ┌──────────┬──────────┬──────────┐        │
│  │ Dashboard│ CC Switch│ Workspaces│        │
│  └────┬─────┴────┬─────┴────┬─────┘        │
│       └──────────┴──────────┘              │
│                Vue 3 + Pinia               │
└────────────────────┬────────────────────────┘
                     │ Tauri IPC
┌────────────────────▼────────────────────────┐
│                Backend (Rust)               │
│  ┌──────────────┬──────────────┐           │
│  │ Environment  │   Claude     │           │
│  │   Detector   │   Installer  │           │
│  └──────────────┴──────────────┘           │
│  ┌──────────────┬──────────────┐           │
│  │ cc-switch    │   IDE        │           │
│  │ Integration  │   Launcher   │           │
│  └──────────────┴──────────────┘           │
│  ┌──────────────┬──────────────┐           │
│  │   Workspace  │   System     │           │
│  │   Manager    │   Info       │           │
│  └──────────────┴──────────────┘           │
└─────────────────────────────────────────────┘
```

### 3.2 核心功能设计

#### Dashboard 仪表盘

**功能**:
- 环境依赖状态卡片（Node.js / Git / Python / UV）
- Claude Code 安装状态
- 系统信息（OS / 架构 / 主机名）
- 一键安装缺失组件

**数据结构**:
```typescript
interface EnvironmentStatus {
  component: 'node' | 'git' | 'python' | 'uv';
  installed: boolean;
  version?: string;
  required: boolean;
  installUrl?: string;
}

interface DashboardState {
  environment: EnvironmentStatus[];
  claudeCodeInstalled: boolean;
  claudeCodeVersion?: string;
  systemInfo: SystemInfo;
  isDetecting: boolean;
  isInstalling: boolean;
}
```

#### CC Switch 页面

**功能**:
- Claude Code 安装状态检测
- 安装 Claude Code（npm install）
- 打开 cc-switch（下载/启动）
- 显示 cc-switch 介绍

**数据结构**:
```typescript
interface CCSwitchState {
  claudeCodeInstalled: boolean;
  claudeCodeVersion?: string;
  isInstalling: boolean;
  ccSwitchInstalled: boolean;
  ccSwitchVersion?: string;
  isDownloading: boolean;
}
```

**安装流程**:
```
检测 Node.js 和 Git 是否已安装
    ↓
执行: npm install -g @anthropic-ai/claude-code
    ↓
检测安装结果: claude --version
    ↓
更新状态
```

**cc-switch 打开流程**:
```
检测本地是否已安装 cc-switch
    ↓
已安装 → 直接启动
    ↓
未安装 → 从 GitHub 下载最新版
    ↓
安装并启动
```

#### IDE 启动器

**功能**:
- 自动检测已安装 IDE
- 显示 IDE 信息（名称/版本/路径）
- 启动 IDE 并打开指定目录

**数据结构**:
```typescript
interface IdeInfo {
  name: 'vscode' | 'cursor' | 'trae';
  displayName: string;
  executablePath: string;
  version?: string;
}
```

#### 工作区管理

**功能**:
- 创建/删除工作区
- 设置默认 IDE
- 快速打开（启动 IDE）

**数据结构**:
```typescript
interface Workspace {
  id: string;
  name: string;
  path: string;
  defaultIde?: 'vscode' | 'cursor' | 'trae';
  lastOpened?: string;
  createdAt: string;
}
```

### 3.3 页面结构

```
Sidebar
├── Dashboard (环境状态概览)
├── CC Switch (Claude Code 安装)
├── IDE 启动器
├── 工作区
└── 设置

Main Content
├── DashboardView
│   ├── 欢迎区域
│   ├── 环境状态卡片
│   └── 快速操作
├── CCSwitchView
│   ├── Claude Code 安装状态
│   ├── 安装按钮
│   └── cc-switch 集成区域
├── IDELauncherView
│   └── IDE 列表
├── WorkspacesView
│   ├── 工作区列表
│   └── 创建模态框
└── SettingsView
    └── 应用设置
```

### 3.4 技术实现要点

#### 环境检测
```rust
// Rust 后端
#[tauri::command]
pub async fn detect_environment() -> Vec<ComponentStatus> {
    // 并行检测各个组件
    let checks = vec![
        check_node().await,
        check_git().await,
        check_python().await,
        check_uv().await,
    ];
    join_all(checks).await
}
```

#### Claude Code 安装
```rust
#[tauri::command]
pub async fn install_claude_code() -> Result<InstallResult, String> {
    // 1. 检查前置依赖
    // 2. 执行 npm install
    // 3. 验证安装
    // 4. 返回结果
}
```

#### cc-switch 下载
```rust
#[tauri::command]
pub async fn download_cc_switch() -> Result<(), String> {
    // 1. 获取最新版本信息
    // 2. 下载安装包
    // 3. 执行安装
    // 4. 启动应用
}
```

---

## 四、验收标准

### 功能验收

- [ ] **Dashboard**
  - [ ] 正确检测 Node.js / Git / Python / UV 安装状态
  - [ ] 显示组件版本号
  - [ ] 一键安装缺失组件
  - [ ] 实时显示安装进度

- [ ] **CC Switch 页面**
  - [ ] 正确检测 Claude Code 安装状态
  - [ ] 成功安装 Claude Code
  - [ ] 检测 cc-switch 是否已安装
  - [ ] 下载并启动 cc-switch

- [ ] **IDE 启动器**
  - [ ] 正确检测 VS Code / Cursor / Trae
  - [ ] 成功启动 IDE
  - [ ] 打开指定目录

- [ ] **工作区管理**
  - [ ] 创建工作区
  - [ ] 删除工作区
  - [ ] 设置默认 IDE
  - [ ] 打开工作区

### 性能验收

- [ ] 应用启动时间 < 2s
- [ ] 环境检测完成 < 5s
- [ ] 界面响应流畅，无卡顿

### 兼容性验收

- [ ] Windows 10/11
- [ ] macOS 12+
- [ ] Linux (Ubuntu 20.04+)

---

## 五、项目边界

### 我们的责任
- 基础环境安装（Node.js / Git / Python / UV）
- Claude Code 安装
- cc-switch 下载与启动
- IDE 启动
- 工作区管理

### cc-switch 的责任
- Provider 管理
- MCP 管理
- Skills 管理
- 用量统计
- 高级配置

### 分工界限
```
用户首次使用:
    我们的 App → 安装环境 → 安装 Claude Code → 启动 cc-switch

日常使用:
    cc-switch → 管理 Provider / MCP / Skills
    我们的 App → 快速启动工作区 / 环境维护
```

---

*PRD 版本: v1.0*
*创建日期: 2026-03-02*
