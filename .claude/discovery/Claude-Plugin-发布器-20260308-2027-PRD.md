# PRD: Claude Plugin 发布器

## 1. 当前状态
- 当前团队已经明确：Skill/Plugin 的规范更新不应直接改运行缓存或 settings，而应回到 canonical source 修改，再经版本、marketplace、云端与本地安装链路逐层同步。
- 当前 cytopia 体系已经具备完整的 Claude Plugin 结构：
  - 源仓：`cytopia-workflow/`
  - plugin manifest：`skills/workflow-kit/plugin.json`
  - marketplace 索引：`.claude-plugin/marketplace.json`
  - 本地 marketplace clone：`~/.claude/plugins/marketplaces/<marketplace>`
  - 本地安装缓存：`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>`
  - 已安装状态记录：`~/.claude/plugins/installed_plugins.json`
  - 已知 marketplace 记录：`~/.claude/plugins/known_marketplaces.json`
- 当前已经完成 Discovery Skill 本体的重写，但还没有一个通用的“修改插件内部内容并全链路发版生效”的专用 Skill。
- 当前 `skills-updater` 只覆盖 marketplace 更新和部分重装辅助，不等于完整发布闭环；其中 `update_marketplace.py` 的 reinstall 仍偏半自动（通过 `.pending_installs` 记录命令），不是最终的发布-生效验证器。

## 2. 目标结果
- 创建一个首版可用的 **Claude Plugin 发布器 Skill**。
- 该 Skill 的目标不是只服务 `workflow-kit`，而是服务于**任何采用 Claude Plugin 结构**的插件：
  - 有 canonical source
  - 有 `plugin.json` 或同等 manifest
  - 有 marketplace / registry 索引
  - 有本地 marketplace clone
  - 有本地 cache 安装目录
  - 有本地 installed state 记录
- 该 Skill 必须覆盖全链路闭环：
  1. 定位唯一源头
  2. 检查 plugin/marketplace 隐藏约束
  3. 更新源文件后同步版本与索引
  4. 同步云端
  5. 刷新本地 marketplace / install
  6. 验证 cache 与当前系统生效
- 该 Skill 必须区分：
  - 安装层已生效
  - 当前会话已确认使用新版
  二者不可混为一谈。

## 3. 约束与边界
- 包含：
  - Claude Plugin 结构下的发布流程抽象
  - 单一真相源定位
  - 版本与 marketplace 索引同步
  - 云端发布
  - 本地 marketplace update / install / reinstall
  - 安装态与运行态验证
  - 失败分支与阻断规则
- 不包含：
  - 任意非 Claude Plugin 生态的通用扩展发布器
  - 首版直接覆盖 npx skills / skills.sh 的全部生态
  - 自动处理所有 GitHub Release / Tag 策略
  - 自动替用户执行高风险外部操作而不确认
- 硬约束：
  - 不允许直接编辑 cache 作为源头
  - settings 不承载 Skill 正文
  - manifest 存在硬校验约束，发布前必须检查
  - 若源头不唯一、manifest 不合法、版本未同步、云端失败、本地未生效，必须给出失败结论，不能伪装为成功

## 4. 全部可达路径对比

### 路径 A：仅为 workflow-kit 定制的发布器
- 成立条件：目标只服务当前 `cytopia-workflow` 结构，短期只需要给本团队使用。
- 关键变量：实现速度、目录耦合度、复用性、后续重构成本。
- 对用户的影响：最容易快速落地，但一旦插件根路径、marketplace 名或仓库结构变化，就需要重写；给别人使用时泛化能力差。
- 结论：不选。因为用户已经明确要求不能只绑定 Discovery、不能只绑定当前放置方式，且希望别人也能用。

### 路径 B：面向 Claude Plugin 结构的通用发布器（选定）
- 成立条件：目标对象具备 plugin manifest、marketplace/registry、本地 clone、cache 和安装记录等稳定结构特征。
- 关键变量：泛化程度、首版复杂度、可复用性、落地可控性。
- 对用户的影响：既能覆盖当前 cytopia-workflow，也能迁移到别的 Claude Plugin 仓库；抽象层级足够稳，且不会像“任意扩展发布器”那样过度抽象。
- 结论：选定。它是当前最平衡的路径。

### 路径 C：抽象到任意扩展包生态的超通用发布器
- 成立条件：需要统一处理不止 Claude Plugin，还要覆盖其他生态与安装模型。
- 关键变量：抽象成本、定义复杂度、规则漂移、首版交付速度。
- 对用户的影响：理论复用面最大，但首版会过重，且大量约束会变成“猜测式泛化”，增加实现风险。
- 结论：当前不选。等 Claude Plugin 发布链跑通并稳定后，才有必要向上再抽象。

## 5. 关键决策
- 决策 1：Skill 的抽象层级选择 **Claude Plugin 发布器**
  - 决策理由：保留泛化能力，同时避免抽象过头。
  - 对用户的影响：既可服务当前 workflow-kit，也可迁移给其他 Claude Plugin 使用者。

- 决策 2：首版闭环范围选择 **全链路**
  - 决策理由：仅做到源头修改或仅做到云端发布，都不能证明“新版真的生效”。
  - 对用户的影响：减少“看起来发版了，实际本地还没生效”的假阳性。

- 决策 3：采用 **四层模型** 作为稳定不变量
  - 决策理由：发布问题本质上就是源头层、元数据层、云端层、本地运行层的同步问题。
  - 对用户的影响：后续无论仓库位置怎么换，只要仍属于 Claude Plugin 体系，就能复用同样的发布逻辑。

- 决策 4：发布 Skill 必须内建 **manifest 隐藏约束检查**
  - 决策理由：`plugin.json` 的真实校验规则比公开示例严格，若不检查，安装阶段才会暴雷。
  - 对用户的影响：降低“本地改完、云端发出、安装失败”的回滚成本。

- 决策 5：生效验证必须至少做到三层
  - 决策理由：单看 install 成功提示不可靠。
  - 对用户的影响：发布 Skill 需要检查：
    1. `installed_plugins.json` 是否更新
    2. `cache/` 是否出现新版本或新 installPath
    3. 目标变更锚点是否进入运行态文件

## 6. 已清零的关键未决项
- “这个 Skill 是只做 workflow-kit 专用，还是做泛化版本？” → 结论：做 **Claude Plugin 发布器**。
- “首版闭环只到云端还是做到本地生效？” → 结论：做 **全链路闭环**。
- “settings 是否作为规则正文承载层？” → 结论：**不是**，settings 只负责启用和权限。
- “cache 是否可以作为修改源头？” → 结论：**不可以**，cache 只是安装结果。
- “发布成功是否等于 install 提示成功？” → 结论：**不等于**，必须做 installed state + cache + 锚点验证。
- “manifest 约束是否只靠经验？” → 结论：**不是**，已有隐藏规则文档，可纳入 Skill 的硬检查。

## 7. 进入 Planning 的前置共识
- 将创建一个新的 Skill，用于 Claude Plugin 的全链路发布与生效验证。
- 该 Skill 的对象不是特定的 Discovery，也不是特定目录，而是 Claude Plugin 体系本身。
- 首版默认流程应覆盖：
  ```text
  定位源头
  → 检查 manifest / marketplace 约束
  → 更新内容
  → 同步版本与索引
  → 云端发布
  → 本地 marketplace update / install
  → installed_plugins.json / cache / 锚点验证
  → 输出发布报告
  ```
- 当前已经具备进入 Planning 的条件：关键路径已选定、抽象层级已选定、闭环范围已选定、关键未决项已清零。
