# rule-keeper-pro

[![skills.sh](https://skills.sh/b/adouwt/rule-keeper)](https://skills.sh/adouwt/rule-keeper)

> 一个用于在项目迭代中**持续维护项目规则文件**的 AI Skill。
> 让 AI 协作中的"项目契约"（AGENTS.md / CLAUDE.md / .cursor/rules 等）始终保持最新、够薄、够硬、可执行。

## 安装

```bash
# 安装到当前项目
npx skills add adouwt/rule-keeper

# 安装到全局（所有项目可用）
npx skills add adouwt/rule-keeper -g

# 只装这一个 skill
npx skills add adouwt/rule-keeper --skill rule-keeper-pro

# 指定装到某个 agent（如 cursor / devin / claude-code）
npx skills add adouwt/rule-keeper -a cursor -a devin
```

## 这是什么

在 AI 辅助开发中，项目规则文件（如 `AGENTS.md`）是 AI 与协作者的行为契约：记录**已经做出的决策和约定**，而不是代码事实。但规则文件很容易随着项目演进逐渐漂移、膨胀、失效——`rule-keeper-pro` 就是用来解决这个问题的。

它会在合适的时机（功能完成 / PR 合并 / 会话收尾）主动触发，把本轮值得固化的**决策、约定、边界、踩坑、验收标准**写入规则文件，同时修订或删除已过期内容，保证规则：

- **够薄**：6 段固定结构，默认 150 行硬上限
- **够硬**：每条都是祈使句、可校验、跨章节不重复
- **可执行**：只写高信号规则，不写实现细节、临时状态、常识

## 适用场景

- 团队/个人在用 Cursor、Devin、Claude 等 AI 工具协作开发，希望项目规则文件随迭代自动维护
- 项目已有 `AGENTS.md` / `CLAUDE.md` / `.cursor/rules` 等规则文件，但没人维护、逐渐失效
- 想从零建立一份"够薄够硬"的项目规则契约

## 手动安装（不通过 skills CLI）

直接把本项目文件夹拷贝到对应 AI 工具的 skills 目录即可，支持 Cursor、Devin 等工具。

```bash
# 以 Devin 为例（用户级 skill 目录）
cp -r skills/rule-keeper-pro ~/.config/devin/skills/rule-keeper-pro

# 以 Cursor 为例
cp -r skills/rule-keeper-pro ~/.cursor/skills/rule-keeper-pro
```

无需额外依赖，仅用到 Python 3 标准库（脚本位于 `skills/rule-keeper-pro/scripts/`）。

## 目录结构

```
rule-keeper/
├── readme.md                                  # 仓库级说明（本文件）
└── skills/
    └── rule-keeper-pro/                       # skill 目录（目录名即 skill 名）
        ├── SKILL.md                           # Skill 主入口：工作流程与触发时机
        ├── assets/
        │   └── AGENTS.md.tmpl                  # 规则文件模板（6 段结构）
        ├── references/
        │   └── rules-file-spec.md              # 规则文件格式规范（结构、句式、闸门）
        └── scripts/
            ├── find_rules_files.py             # 定位项目中的规则文件（只读）
            └── validate_rules.py               # 校验规则文件结构与质量（只读）
```

## 工作流程（7 步）

`rule-keeper-pro` 在被触发后，会按以下流程执行：

1. **定位规则文件** —— 运行 `skills/rule-keeper-pro/scripts/find_rules_files.py <项目根>`，优先复用已存在的规则文件；不存在时从 `skills/rule-keeper-pro/assets/AGENTS.md.tmpl` 新建。
2. **读取现状与采集变更信号** —— 通读规则文件，从会话决策、git 历史、约定风格、踩坑、验收标准中收集"可能值得写入"的信号。
3. **评估并分类** —— 逐条过三道闸门（高信号 / 无重复 / 无矛盾），打标签：新增 / 修订 / 删除 / 合并 / 不变。
4. **最小化写入** —— 用 `Edit` 增量修改，保留原措辞，新条目镜像相邻条目格式。
5. **超额瘦身** —— 超过行数上限时长说明改链接、同模式合并、删除"过去是什么"的条目。
6. **校验与自检** —— 运行 `skills/rule-keeper-pro/scripts/validate_rules.py <规则文件>`，并跑一遍自检清单。
7. **汇报** —— 输出文件路径、变更小结（新增/修订/删除/合并各几条及原因）、当前行数/上限。

## 规则文件结构（6 段，默认 ≤ 150 行）

| § | 章节 | 用途 | 行数预算 |
| --- | --- | --- | --- |
| 1 | 项目指纹 | name / goal / stack / repo | ≤8 |
| 2 | 架构骨架 | 分层、模块、依赖方向 | ≤40 |
| 3 | 硬约束 | DO / DON'T 祈使句 | ≤50 |
| 4 | 关键决策 | 表格：决策 + 原因 + 拒绝的替代方案 | ≤30 |
| 5 | 工作流 | dev / test / commit / doc ritual | ≤20 |
| 6 | 元规则 | 本文件自身的更新协议 | ≤10 |

- 默认硬上限 150 行；在文件头部声明 `maxLines: 200` 可覆盖（适用于大项目）。
- 完整模板见 `skills/rule-keeper-pro/assets/AGENTS.md.tmpl`，格式规范见 `skills/rule-keeper-pro/references/rules-file-spec.md`。

## 脚本用法

### 定位规则文件

```bash
python3 skills/rule-keeper-pro/scripts/find_rules_files.py [项目根目录]
# 默认以当前目录为项目根；列出候选规则文件，未找到时建议在项目根创建 AGENTS.md
```

### 校验规则文件

```bash
python3 skills/rule-keeper-pro/scripts/validate_rules.py <规则文件路径>
# 退出码：0 = 通过或仅警告；1 = 存在错误；2 = 用法错误
```

校验项包括：行数上限、6 段结构完整性、重复分区/重复规则行、超长行、规则条目数、TODO/占位残留、元数据完整性等。

## 与其他文件的边界

| 文件 | 放什么 |
| --- | --- |
| `AGENTS.md`（本 skill 输出） | 项目设计 —— 代码**是**什么 / **必须**怎么写 |
| `USER.md` | 用户偏好 —— 语气、语言、工作风格 |
| `~/.workbuddy/MEMORY.md` 与 daily log | 历史 —— 做过什么、什么时候做 |

**绝不**把用户偏好写进 AGENTS.md；**绝不**把架构规则写进 USER.md；**绝不**把时间线活动写进 AGENTS.md。

## 核心原则

- **只写高信号规则**：决策、约定、边界、踩坑、验收标准；不写实现细节、临时状态、代码里已能体现的事实。
- **少而硬**：规则宁缺毋滥；能由 lint / CI 等工具自动保证的内容不写进规则。
- **每次变更过三道闸门**：高信号、无重复、无矛盾。
- **无强信号就不更新**：评估后若没有值得固化的变更，如实报告"本轮无需更新"，不为更新而更新。
- **薄而硬**：6 段固定结构，默认 150 行硬上限，每段有行数预算，超额必须瘦身。

## License

MIT
