#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
案例报告 PDF 生成脚本
完整流程：截图 mockup → 合并 HTML → 导出 PDF
"""

import base64
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

def screenshot_mockup(mockup_html: Path, output_png: Path) -> None:
    """使用 Playwright 截图 mockup HTML"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1280, "height": 720},
            device_scale_factor=2  # 高清截图
        )
        page.goto(f"file:///{mockup_html}")
        page.screenshot(path=str(output_png), full_page=False)
        browser.close()

def image_to_base64(image_path: Path) -> str:
    """将图片转为 base64 data URI"""
    data = image_path.read_bytes()
    b64 = base64.b64encode(data).decode()
    ext = image_path.suffix.lower().replace(".", "")
    if ext == "jpg":
        ext = "jpeg"
    return f"data:image/{ext};base64,{b64}"

def merge_case_pages(
    case_files: list[Path],
    screenshot_map: dict[str, Path],
    output_html: Path
) -> None:
    """
    合并多个案例页为单个 HTML

    Args:
        case_files: 案例 HTML 文件列表（按顺序）
        screenshot_map: 占位符类名到截图文件的映射，如 {"placeholder-img": Path("mockup.png")}
        output_html: 输出合并后的 HTML 路径
    """
    # 读取第一个文件的 CSS 作为统一样式
    first_html = case_files[0].read_text(encoding="utf-8")
    css_match = re.search(r"<style>(.*?)</style>", first_html, re.DOTALL)
    unified_css = css_match.group(1) if css_match else ""

    # 收集所有案例内容
    pages_html = []
    for i, case_file in enumerate(case_files):
        content = case_file.read_text(encoding="utf-8")

        # 提取 body 内容
        body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.DOTALL)
        body_content = body_match.group(1).strip() if body_match else content

        # 替换占位图为 base64 截图
        for placeholder_class, screenshot_path in screenshot_map.items():
            if screenshot_path.exists():
                dataurl = image_to_base64(screenshot_path)
                body_content = re.sub(
                    rf'<div class="{placeholder_class}"[^>]*>.*?</div>',
                    f'<img src="{dataurl}" style="width:100%;display:block;margin-bottom:22px;border-radius:4px;">',
                    body_content,
                    flags=re.DOTALL
                )

        # 统一 section-title 为 h2
        body_content = re.sub(
            r'<div class="section-title">(.*?)</div>',
            r'<h2 class="section-title">\1</h2>',
            body_content
        )

        # 添加分页符（最后一页不需要）
        page_break = "page-break-after: always;" if i < len(case_files) - 1 else ""
        pages_html.append(f'<div style="{page_break}">\n{body_content}\n</div>')

    # 组装完整 HTML
    merged_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>案例合集</title>
<style>
{unified_css}
@page {{ size: A4; margin: 0; }}
@media print {{
  body {{ padding: 0 !important; margin: 0 !important; }}
}}
</style>
</head>
<body>
{chr(10).join(pages_html)}
</body>
</html>"""

    output_html.write_text(merged_html, encoding="utf-8")

def export_pdf(input_html: Path, output_pdf: Path) -> None:
    """使用 Playwright 导出 PDF"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file:///{input_html}")
        page.pdf(
            path=str(output_pdf),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )
        browser.close()

def main():
    """主流程示例"""
    workdir = Path(__file__).parent.parent  # 项目根目录
    os.chdir(workdir)

    print("=== 步骤1: 截图 mockup ===")
    for i in [1, 2]:
        mockup_html = workdir / f"mockup{i}.html"
        mockup_png = workdir / f"mockup{i}.png"
        if mockup_html.exists():
            screenshot_mockup(mockup_html, mockup_png)
            print(f"  已生成: mockup{i}.png")

    print("\n=== 步骤2: 合并案例页 ===")
    case_files = sorted(workdir.glob("案例单页*.html"))
    screenshot_map = {
        "placeholder-img": workdir / "mockup1.png",
        # 如果有多个不同的占位符，可以在这里映射
    }
    merged_html = workdir / "案例合集.html"
    merge_case_pages(case_files, screenshot_map, merged_html)
    print(f"  已生成: {merged_html.name}")

    print("\n=== 步骤3: 导出 PDF ===")
    output_pdf = workdir / "案例合集.pdf"

    # 检查文件是否被占用
    if output_pdf.exists():
        try:
            output_pdf.rename(output_pdf)  # 尝试重命名自己
        except PermissionError:
            print(f"  错误: {output_pdf.name} 被占用，请关闭 PDF 阅读器后重试")
            return

    export_pdf(merged_html, output_pdf)
    print(f"  已生成: {output_pdf.name}")
    print("\n=== 完成 ===")

if __name__ == "__main__":
    main()
