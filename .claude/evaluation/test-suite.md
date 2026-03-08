# 浏览器自动化工具标准化测评集

## 概述

本测评集旨在为浏览器自动化工具（如 Puppeteer、Selenium、Playwright 等）提供一套标准化的能力评估框架。

---

## 测试目标网站

| 难度 | 网站 | URL | 特点 |
|------|------|-----|------|
| 简单 | httpbin.org | https://httpbin.org | 简单的HTTP测试服务，响应可预测，适合基础功能测试 |
| 中等 | The Internet Herokuapp | https://the-internet.herokuapp.com | 专门用于自动化测试的练习网站，包含表单、动态内容等 |
| 复杂 | Dynamic Loading Demo | https://the-internet.herokuapp.com/dynamic_loading | 包含异步加载、延迟渲染等复杂场景 |

---

## 测试项详情

### T1: 基础导航 (Basic Navigation)

**权重**: 1.0 (基础必备)

**测试步骤**:
1. 启动浏览器实例
2. 导航至 https://httpbin.org
3. 等待页面加载完成
4. 获取页面标题
5. 获取当前 URL
6. 关闭浏览器

**预期结果**:
- 页面成功加载，无超时错误
- 页面标题包含 "httpbin"
- 当前 URL 与目标 URL 一致

**成功标准**:
- [PASS] 页面在 10 秒内完成加载
- [PASS] 标题正确获取且不为空
- [PASS] URL 匹配，无重定向异常
- [FAIL] 页面加载超时 (>10秒)
- [FAIL] 标题获取失败或为空
- [FAIL] URL 不匹配

---

### T2: 元素定位 (Element Locators)

**权重**: 1.0 (基础必备)

**测试步骤**:
1. 导航至 https://the-internet.herokuapp.com/login
2. 使用以下选择器定位元素：
   - ID 选择器: `#username`
   - Class 选择器: `.large-4`
   - Tag 选择器: `h2`
   - CSS 选择器: `input[type="password"]`
   - XPath: `//button[@type="submit"]`
   - 文本内容: 包含 "Login" 的链接
3. 验证每个元素是否成功定位

**预期结果**:
- 所有选择器类型均能成功定位到对应元素
- 定位的元素数量与预期一致

**成功标准**:
- [PASS] ID 选择器成功定位元素
- [PASS] Class 选择器成功定位元素
- [PASS] Tag 选择器成功定位元素
- [PASS] CSS 选择器成功定位元素
- [PASS] XPath 选择器成功定位元素
- [PASS] 文本匹配选择器成功定位元素
- [FAIL] 任一选择器定位失败
- [FAIL] 定位到错误元素

---

### T3: 点击交互 (Click Interactions)

**权重**: 1.0 (基础必备)

**测试步骤**:
1. 导航至 https://the-internet.herokuapp.com
2. 点击 "Form Authentication" 链接
3. 验证页面跳转至登录页
4. 返回首页
5. 点击 "Checkboxes" 链接
6. 勾选第一个复选框
7. 点击第二个复选框两次（取消再勾选）
8. 验证复选框状态变化

**预期结果**:
- 链接点击后正确跳转
- 复选框点击后状态正确切换
- 按钮点击事件正常触发

**成功标准**:
- [PASS] 链接点击后 URL 正确变化
- [PASS] 复选框状态正确切换（checked/unchecked）
- [PASS] 连续点击操作正常执行
- [FAIL] 点击无响应
- [FAIL] 跳转目标错误
- [FAIL] 元素状态未变化

---

### T4: 表单输入 (Form Input)

**权重**: 1.2 (核心功能)

**测试步骤**:
1. 导航至 https://the-internet.herokuapp.com/login
2. 在用户名输入框输入 "tomsmith"
3. 在密码输入框输入 "SuperSecretPassword!"
4. 点击登录按钮
5. 验证登录成功后的页面内容
6. 导航至 https://the-internet.herokuapp.com/dropdown
7. 选择下拉框选项 "Option 1"
8. 验证选项被选中
9. 切换至 "Option 2"
10. 验证选项变更

**预期结果**:
- 文本输入正确填入
- 登录表单提交成功
- 下拉选择器选项正确切换
- 表单验证消息正确显示（如适用）

**成功标准**:
- [PASS] 文本正确输入到指定字段
- [PASS] 表单提交成功，页面跳转正确
- [PASS] 下拉选项正确选择
- [PASS] 选项切换后状态正确更新
- [FAIL] 输入内容未填入或错误
- [FAIL] 表单提交失败
- [FAIL] 下拉选择无效

---

### T5: 内容提取 (Content Extraction)

**权重**: 1.0 (基础必备)

**测试步骤**:
1. 导航至 https://httpbin.org/html
2. 提取页面标题文本
3. 提取 H1 元素文本
4. 提取第一个段落的文本内容
5. 导航至 https://the-internet.herokuapp.com/login
6. 提取输入框的 placeholder 属性
7. 提取按钮的 type 属性
8. 提取页面中所有链接的 href 属性列表

**预期结果**:
- 元素文本内容正确提取
- 元素属性值正确获取
- 批量提取返回完整列表

**成功标准**:
- [PASS] 文本内容与预期一致
- [PASS] 属性值正确获取
- [PASS] 批量提取无遗漏
- [PASS] 特殊字符正确处理
- [FAIL] 提取内容为空
- [FAIL] 提取内容与预期不符
- [FAIL] 属性获取失败

---

### T6: 截图功能 (Screenshot)

**权重**: 0.8 (进阶功能)

**测试步骤**:
1. 导航至 https://httpbin.org
2. 截取完整页面截图
3. 验证截图文件生成且大小 > 0
4. 导航至 https://the-internet.herokuapp.com/login
5. 截取特定元素（登录表单）截图
6. 验证元素截图文件生成
7. 设置视口大小为 1920x1080，截取截图
8. 设置视口大小为 375x667（移动端），截取截图
9. 验证不同分辨率截图差异

**预期结果**:
- 页面截图文件正确生成
- 元素截图仅包含目标元素
- 不同视口大小截图显示正确

**成功标准**:
- [PASS] 截图文件成功创建
- [PASS] 文件大小大于 0 字节
- [PASS] 元素截图范围正确
- [PASS] 不同分辨率截图内容适配
- [FAIL] 截图文件未生成
- [FAIL] 截图文件损坏（大小为0）
- [FAIL] 元素截图包含错误区域

---

### T7: 等待机制 (Waiting Mechanisms)

**权重**: 1.5 (核心功能，动态页面必备)

**测试步骤**:
1. 导航至 https://the-internet.herokuapp.com/dynamic_loading/1
2. 点击 "Start" 按钮
3. 使用显式等待，等待 "Hello World!" 文本出现（最长 10 秒）
4. 验证等待成功，文本正确显示
5. 导航至 https://the-internet.herokuapp.com/dynamic_loading/2
6. 点击 "Start" 按钮
7. 等待隐藏元素渲染完成
8. 验证元素可见且内容正确
9. 导航至 https://the-internet.herokuapp.com/dynamic_controls
10. 点击 "Remove" 按钮
11. 等待复选框消失（使用等待条件）
12. 点击 "Add" 按钮
13. 等待复选框重新出现

**预期结果**:
- 显式等待正确识别元素出现
- 等待超时设置正常工作
- 元素状态变化正确检测

**成功标准**:
- [PASS] 动态内容加载后被正确检测
- [PASS] 等待在超时前成功返回
- [PASS] 元素可见性变化正确捕获
- [PASS] 等待条件可自定义配置
- [FAIL] 等待超时但元素实际存在
- [FAIL] 未等待导致获取空内容
- [FAIL] 元素状态变化未检测

---

### T8: 错误处理 (Error Handling)

**权重**: 1.2 (核心功能)

**测试步骤**:
1. 导航至 https://httpbin.org
2. 尝试定位不存在的元素 `#nonexistent-element-12345`
3. 验证抛出正确的异常类型
4. 尝试在 1 秒内定位延迟加载的元素（设置较短超时）
5. 验证超时异常正确抛出
6. 尝试点击隐藏元素（定位到但不可交互）
7. 验证错误处理行为
8. 尝试导航至无效 URL `https://invalid-domain-12345.com`
9. 验证网络错误处理
10. 使用 try-catch 包裹操作，验证异常信息完整性

**预期结果**:
- 元素不存在时抛出明确异常
- 超时情况正确处理
- 网络错误有清晰提示
- 异常信息包含足够调试信息

**成功标准**:
- [PASS] 元素不存在时抛出特定异常
- [PASS] 超时异常包含超时信息
- [PASS] 网络错误被正确捕获
- [PASS] 异常信息包含选择器/URL 等上下文
- [FAIL] 元素不存在但无异常
- [FAIL] 超时未触发或触发错误
- [FAIL] 异常信息缺失关键上下文

---

## 评分标准

### 总分计算

```
总分 = Σ(测试项得分 × 权重)

其中：
- 测试项得分：1 (PASS) 或 0 (FAIL)
- 权重：各测试项的建议权重
```

### 能力等级

| 等级 | 得分区间 | 说明 |
|------|----------|------|
| 优秀 | 90-100% | 完全满足所有核心功能，可投入生产使用 |
| 良好 | 70-89% | 满足大部分功能，少量边界情况需处理 |
| 合格 | 50-69% | 基础功能可用，存在明显功能缺失 |
| 不合格 | <50% | 功能严重缺失，不建议使用 |

### 各测试项权重汇总

| 测试项 | 权重 | 加权后满分 |
|--------|------|-----------|
| T1 基础导航 | 1.0 | 1.0 |
| T2 元素定位 | 1.0 | 1.0 |
| T3 点击交互 | 1.0 | 1.0 |
| T4 表单输入 | 1.2 | 1.2 |
| T5 内容提取 | 1.0 | 1.0 |
| T6 截图功能 | 0.8 | 0.8 |
| T7 等待机制 | 1.5 | 1.5 |
| T8 错误处理 | 1.2 | 1.2 |
| **总计** | **8.7** | **8.7** |

---

## 测试执行模板

### 测试记录表

```markdown
| 测试项 | 目标网站 | 执行时间 | 结果 | 备注 |
|--------|----------|----------|------|------|
| T1 | httpbin.org | | PASS/FAIL | |
| T2 | the-internet | | PASS/FAIL | |
| ... | ... | | ... | |
```

### 环境信息

记录以下信息以便复现：
- 浏览器自动化工具名称及版本：
- 浏览器类型及版本：
- 操作系统：
- 执行时间：
- 网络环境：

---

## 附录

### 参考资源

- httpbin.org: https://httpbin.org
- The Internet Herokuapp: https://the-internet.herokuapp.com
- Playwright 测试示例: https://playwright.dev/docs/intro
- Puppeteer 测试示例: https://pptr.dev/guides/evaluation
- Selenium 文档: https://www.selenium.dev/documentation/

### 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-03-02 | 初始版本，包含 8 个测试项 |
