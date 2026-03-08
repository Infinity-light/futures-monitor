import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright 测评配置文件
 */
export default defineConfig({
  testDir: '.',
  testMatch: 'eval.spec.ts',

  /* 运行测试文件时完全并行 */
  fullyParallel: false, // 按顺序执行测试

  /* 如果测试失败，禁止有残留 */
  forbidOnly: !!process.env.CI,

  /* 失败时重试次数 */
  retries: 0,

  /* 并行工作进程数 */
  workers: 1,

  /* 报告器配置 */
  reporter: [
    ['list'],
    ['html', { outputFolder: '../playwright-report' }],
    ['json', { outputFile: '../playwright-report/results.json' }]
  ],

  /* 共享所有测试的选项 */
  use: {
    /* 基础 URL */
    baseURL: undefined,

    /* 收集所有跟踪信息 */
    trace: 'on',

    /* 截图 */
    screenshot: 'off',

    /* 视频录制 */
    video: 'off',

    /* 视口大小 */
    viewport: { width: 1280, height: 720 },

    /* 浏览器启动选项 */
    launchOptions: {
      slowMo: 0,
    },
  },

  /* 项目配置 */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /* 测试超时时间 */
  timeout: 60000,

  /* 期望超时时间 */
  expect: {
    timeout: 10000,
  },
});
