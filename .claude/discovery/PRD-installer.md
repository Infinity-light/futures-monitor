# PRD: Claude Code 环境安装程序 - 跨平台打包

## 需求概述

将现有的 Python 安装程序项目打包为三端独立可执行文件，用户无需安装 Python 即可运行。

## 用户动线

### Windows 动线
1. **开发者运行打包** → 执行 `python build.py --platform windows`
2. **生成产物** → `dist/ClaudeEnvInstaller-Windows.exe`
3. **终端用户使用** → 双击 exe，按安装向导完成安装
4. **完成标准** → 桌面出现快捷方式，开始菜单可找到程序

### macOS 动线
1. **开发者运行打包** → 执行 `python build.py --platform macos`
2. **生成产物** → `dist/ClaudeEnvInstaller-macOS.dmg`
3. **终端用户使用** → 双击 dmg，拖拽应用到 Applications 文件夹
4. **完成标准** → Launchpad 可见，双击运行

### Linux 动线
1. **开发者运行打包** → 执行 `python build.py --platform linux`
2. **生成产物** → `dist/ClaudeEnvInstaller-Linux.AppImage`
3. **终端用户使用** → 下载后 `chmod +x` 赋予权限，双击运行
4. **完成标准** → 无需安装依赖，双击直接启动

## 技术决策

| 平台 | 打包工具 | 安装包格式 | 理由 |
|------|---------|-----------|------|
| Windows | PyInstaller + Inno Setup | .exe 安装向导 | 最熟悉的 Windows 安装体验，支持卸载 |
| macOS | PyInstaller + create-dmg | .dmg 拖拽安装 | 符合 macOS 用户习惯，简洁优雅 |
| Linux | PyInstaller + AppImageKit | AppImage | 真正的绿色软件，跨发行版兼容 |

## 文件结构

```
claude-env-installer/
├── build.py              # 统一构建入口
├── build/
│   ├── windows/
│   │   ├── installer.iss    # Inno Setup 脚本
│   │   └── build_windows.py # Windows 打包脚本
│   ├── macos/
│   │   ├── build_macos.py   # macOS 打包脚本
│   │   └── resources/       # dmg 背景图等
│   └── linux/
│       ├── build_linux.py   # Linux 打包脚本
│       └── AppRun           # AppImage 入口
├── dist/                 # 输出目录
│   ├── ClaudeEnvInstaller-Windows.exe
│   ├── ClaudeEnvInstaller-macOS.dmg
│   └── ClaudeEnvInstaller-Linux.AppImage
└── src/                  # 原有源代码
```

## 验收标准

- [ ] `python build.py --all` 可构建三端安装包
- [ ] Windows 安装包在干净 Win10/Win11 环境可安装运行
- [ ] macOS dmg 在干净 macOS 环境可拖拽安装运行
- [ ] Linux AppImage 在 Ubuntu 22.04/24.04 可双击运行
- [ ] 所有安装包包含完整的安装程序功能（检查/下载/安装/配置）

## 排除项

- 不考虑代码签名（用户可自行购买证书签名）
- 不考虑自动更新机制
- 不考虑 32 位系统支持
