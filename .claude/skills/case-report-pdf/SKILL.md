---
name: case-report-pdf
description: 将 HTML 案例页转换为 PDF 报告，处理截图嵌入、多页合并、打印优化等技术流程。适用于企业案例报告、项目总结、解决方案文档的 PDF 生成。
---

## 触发场景

当用户需要以下功能时触发：
- "案例报告 PDF"
- "HTML 转 PDF"
- "合并案例页生成 PDF"
- "打印优化"
- "批量导出 PDF"

## 核心工作流

### 1. 检查输入文件

需要以下文件：
- `案例单页1.html`, `案例单页2.html` ... （单个案例 HTML 文件）
- `mockup1.html`, `mockup2.html` ... （产品界面截图源文件，可选）
- `logo.png` （企业 logo，建议先裁剪透明边距）

### 2. 统一 CSS 样式（关键！）

多案例合并时，必须确保所有单页 CSS 结构一致：

```css
/* 推荐结构 - 简单统一 */
body {
  max-width: 210mm;
  margin: 0 auto;
  padding: 15mm;          /* 统一页边距 */
  font-family: "Noto Sans SC", "Microsoft YaHei", sans-serif;
  font-size: 10.5pt;
  line-height: 1.75;
}

@page { size: A4; margin: 0; }  /* PDF 页面尺寸 */

@media print {
  body { padding: 0; }   /* 打印时去除 body padding */
}
```

**常见错误**：
- 案例1 用 `.page { padding: 12mm }`，案例2 用 `body { padding: 15mm }` → 合并后页间距不一致
- 解决方案：统一用一种方式，推荐直接写 `body { padding: 15mm }`

### 3. 图片预处理（重要！）

使用 `scripts/check_image.py` 检查并裁剪图片：

```bash
python check_image.py logo.png
# 输出生成 logo-cropped.png
```

**为什么需要**：很多 logo 图片有大量透明边距，直接嵌入会导致显示异常。

### 4. 截图 Mockup（如需要）

使用 Playwright 截图产品界面：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.goto("file:///path/to/mockup.html")
    page.screenshot(path="mockup.png", full_page=False)
    browser.close()
```

参数要点：
- `viewport`: 1280×720（16:9 比例）
- `device_scale_factor=2`：高清截图
- `full_page=False`：只截 viewport 区域

### 5. 合并 HTML

将多个案例页合并为单个 HTML 文件：

```html
<!DOCTYPE html>
<html>
<head>
  <!-- 统一 CSS -->
  <style>
    .page-break {
      page-break-after: always;
    }
    .page-break:last-child {
      page-break-after: auto;
    }
  </style>
</head>
<body>
  <!-- 案例1 -->
  <div class="page-break">
    ...案例1内容...
    <img src="data:image/png;base64,xxx">  <!-- base64 嵌入截图 -->
  </div>

  <!-- 案例2 -->
  <div class="page-break">
    ...案例2内容...
  </div>
</body>
</html>
```

**技术要点**：
- 图片转 base64 内嵌：`base64.b64encode(open(img, 'rb').read()).decode()`
- 使用 `data:image/png;base64,` 前缀
- 正则替换占位符：`<div class="placeholder">` → `<img>`

### 6. 导出 PDF

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("file:///path/to/merged.html")
    page.pdf(
        path="output.pdf",
        format="A4",
        print_background=True,  # 保留背景色
        margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
    )
    browser.close()
```

**注意**：导出前确保 PDF 文件未被占用（关闭 PDF 阅读器）。

## 完整脚本

使用 `scripts/build.py` 一键执行：

```bash
python build.py
```

脚本自动完成：截图 mockup → 合并 HTML → 导出 PDF。

## 常见陷阱

| 问题 | 原因 | 解决 |
|------|------|------|
| 页边距不一致 | CSS 结构不统一 | 统一 body padding，不用 .page 包裹 |
| Logo 显示异常 | 图片有透明边距 | 先用 check_image.py 裁剪 |
| PDF 导出失败 | 文件被占用 | 关闭 PDF 阅读器后重试 |
| 中文显示乱码 | 字体未加载 | 使用系统字体（微软雅黑），或确保网络可访问 Google Fonts |
| 图片不显示 | 路径错误或外部资源 | 用 base64 内嵌所有图片 |
| emoji 打印方框 | 字体不支持 | 避免使用 emoji，改用文字或 SVG |

## 环境要求

- Python 3.8+
- Playwright: `pip install playwright`
- Playwright 浏览器: `playwright install chromium`
- Pillow: `pip install pillow`（图片处理）
