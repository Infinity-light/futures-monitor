---
name: conversation-to-article
description: 当用户说：“为我（根据上文）写一篇……文章”的时候加载。Transforms conversation context into publishable articles for WeChat Official Account and Xiaohongshu. Generates multiple style variants (tutorial, story, opinion, review, guide) with moderate personalization and depth. Use when user mentions "生成文章", "写文章", "/article", or wants to convert discussion into social media content.
---

# Conversation to Article Generator

将对话上下文转化为可发布的自媒体文章，支持微信公众号和小红书双平台，提供多种风格变体。

## Language

**Match user's language**: 根据用户使用的语言响应。中文对话生成中文文章，英文对话生成英文文章。

## Usage

```bash
# 基础用法 - 分析当前对话并生成文章
/article

# 指定风格
/article --style tutorial

# 指定平台
/article --platform wechat

# 组合使用
/article --style story --platform xiaohongshu
```

## Options

| Option | Description |
|--------|-------------|
| `--style <name>` | 文章风格 (见 Style Gallery) |
| `--platform <name>` | 目标平台: wechat / xiaohongshu / both (默认) |

## Style Gallery

| Style | 中文名 | Description |
|-------|--------|-------------|
| `tutorial` | 教程型 | 步骤清晰、实操性强，适合技术分享、工具使用 |
| `story` | 故事型 | 叙事完整、情感真实，适合经验分享、案例分析 |
| `opinion` | 观点型 | 论点鲜明、论据充分，适合行业洞察、热点评论 |
| `review` | 种草型 | 真实体验、优缺点并存，适合产品测评、工具推荐 |
| `guide` | 攻略型 | 信息密集、实用价值高，适合避坑指南、资源汇总 |

## Writing Principles

### Core: 中度拟人 + 深度内容

| 要素 | 采用 | 避免 |
|------|------|------|
| **人称** | 适度使用"我"、"我们" | 全篇"我我我" |
| **语气** | 自然口语化，像朋友聊天 | 过度热情、感叹号泛滥 |
| **表情** | 极少量或不用emoji | emoji堆砌 |
| **深度** | 有观点、有论据、有思考 | 浅尝辄止、流水账 |
| **结构** | 逻辑清晰、层层递进 | 碎片化、跳跃 |

### Platform Differences

| 维度 | 微信公众号 | 小红书 |
|------|-----------|--------|
| **标题** | 正式 + 悬念 + 完整句 | 口语化 + 短句 |
| **开头** | 引言铺垫 | 直接痛点/好处 |
| **正文** | 小标题分段、论述完整 | 短段落、列表 |
| **结尾** | 总结升华 + 关注引导 | 互动提问 |
| **字数** | 1500-3000字 | 300-800字 |

## File Structure

每次生成创建独立目录：

```
generated-articles/{date}_{topic-slug}/
├── analysis.md                    # 对话分析结果
├── wechat/
│   ├── tutorial.md               # Markdown源文件
│   ├── tutorial.html             # 转换后的HTML（可选）
│   ├── story.md
│   ├── opinion.md
│   ├── review.md
│   └── guide.md
└── xiaohongshu/
    ├── tutorial.txt              # 纯文本格式（可直接复制）
    ├── tutorial-images/          # 图片版（可选）
    ├── story.txt
    ├── opinion.txt
    ├── review.txt
    └── guide.txt
```

## Workflow

### Progress Checklist

```
Article Generation Progress:
- [ ] Step 1: Analyze conversation context
- [ ] Step 2: Confirmation - Topic & style selection
- [ ] Step 3: Generate articles
- [ ] Step 4: Render for publishing
- [ ] Step 5: Completion report
```

### Step 1: Analyze Conversation Context

分析当前对话，提取以下信息：

**Actions**:
1. 识别对话主题和核心内容
2. 提取关键信息点、结论、观点
3. 判断内容类型（技术讨论、问题解决、创意探索、知识学习等）
4. 评估各风格的适配度
5. 保存分析结果到 `analysis.md`

**Analysis Framework**: See `references/config/analysis-framework.md`

### Step 2: Confirmation - Topic & Style Selection

**Purpose**: 确认主题理解 + 选择生成风格。**Do NOT skip.**

**Display summary**:
- 识别的主题
- 提取的关键点
- 推荐的风格（基于内容类型）

**Use AskUserQuestion** for:
1. 确认主题理解是否正确
2. 选择要生成的风格（多选）
3. 选择目标平台

### Step 3: Generate Articles

根据选择的风格和平台生成文章。

**For each selected style**:
1. 加载对应风格模板 (`references/styles/{style}.md`)
2. 加载平台规范 (`references/platforms/{platform}.md`)
3. 基于对话内容生成文章
4. 保存到对应目录

**Generation Order**:
- 先生成微信公众号版本（Markdown格式，后续转HTML）
- 再基于长文精简为小红书版本（**直接生成纯文本格式，无Markdown符号**）

**小红书纯文本格式规范**:
- 不使用 `#` `*` `**` 等Markdown符号
- 用空行分隔段落
- 用"一、二、三"或"1. 2. 3."表示列表
- 用「」或【】强调关键词
- 结尾直接写标签，如：#话题 #标签

### Step 4: Render for Publishing

将生成的内容转换为可直接发布的格式。

**微信公众号 → HTML**

调用 `baoyu-markdown-to-html` Skill：

```
/baoyu-markdown-to-html wechat/{style}.md --theme default
```

输出：`wechat/{style}.html`（可直接粘贴到公众号编辑器）

**小红书 → 图片版（可选）**

如果用户需要图片版，调用 `baoyu-xhs-images` Skill：

```
/baoyu-xhs-images xiaohongshu/{style}.txt
```

输出：`xiaohongshu/{style}-images/` 目录下的系列图片

**Use AskUserQuestion** 询问用户：
1. 是否需要转换公众号文章为HTML
2. 小红书是否需要生成图片版

### Step 5: Completion Report

```
Article Generation Complete!

Topic: [topic]
Date: [YYYY-MM-DD]
Location: generated-articles/{date}_{slug}/

Generated Files:
✓ analysis.md

WeChat Official Account:
[✓/✗] tutorial.md - 教程型
[✓/✗] story.md - 故事型
[✓/✗] opinion.md - 观点型
[✓/✗] review.md - 种草型
[✓/✗] guide.md - 攻略型

Xiaohongshu:
[✓/✗] tutorial.md - 教程型
[✓/✗] story.md - 故事型
[✓/✗] opinion.md - 观点型
[✓/✗] review.md - 种草型
[✓/✗] guide.md - 攻略型

Next Steps:
→ Review and edit the generated articles
→ Copy to your publishing platform
```

## References

Detailed templates in `references/` directory:

**Styles** (风格模板):
- `styles/tutorial.md` - 教程型写作指南
- `styles/story.md` - 故事型写作指南
- `styles/opinion.md` - 观点型写作指南
- `styles/review.md` - 种草型写作指南
- `styles/guide.md` - 攻略型写作指南

**Platforms** (平台规范):
- `platforms/wechat.md` - 微信公众号规范
- `platforms/xiaohongshu.md` - 小红书规范

**Config** (配置):
- `config/analysis-framework.md` - 对话分析框架

## Dependencies

本Skill依赖以下外部Skill进行渲染：

| Skill | 用途 | 必需 |
|-------|------|------|
| `baoyu-markdown-to-html` | 将公众号Markdown转为HTML | 可选 |
| `baoyu-xhs-images` | 将小红书内容生成图片版 | 可选 |

**安装方式**：
```bash
# 如果参考文件目录已有baoyu-skills，可直接使用
# 否则可通过以下方式安装
npx skills add JimLiu/baoyu-skills
```

**注意**：小红书纯文本版不需要额外Skill，本Skill直接生成可复制的纯文本格式。
