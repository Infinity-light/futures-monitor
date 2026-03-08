---
name: poster-creator
description: 活动海报制作工具。支持两种模式：1) AI全图生成（单页海报）；2) AI底图+前端叠加（多页/复杂信息）。适用于会议、讲座、训练营等活动宣传。
---

# Poster Creator - 海报制作

## 两种工作模式

根据需求选择模式：

| 模式 | 适用场景 | 输出 |
|------|---------|------|
| **A-全图生成** | 单页、信息简单、快速出图 | PNG |
| **B-底图+叠加** | 多页、信息复杂、需可编辑 | PNG + HTML |

默认优先尝试 **模式A**，信息复杂时转 **模式B**。

---

## 模式A：AI全图生成

### 适用条件
- 单页海报
- 信息层级清晰（标题+时间地点+主办方）
- 不常修改

### Prompt模板

**第一页（主视觉页）**：
```
高端[科技/商务]活动海报，[深蓝/深灰]渐变背景。

顶部：[主标题，如"AI应用超级个体训练营"]，
[副标题，如"探索行业真应用"]。

中心：[主视觉描述，如发光红色龙虾logo悬浮在神经网络背景中]。

底部区域：[时间地点信息，清晰可读的大字号]。

右下角：[二维码区域，白色背景方块]。

底部：[主办方单位名称]。

电影级质感，竖版1440x2560，高对比度，文字清晰无断裂
```

**关键**：明确指定"文字清晰可读"，避免AI生成模糊文字。

### 质量检查清单
- [ ] 大字清晰无断裂
- [ ] 时间地点信息正确
- [ ] 无错别字
- [ ] 配色协调（深色底+亮色字）
- [ ] 二维码区域有对比色（如白色背景）

---

## 模式B：AI底图 + 前端叠加

### 适用条件
- 多页海报（2页+）
- 信息复杂（日程+学员+项目）
- 需要后期微调

### 底图生成原则

**DO（必须）**：
- 明确留白区域："下方XX%区域自然过渡，不生成任何文字"
- 只说结构和氛围："发光时间线"、"深色渐变"
- 固定元素才放底图：标题、主视觉logo

**DON'T（禁止）**：
- 不要生成具体时间/人名（会变假字）
- 不要生成框线（前端会错位）
- 不要浅色背景（文字看不清）
- 不要白色区域（除非文字是深色）

### 底图Prompt示例

```
高端科技会议海报第二页。
顶部白色大字"日程安排"。
下方整体深蓝到黑色渐变背景，中心区域纯净无元素。
周围边缘少量星空光点装饰。
底部右侧角落有小红色龙虾剪影。
无框线、无占位符、无文字。
竖版1440x2560
```

### 前端叠加规范

**定位策略**：
```css
.content {
    position: absolute;
    top: 400px;      /* 避开标题 */
    left: 100px;
    right: 100px;
    bottom: 150px;   /* 避开装饰 */
}
```

**字体层级**：
| 用途 | 字号 | 颜色 |
|------|------|------|
| 时间 | 44px | #00d4ff |
| 标题 | 36px | #fff |
| 正文 | 28px | rgba(255,255,255,0.9) |
| 辅助 | 24px | rgba(255,255,255,0.6) |

**布局原则**：
- 时间地点左对齐，二维码右置
- 左右两栏用 flex，间距 60-80px
- 纯文字排版，不用卡片背景（除非底图太花）

**完整 HTML 模板（第二页）**：
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Noto Sans SC', sans-serif; background: #000; }
        .poster {
            width: 1440px; height: 2560px;
            position: relative; overflow: hidden;
        }
        .poster-bg {
            position: absolute; top: 0; left: 0;
            width: 100%; height: 100%; object-fit: cover;
        }
        .content {
            position: absolute;
            top: 480px;      /* 避开标题 */
            left: 100px; right: 100px; bottom: 180px;
        }
        /* 日程 */
        .schedule { margin-bottom: 80px; }
        .schedule-item { margin-bottom: 50px; }
        .time {
            font-size: 44px; font-weight: 700;
            color: #00d4ff; letter-spacing: 4px;
            margin-bottom: 12px;
        }
        .event {
            font-size: 32px; color: rgba(255,255,255,0.95);
            letter-spacing: 2px;
        }
        /* 分隔线 */
        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(0,212,255,0.4), transparent);
            margin: 60px 0;
        }
        /* 左右两栏 */
        .columns { display: flex; gap: 80px; }
        .column { flex: 1; }
        .col-title {
            font-size: 36px; font-weight: 700;
            color: #fff; letter-spacing: 6px;
            margin-bottom: 40px;
        }
        .entry { margin-bottom: 28px; }
        .entry-label {
            font-size: 28px; font-weight: 700;
            color: #00ff88; letter-spacing: 2px;
        }
        .entry-desc {
            font-size: 24px;
            color: rgba(255,255,255,0.85); margin-top: 6px;
        }
    </style>
</head>
<body>
<div class="poster">
    <img class="poster-bg" src="底图_第二页.png" alt="底图">
    <div class="content">
        <!-- 日程 -->
        <div class="schedule">
            <div class="schedule-item">
                <div class="time">09:00 — 10:00</div>
                <div class="event">营员报到 · 启动仪式</div>
            </div>
        </div>
        <div class="divider"></div>
        <!-- 两栏 -->
        <div class="columns">
            <div class="column">
                <div class="col-title">往期学员</div>
                <div class="entry">
                    <div class="entry-label">中科院</div>
                    <div class="entry-desc">材料科学博士后</div>
                </div>
            </div>
            <div class="column">
                <div class="col-title">往期项目</div>
                <div class="entry">
                    <div class="entry-label">量化交易</div>
                    <div class="entry-desc">智能风控系统</div>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
```

---

## 关键决策点

### 何时用模式A vs 模式B？

```
单页 + 信息简单（标题/时间/地点/主办方）
└── 模式A：AI全图生成 ✓

单页 + 信息复杂（日程表+多栏内容）
└── 模式A：AI全图（AI直接生成完整内容，不叠加）

多页 + 需后期修改
└── 模式B：底图+前端叠加 ✓

不确定时
└── 先试模式A，效果不佳转模式B
```

### 底图 vs HTML 的职责边界

| 元素 | 归属 | 原因 |
|------|------|------|
| 主标题 | 底图 | AI字体设计更好 |
| 时间地点 | 均可 | 简单用AI，复杂用HTML |
| 日程表 | HTML | 避免AI生成假字 |
| 两栏列表 | HTML | 对齐可控 |
| 二维码 | Python合成 | 避免AI变形 |
| 装饰图案 | 底图 | 氛围感 |
| Logo | 底图 | 品牌识别 |

---

## 多页海报设计

### 页间衔接
- 统一配色（深蓝+青绿+红龙虾）
- 统一字体层级
- 每页底部/顶部有视觉呼应（如龙虾位置变化）

### 常见页面结构

**第一页（主视觉）**：
- 大标题 + 副标题
- 中心主视觉（龙虾/logo）
- 标语
- 时间地点 + 二维码
- 主办方

**第二页（详情）**：
- 标题"日程安排"
- 时间线 + 内容
- 分隔线
- 左右两栏（学员/项目/亮点）

**第三页（合作）**：
- Logo墙 或 纯文字列表
- 分类：主办/支持/社区

---

## 实战经验

### 二维码最佳实践
- 白色背景 + 12px内边距 + 圆角
- 位置：右下或右侧中间
- 下方标注"扫码报名"（蓝色 #00d4ff，非绿色）
- 尺寸：200-240px
- 使用 Python PIL 合成（避免AI生成变形）：

```python
from PIL import Image

poster = Image.open('底图.png')
qr = Image.open('二维码.png')
qr = qr.resize((240, 240), Image.Resampling.LANCZOS)

# 计算位置：右下角，边距 80px
x = poster.width - 240 - 80
y = poster.height - 240 - 80

poster.paste(qr, (x, y))
poster.save('海报_最终.png')
```

### 常见失败案例

| 问题 | 原因 | 解决 |
|------|------|------|
| 底图有假字/乱码 | AI生成了细节文字 | 强调"不生成任何文字" |
| 白色区域太大 | 提示词没说深色 | 指定"深蓝到黑色渐变" |
| 框线对不齐 | 底图有固定结构 | 底图只给氛围，结构用CSS |
| 文字看不清 | 背景太浅/太花 | 深色底+白色字 |
| 第二页像白板 | 留白太大无装饰 | 加星空/光点/角落logo |
| 二维码与时间重叠 | 空间规划不当 | 时间左对齐，二维码右置，padding-right预留 |
| 扫码文字用绿色 | 与蓝色主题不搭 | 用青色 #00d4ff，禁用绿色 |
| 头像与主题不符 | 强行加人像 | 去掉头像，用主题元素替代 |

### 配色方案

```yaml
科技:
  背景: "深蓝 #0a1628 到黑色"
  强调: "#00d4ff" (青)
  点缀: "#00ff88" (绿)
  品牌: "红色龙虾"

商务:
  背景: "深灰到黑色"
  强调: "#ffd700" (金)
  点缀: "#fff" (白)
```

---

## 输出规范

**模式A输出**：
- `海报_主题.png`

**模式B输出**：
- `底图_[页码].png`（AI生成）
- `海报_[页码].html`（前端叠加）
- 截图导出最终 PNG

---

## 完整工作示例

### 案例：AI训练营两页海报

**需求**：3月7日活动，主题"探索行业真应用"，OpenClaw龙虾logo

**执行流程**：

**第一页（主视觉）- 模式A**：
1. 生成Prompt：
   ```
   高端科技活动海报，深蓝渐变背景。
   顶部："AI应用超级个体训练营"，"探索行业真应用"。
   中心：发光红色龙虾logo悬浮在神经网络中。
   底部：时间地点，右下角白色二维码区域。
   电影级质感，竖版1440x2560
   ```
2. AI生成底图
3. Python合成二维码（见上方代码）
4. 交付：`海报_第一页.png`

**第二页（详情）- 模式B**：
1. 底图Prompt：
   ```
   高端科技会议海报第二页。
   顶部白色大字"日程安排"。
   下方整体深蓝到黑色渐变，中心区域纯净。
   周围边缘少量星空光点。
   底部右侧有小红色龙虾剪影。
   无框线、无占位符、无文字。
   竖版1440x2560
   ```
2. 生成底图
3. HTML叠加日程和两栏内容（用上方模板）
4. 浏览器截图导出
5. 交付：`海报_第二页.png`

---

## 快速检查清单

生成后逐项确认：
- [ ] 文字清晰可读，无断裂模糊
- [ ] 时间地点信息正确无误
- [ ] 无错别字、无假字乱码
- [ ] 二维码区域白色背景，清晰可见
- [ ] 扫码报名文字为蓝色（#00d4ff）
- [ ] 配色协调，深色底+亮色字
- [ ] 多页间风格统一（配色/字体/装饰）
