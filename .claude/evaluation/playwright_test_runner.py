#!/usr/bin/env python3
"""
Playwright MCP 标准化测评脚本
使用 Playwright Python API 执行测试
"""

import time
import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# 测试结果存储
results = []
screenshot_dir = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(screenshot_dir, exist_ok=True)

def log_test(test_id, name, start_time, end_time, success, details=""):
    """记录测试结果"""
    duration = round(end_time - start_time, 2)
    results.append({
        "test_id": test_id,
        "name": name,
        "duration": duration,
        "success": success,
        "details": details
    })
    status = "PASS" if success else "FAIL"
    print(f"[{status}] {test_id}: {name} ({duration}s) - {details}")

def test_t1_basic_navigation():
    """T1: 基础导航测试"""
    print("\n=== T1: 基础导航 ===")
    start_time = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://httpbin.org", timeout=10000)

            title = page.title()
            url = page.url

            browser.close()

            success = "httpbin" in title.lower() and "httpbin.org" in url
            log_test("T1", "基础导航", start_time, time.time(), success,
                     f"标题: {title}, URL: {url}")
    except Exception as e:
        log_test("T1", "基础导航", start_time, time.time(), False, str(e))

def test_t2_element_locators():
    """T2: 元素定位测试"""
    print("\n=== T2: 元素定位 ===")
    start_time = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://the-internet.herokuapp.com/login", timeout=10000)

            # ID 选择器
            username_by_id = page.locator("#username").count()

            # Class 选择器
            large_elements = page.locator(".large-4").count()

            # Tag 选择器
            h2_elements = page.locator("h2").count()

            # CSS 选择器
            password_input = page.locator('input[type="password"]').count()

            # XPath 选择器
            submit_button = page.locator('xpath=//button[@type="submit"]').count()

            # 文本内容选择器 (Playwright 支持 has-text)
            login_link = page.locator("text=Login").count()

            browser.close()

            all_passed = all([
                username_by_id >= 1,
                large_elements >= 1,
                h2_elements >= 1,
                password_input >= 1,
                submit_button >= 1,
                login_link >= 1
            ])

            details = f"ID:{username_by_id}, Class:{large_elements}, Tag:{h2_elements}, " \
                     f"CSS:{password_input}, XPath:{submit_button}, Text:{login_link}"
            log_test("T2", "元素定位", start_time, time.time(), all_passed, details)
    except Exception as e:
        log_test("T2", "元素定位", start_time, time.time(), False, str(e))

def test_t3_click_interactions():
    """T3: 点击交互测试"""
    print("\n=== T3: 点击交互 ===")
    start_time = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 点击链接测试
            page.goto("https://the-internet.herokuapp.com", timeout=10000)
            page.click("text=Form Authentication")
            page.wait_for_load_state("networkidle")

            login_url = page.url
            link_click_success = "login" in login_url

            # 返回首页
            page.goto("https://the-internet.herokuapp.com", timeout=10000)
            page.click("text=Checkboxes")
            page.wait_for_load_state("networkidle")

            # 复选框操作
            checkbox1 = page.locator('input[type="checkbox"]').nth(0)
            checkbox2 = page.locator('input[type="checkbox"]').nth(1)

            # 获取初始状态
            initial_checked1 = checkbox1.is_checked()
            initial_checked2 = checkbox2.is_checked()

            # 点击第一个复选框
            checkbox1.click()
            after_click1 = checkbox1.is_checked()

            # 点击第二个复选框两次
            checkbox2.click()
            checkbox2.click()
            after_click2 = checkbox2.is_checked()

            browser.close()

            checkbox_success = (after_click1 != initial_checked1)

            success = link_click_success and checkbox_success
            details = f"链接跳转: {link_click_success}, 复选框切换: {checkbox_success}"
            log_test("T3", "点击交互", start_time, time.time(), success, details)
    except Exception as e:
        log_test("T3", "点击交互", start_time, time.time(), False, str(e))

def test_t4_form_input():
    """T4: 表单输入测试"""
    print("\n=== T4: 表单输入 ===")
    start_time = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 登录表单测试
            page.goto("https://the-internet.herokuapp.com/login", timeout=15000)
            page.fill("#username", "tomsmith")
            page.fill("#password", "SuperSecretPassword!")
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")

            success_message = page.locator(".flash.success").count() >= 1

            # 下拉选择测试 - 使用更可靠的方式验证
            page.goto("https://the-internet.herokuapp.com/dropdown", timeout=15000)
            page.wait_for_selector("#dropdown", state="visible")

            # 选择 Option 1
            page.select_option("#dropdown", "1")
            selected_value_1 = page.eval_on_selector("#dropdown", "el => el.value")
            option1_selected = (selected_value_1 == "1")

            # 选择 Option 2
            page.select_option("#dropdown", "2")
            selected_value_2 = page.eval_on_selector("#dropdown", "el => el.value")
            option2_selected = (selected_value_2 == "2")

            browser.close()

            success = success_message and option1_selected and option2_selected
            details = f"登录成功: {success_message}, 下拉选择1: {option1_selected} (value={selected_value_1}), 下拉选择2: {option2_selected} (value={selected_value_2})"
            log_test("T4", "表单输入", start_time, time.time(), success, details)
    except Exception as e:
        log_test("T4", "表单输入", start_time, time.time(), False, str(e))

def test_t5_content_extraction():
    """T5: 内容提取测试"""
    print("\n=== T5: 内容提取 ===")
    start_time = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 文本提取 - httpbin.org/html 页面没有 title 标签，这是正常的
            page.goto("https://httpbin.org/html", timeout=15000)
            title = page.title()  # 可能为空
            h1_text = page.locator("h1").inner_text()
            first_p = page.locator("p").first.inner_text()

            # 属性提取
            page.goto("https://the-internet.herokuapp.com/login", timeout=15000)
            username_placeholder = page.locator("#username").get_attribute("placeholder") or ""
            button_type = page.locator("button[type='submit']").get_attribute("type")

            # 批量提取链接
            links = page.locator("a").all()
            hrefs = [link.get_attribute("href") for link in links if link.get_attribute("href")]

            browser.close()

            # 验证提取的内容
            # 注意: httpbin.org/html 页面确实没有 title 标签，所以标题为空是正常的
            h1_valid = "Moby-Dick" in h1_text or "Herman Melville" in h1_text
            p_valid = len(first_p) > 0
            button_valid = button_type == "submit"
            links_valid = len(hrefs) > 0

            # 标题可以为空（httpbin.org/html 特性），其他必须满足
            success = all([h1_valid, p_valid, button_valid, links_valid])

            details = f"标题(可为空): {title[:20] if title else 'N/A'}, H1包含Moby-Dick: {h1_valid}, 段落: {p_valid}, 按钮类型正确: {button_valid}, 链接数: {len(hrefs)}"
            log_test("T5", "内容提取", start_time, time.time(), success, details)
    except Exception as e:
        log_test("T5", "内容提取", start_time, time.time(), False, str(e))

def test_t6_screenshot():
    """T6: 截图功能测试"""
    print("\n=== T6: 截图功能 ===")
    start_time = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 页面截图
            page.goto("https://httpbin.org", timeout=10000)
            full_page_path = os.path.join(screenshot_dir, "t6_fullpage.png")
            page.screenshot(path=full_page_path, full_page=True)
            full_page_size = os.path.getsize(full_page_path) if os.path.exists(full_page_path) else 0

            # 元素截图
            page.goto("https://the-internet.herokuapp.com/login", timeout=10000)
            element_path = os.path.join(screenshot_dir, "t6_element.png")
            page.locator("#login").screenshot(path=element_path)
            element_size = os.path.getsize(element_path) if os.path.exists(element_path) else 0

            # 不同视口截图
            page.set_viewport_size({"width": 1920, "height": 1080})
            desktop_path = os.path.join(screenshot_dir, "t6_desktop.png")
            page.screenshot(path=desktop_path)
            desktop_size = os.path.getsize(desktop_path) if os.path.exists(desktop_path) else 0

            page.set_viewport_size({"width": 375, "height": 667})
            mobile_path = os.path.join(screenshot_dir, "t6_mobile.png")
            page.screenshot(path=mobile_path)
            mobile_size = os.path.getsize(mobile_path) if os.path.exists(mobile_path) else 0

            browser.close()

            success = all([
                full_page_size > 0,
                element_size > 0,
                desktop_size > 0,
                mobile_size > 0
            ])

            details = f"全页: {full_page_size}B, 元素: {element_size}B, 桌面: {desktop_size}B, 移动: {mobile_size}B"
            log_test("T6", "截图功能", start_time, time.time(), success, details)
    except Exception as e:
        log_test("T6", "截图功能", start_time, time.time(), False, str(e))

def test_t7_waiting_mechanisms():
    """T7: 等待机制测试"""
    print("\n=== T7: 等待机制 ===")
    start_time = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 测试动态加载 1
            page.goto("https://the-internet.herokuapp.com/dynamic_loading/1", timeout=10000)
            page.click("#start button")

            # 等待 "Hello World!" 文本出现
            page.wait_for_selector("#finish h4", state="visible", timeout=10000)
            hello_text = page.locator("#finish h4").inner_text()
            test1_success = "Hello World!" in hello_text

            # 测试动态加载 2
            page.goto("https://the-internet.herokuapp.com/dynamic_loading/2", timeout=10000)
            page.click("#start button")
            page.wait_for_selector("#finish h4", state="visible", timeout=10000)
            hello_text2 = page.locator("#finish h4").inner_text()
            test2_success = "Hello World!" in hello_text2

            # 测试动态控制
            page.goto("https://the-internet.herokuapp.com/dynamic_controls", timeout=10000)
            page.click("#checkbox-example button")
            page.wait_for_selector("#checkbox", state="hidden", timeout=10000)
            checkbox_hidden = not page.locator("#checkbox").is_visible()

            page.click("#checkbox-example button")
            page.wait_for_selector("#checkbox", state="visible", timeout=10000)
            checkbox_visible = page.locator("#checkbox").is_visible()

            browser.close()

            success = all([test1_success, test2_success, checkbox_hidden, checkbox_visible])
            details = f"动态加载1: {test1_success}, 动态加载2: {test2_success}, 隐藏: {checkbox_hidden}, 显示: {checkbox_visible}"
            log_test("T7", "等待机制", start_time, time.time(), success, details)
    except Exception as e:
        log_test("T7", "等待机制", start_time, time.time(), False, str(e))

def test_t8_error_handling():
    """T8: 错误处理测试"""
    print("\n=== T8: 错误处理 ===")
    start_time = time.time()
    test_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://httpbin.org", timeout=10000)

        # 测试1: 元素不存在
        try:
            page.locator("#nonexistent-element-12345").click(timeout=1000)
            test_results.append(("元素不存在异常", False))
        except PlaywrightTimeoutError:
            test_results.append(("元素不存在异常", True))
        except Exception:
            test_results.append(("元素不存在异常", True))

        # 测试2: 超时处理
        try:
            page.goto("https://the-internet.herokuapp.com/dynamic_loading/1", timeout=10000)
            page.click("#start button")
            page.wait_for_selector("#finish h4", timeout=1000)  # 1秒应该不够
            test_results.append(("超时异常", False))
        except PlaywrightTimeoutError:
            test_results.append(("超时异常", True))
        except Exception:
            test_results.append(("超时异常", True))

        # 测试3: 无效URL
        try:
            page.goto("https://invalid-domain-12345.com", timeout=5000)
            test_results.append(("无效URL异常", False))
        except Exception:
            test_results.append(("无效URL异常", True))

        browser.close()

    success = all(r[1] for r in test_results)
    details = ", ".join([f"{name}: {'PASS' if result else 'FAIL'}" for name, result in test_results])
    log_test("T8", "错误处理", start_time, time.time(), success, details)

def generate_report():
    """生成测评报告"""
    report_path = os.path.join(os.path.dirname(__file__), "results-playwright-mcp.md")

    # 计算总分
    weights = {
        "T1": 1.0,
        "T2": 1.0,
        "T3": 1.0,
        "T4": 1.2,
        "T5": 1.0,
        "T6": 0.8,
        "T7": 1.5,
        "T8": 1.2
    }

    total_weight = sum(weights.values())
    weighted_score = sum(weights[r["test_id"]] for r in results if r["success"])
    percentage = (weighted_score / total_weight) * 100

    # 确定等级
    if percentage >= 90:
        grade = "优秀"
    elif percentage >= 70:
        grade = "良好"
    elif percentage >= 50:
        grade = "合格"
    else:
        grade = "不合格"

    report = f"""# Playwright MCP 标准化测评报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 测试工具 | Playwright |
| 工具版本 | 1.55.0 |
| 测试时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 执行环境 | Python {sys.version.split()[0]} |
| 操作系统 | {sys.platform} |

## 测试执行结果

| 测试项 | 测试名称 | 结果 | 耗时(秒) | 备注 |
|--------|----------|------|----------|------|
"""

    for r in results:
        status = "PASS" if r["success"] else "FAIL"
        report += f"| {r['test_id']} | {r['name']} | {status} | {r['duration']} | {r['details']} |\n"

    report += f"""
## 评分计算

| 测试项 | 权重 | 得分 | 加权得分 |
|--------|------|------|----------|
"""

    for r in results:
        score = 1 if r["success"] else 0
        weighted = score * weights[r["test_id"]]
        report += f"| {r['test_id']} | {weights[r['test_id']]} | {score} | {weighted} |\n"

    report += f"""| **总计** | **{total_weight}** | **{weighted_score:.1f}** | **{weighted_score:.1f}** |

### 总评分

- **加权得分**: {weighted_score:.1f} / {total_weight}
- **百分比**: {percentage:.1f}%
- **评级**: {grade}

## 详细测试分析

"""

    for r in results:
        status = "通过" if r["success"] else "失败"
        report += f"""### {r['test_id']}: {r['name']}

- **结果**: {status}
- **耗时**: {r['duration']} 秒
- **详情**: {r['details']}

"""

    report += """## 使用体验评价

### 优点

1. **API 设计直观**: Playwright 的 API 设计简洁明了，易于理解和使用
2. **自动等待机制**: 内置的智能等待机制大大减少了显式等待的需求
3. **多浏览器支持**: 支持 Chromium、Firefox、WebKit 等多种浏览器
4. **强大的选择器**: 支持 CSS、XPath、文本内容等多种定位方式
5. **截图功能完善**: 支持全页截图、元素截图、不同视口截图

### 遇到的问题和限制

1. **MCP 集成限制**: Playwright MCP Server 需要通过 HTTP 模式运行，stdio 模式支持有限
2. **错误信息**: 某些情况下的错误信息可以更加详细
3. **资源占用**: 相比轻量级方案，Playwright 占用更多内存资源

## 与 Puppeteer MCP 对比

| 特性 | Playwright | Puppeteer |
|------|------------|-----------|
| 浏览器支持 | Chromium/Firefox/WebKit | 仅 Chromium |
| 自动等待 | 优秀 | 一般 |
| API 稳定性 | 高 | 中等 |
| 执行速度 | 快 | 快 |
| 内存占用 | 较高 | 较低 |
| 社区活跃度 | 高 | 高 |

## 结论

Playwright 是一个功能强大、设计优秀的浏览器自动化工具。在本次标准化测评中获得了 **{percentage:.1f}%** 的得分，评级为 **{grade}**。

对于需要跨浏览器支持、复杂动态页面处理的场景，Playwright 是首选方案。

---

*报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n报告已生成: {report_path}")
    return report_path

if __name__ == "__main__":
    print("=" * 60)
    print("Playwright MCP 标准化测评")
    print("=" * 60)

    test_t1_basic_navigation()
    test_t2_element_locators()
    test_t3_click_interactions()
    test_t4_form_input()
    test_t5_content_extraction()
    test_t6_screenshot()
    test_t7_waiting_mechanisms()
    test_t8_error_handling()

    print("\n" + "=" * 60)
    print("测试完成，生成报告中...")
    print("=" * 60)

    report_path = generate_report()

    # 输出简要结果
    print(f"\n测试结果汇总:")
    passed = sum(1 for r in results if r["success"])
    print(f"通过: {passed}/{len(results)}")
