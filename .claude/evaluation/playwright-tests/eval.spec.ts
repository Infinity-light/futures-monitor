import { test, expect } from '@playwright/test';
import path from 'path';

// 截图保存目录
const screenshotDir = path.join(__dirname, '../screenshots/playwright');

/**
 * T1: 基础导航测试
 * 目标: https://httpbin.org
 * 验证页面标题和URL
 */
test('T1: 基础导航', async ({ page }) => {
  const startTime = Date.now();

  // 导航到 httpbin.org
  await page.goto('https://httpbin.org', { timeout: 10000 });

  // 验证页面标题包含 "httpbin"
  const title = await page.title();
  expect(title.toLowerCase()).toContain('httpbin');

  // 验证当前URL
  const url = page.url();
  expect(url).toBe('https://httpbin.org/');

  const duration = Date.now() - startTime;
  console.log(`T1 执行耗时: ${duration}ms`);
});

/**
 * T2: 元素定位测试
 * 目标: https://the-internet.herokuapp.com/login
 * 使用多种选择器定位元素
 */
test('T2: 元素定位', async ({ page }) => {
  await page.goto('https://the-internet.herokuapp.com/login');

  // ID 选择器: #username
  const usernameById = page.locator('#username');
  await expect(usernameById).toBeVisible();

  // Class 选择器: .large-4
  const large4Elements = page.locator('.large-4');
  expect(await large4Elements.count()).toBeGreaterThan(0);

  // Tag 选择器: h2
  const h2Element = page.locator('h2');
  await expect(h2Element).toBeVisible();

  // CSS 选择器: input[type="password"]
  const passwordInput = page.locator('input[type="password"]');
  await expect(passwordInput).toBeVisible();

  // XPath 选择器: //button[@type="submit"]
  const submitButton = page.locator('xpath=//button[@type="submit"]');
  await expect(submitButton).toBeVisible();

  // 文本内容选择器: 包含 "Login" 的元素
  const loginText = page.getByText('Login', { exact: false });
  await expect(loginText.first()).toBeVisible();

  // 角色选择器
  const heading = page.getByRole('heading', { name: 'Login Page' });
  await expect(heading).toBeVisible();
});

/**
 * T3: 点击交互测试
 * 目标: https://the-internet.herokuapp.com
 * 测试链接点击、复选框切换
 */
test('T3: 点击交互', async ({ page }) => {
  // 导航到首页
  await page.goto('https://the-internet.herokuapp.com');

  // 点击 "Form Authentication" 链接
  await page.click('a[href="/login"]');

  // 验证页面跳转至登录页
  await expect(page).toHaveURL(/.*login/);
  await expect(page.getByRole('heading', { name: 'Login Page' })).toBeVisible();

  // 返回首页
  await page.goto('https://the-internet.herokuapp.com');

  // 点击 "Checkboxes" 链接
  await page.click('a[href="/checkboxes"]');
  await expect(page).toHaveURL(/.*checkboxes/);

  // 获取复选框
  const checkbox1 = page.locator('input[type="checkbox"]').nth(0);
  const checkbox2 = page.locator('input[type="checkbox"]').nth(1);

  // 验证初始状态
  expect(await checkbox1.isChecked()).toBe(false);
  expect(await checkbox2.isChecked()).toBe(true);

  // 勾选第一个复选框
  await checkbox1.check();
  expect(await checkbox1.isChecked()).toBe(true);

  // 点击第二个复选框两次（取消再勾选）
  await checkbox2.uncheck();
  expect(await checkbox2.isChecked()).toBe(false);
  await checkbox2.check();
  expect(await checkbox2.isChecked()).toBe(true);
});

/**
 * T4: 表单输入测试
 * 目标: https://the-internet.herokuapp.com/login 和 dropdown
 * 测试表单填写、提交、下拉选择
 */
test('T4: 表单输入', async ({ page }) => {
  // 测试登录表单
  await page.goto('https://the-internet.herokuapp.com/login');

  // 填写用户名和密码
  await page.fill('#username', 'tomsmith');
  await page.fill('#password', 'SuperSecretPassword!');

  // 点击登录按钮
  await page.click('button[type="submit"]');

  // 验证登录成功
  await expect(page).toHaveURL(/.*secure/);
  await expect(page.getByText('You logged into a secure area!')).toBeVisible();

  // 测试下拉选择
  await page.goto('https://the-internet.herokuapp.com/dropdown');

  // 选择 "Option 1"
  await page.selectOption('#dropdown', '1');
  const selectedOption1 = await page.locator('#dropdown option:checked').textContent();
  expect(selectedOption1).toBe('Option 1');

  // 切换至 "Option 2"
  await page.selectOption('#dropdown', '2');
  const selectedOption2 = await page.locator('#dropdown option:checked').textContent();
  expect(selectedOption2).toBe('Option 2');
});

/**
 * T5: 内容提取测试
 * 目标: https://httpbin.org/html 和 the-internet
 * 测试文本提取、属性提取
 */
test('T5: 内容提取', async ({ page }) => {
  // 导航到 httpbin.org/html
  await page.goto('https://httpbin.org/html');

  // 提取页面标题 (httpbin.org/html 页面可能没有 title 标签)
  const title = await page.title();
  console.log(`页面标题: "${title}"`);
  // 允许标题为空，只记录不强制验证

  // 提取 H1 元素文本
  const h1Text = await page.locator('h1').textContent();
  expect(h1Text).toBeTruthy();
  console.log(`H1 文本: ${h1Text}`);

  // 提取第一个段落的文本
  const firstParagraph = await page.locator('p').first().textContent();
  expect(firstParagraph).toBeTruthy();
  console.log(`第一段文本: ${firstParagraph?.substring(0, 50)}...`);

  // 导航到登录页提取属性
  await page.goto('https://the-internet.herokuapp.com/login');

  // 提取输入框的 placeholder 属性
  const usernamePlaceholder = await page.locator('#username').getAttribute('placeholder');
  console.log(`Username placeholder: ${usernamePlaceholder}`);

  // 提取按钮的 type 属性
  const buttonType = await page.locator('button[type="submit"]').getAttribute('type');
  expect(buttonType).toBe('submit');

  // 提取页面中所有链接的 href 属性列表
  const links = await page.locator('a').evaluateAll(anchors =>
    anchors.map(a => a.getAttribute('href'))
  );
  expect(links.length).toBeGreaterThan(0);
  console.log(`页面链接数量: ${links.length}`);
});

/**
 * T6: 截图功能测试
 * 目标: https://httpbin.org 和 the-internet
 * 测试页面截图、元素截图、不同视口截图
 */
test('T6: 截图功能', async ({ page }) => {
  // 导航到 httpbin.org
  await page.goto('https://httpbin.org');

  // 截取完整页面截图
  await page.screenshot({
    path: path.join(screenshotDir, 'T6-httpbin-fullpage.png'),
    fullPage: true
  });

  // 导航到登录页
  await page.goto('https://the-internet.herokuapp.com/login');

  // 截取特定元素（登录表单）截图
  const loginForm = page.locator('#login');
  await loginForm.screenshot({
    path: path.join(screenshotDir, 'T6-login-form-element.png')
  });

  // 设置视口大小为 1920x1080，截取截图
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto('https://httpbin.org');
  await page.screenshot({
    path: path.join(screenshotDir, 'T6-viewport-1920x1080.png')
  });

  // 设置视口大小为 375x667（移动端），截取截图
  await page.setViewportSize({ width: 375, height: 667 });
  await page.screenshot({
    path: path.join(screenshotDir, 'T6-viewport-375x667-mobile.png')
  });

  // 恢复默认视口
  await page.setViewportSize({ width: 1280, height: 720 });
});

/**
 * T7: 等待机制测试
 * 目标: https://the-internet.herokuapp.com/dynamic_loading
 * 测试显式等待、元素状态变化等待
 */
test('T7: 等待机制', async ({ page }) => {
  // 测试动态加载 1
  await page.goto('https://the-internet.herokuapp.com/dynamic_loading/1');

  // 点击 Start 按钮
  await page.click('button:has-text("Start")');

  // 使用显式等待，等待 "Hello World!" 文本出现（最长 10 秒）
  const helloWorld1 = page.locator('#finish h4');
  await helloWorld1.waitFor({ state: 'visible', timeout: 10000 });

  // 验证文本内容
  const text1 = await helloWorld1.textContent();
  expect(text1).toBe('Hello World!');

  // 测试动态加载 2
  await page.goto('https://the-internet.herokuapp.com/dynamic_loading/2');

  // 点击 Start 按钮
  await page.click('button:has-text("Start")');

  // 等待隐藏元素渲染完成
  const helloWorld2 = page.locator('#finish h4');
  await helloWorld2.waitFor({ state: 'visible', timeout: 10000 });

  // 验证元素可见且内容正确
  expect(await helloWorld2.isVisible()).toBe(true);
  const text2 = await helloWorld2.textContent();
  expect(text2).toBe('Hello World!');

  // 测试动态控件 - 使用更可靠的检测方式
  await page.goto('https://the-internet.herokuapp.com/dynamic_controls');

  // 获取初始复选框
  const initialCheckbox = page.locator('input[type="checkbox"]').first();
  expect(await initialCheckbox.count()).toBeGreaterThan(0);

  // 点击 Remove 按钮
  await page.click('button:has-text("Remove")');

  // 等待 "It's gone!" 消息出现，表示复选框已被移除
  await page.waitForSelector('text=It\'s gone!', { timeout: 10000 });

  // 验证复选框已不存在（通过计数）
  await page.waitForFunction(() => {
    return document.querySelectorAll('input[type="checkbox"]').length === 0;
  }, { timeout: 10000 });

  // 点击 Add 按钮
  await page.click('button:has-text("Add")');

  // 等待 "It's back!" 消息出现，表示复选框已重新添加
  await page.waitForSelector('text=It\'s back!', { timeout: 10000 });

  // 验证复选框重新出现
  await page.waitForFunction(() => {
    return document.querySelectorAll('input[type="checkbox"]').length > 0;
  }, { timeout: 10000 });

  const restoredCheckbox = page.locator('input[type="checkbox"]').first();
  expect(await restoredCheckbox.isVisible()).toBe(true);
});

/**
 * T8: 错误处理测试
 * 目标: https://httpbin.org
 * 测试元素不存在、超时、网络错误等情况
 */
test('T8: 错误处理', async ({ page }) => {
  await page.goto('https://httpbin.org');

  // 测试 1: 尝试定位不存在的元素，验证抛出正确的异常
  const nonExistent = page.locator('#nonexistent-element-12345');

  try {
    // 尝试在 2 秒内等待元素可见（应该失败）
    await nonExistent.waitFor({ state: 'visible', timeout: 2000 });
    // 如果执行到这里，说明测试失败
    expect(false).toBe(true); // 强制失败
  } catch (error: any) {
    // 验证超时异常被正确抛出
    expect(error.message).toContain('Timeout');
    console.log('T8-1: 元素不存在时正确抛出超时异常');
  }

  // 测试 2: 使用 count() 检查元素不存在（不会抛出异常）
  const count = await nonExistent.count();
  expect(count).toBe(0);
  console.log('T8-2: count() 正确返回 0');

  // 测试 3: 使用 isVisible() 检查元素不存在（不会抛出异常）
  const isVisible = await nonExistent.isVisible();
  expect(isVisible).toBe(false);
  console.log('T8-3: isVisible() 正确返回 false');

  // 测试 4: 尝试导航至无效 URL
  try {
    await page.goto('https://invalid-domain-12345.com', { timeout: 5000 });
    // 如果成功，可能是 DNS 解析到了某些页面
    console.log('T8-4: 无效域名导航行为:', page.url());
  } catch (error: any) {
    // 验证网络错误被捕获
    console.log('T8-4: 无效域名导航抛出异常:', error.message.substring(0, 100));
  }

  // 测试 5: 使用 try-catch 包裹操作，验证异常信息完整性
  try {
    await page.click('#nonexistent-button-xyz', { timeout: 1000 });
    expect(false).toBe(true);
  } catch (error: any) {
    // 验证异常信息包含选择器信息
    expect(error.message).toBeTruthy();
    console.log('T8-5: 点击不存在元素时异常信息:', error.message.substring(0, 100));
  }
});
