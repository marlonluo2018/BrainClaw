# BrainClaw - 个人助理系统

**通过 AI IDE 将 AI 自动化带给非技术办公人员。**

## 为什么选择 BrainClaw？

OpenClaw 等自动化工具需要技术配置（二进制文件、环境变量、命令行），对普通办公人员造成门槛。此外，许多企业 IT 策略限制安装此类工具。

**BrainClaw 的解决方案：**
- 在企业已批准的 AI IDE 中运行
- 无需技术配置——打开 Markdown 文件即可开始
- 使用自然语言命令而非脚本
- 通过简单的记忆文件学习用户偏好

## 适用人群

- 想要 AI 辅助但不了解编程的办公人员
- 企业环境中软件安装受限的员工
- 想要自动化 Microsoft 365 任务但不想编码的团队
- 任何想要一个能学习自己偏好的个人助理的人

## 快速开始

### 设置（一次性）

1. 打开你的 AI IDE（Claude、Cursor 等）
2. 进入自定义指令 / 系统提示词设置
3. 粘贴 [`CLAUDE.md`](CLAUDE.md) 的内容（Claude Code 会自动加载；其他 IDE 需要手动粘贴）
4. 将工作区设置为 BrainClaw 文件夹

### 日常使用

1. 打开你的 AI IDE
2. 说 **"start"**、**"启动"** 或 **"start assistant"** 来激活完整助理
3. 助理加载 brain 文件，准备协助

（"hi"/"你好" 等问候语，以及 "帮我"/"help me" 等模糊用语**不会**自动启动助理 — 必须使用上述显式触发词。）

**无需安装。无需配置。无需命令行。**

## 工作原理

```
┌──────────────────────────────────────────────────────────────┐
│  AI IDE (Claude / Cursor / etc.)                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  系统提示词  (CLAUDE.md)                               │  │
│  │  "启动时，读取 brain 文件..."                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                        ↓                                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Brain 文件 (assistant_brain/)                        │  │
│  │  ├── SOUL.md               (身份与价值观)              │  │
│  │  ├── OPERATIONAL_RULES.md  (策略)                      │  │
│  │  ├── CONFIG.md             (参数)                      │  │
│  │  ├── workflows/            (编排 + 业务逻辑)           │  │
│  │  │   ├── TASK_WORKFLOW.md                              │  │
│  │  │   ├── EMAIL_WORKFLOW.md                             │  │
│  │  │   ├── STAKEHOLDER_WORKFLOW.md                       │  │
│  │  │   ├── RECORDING_WORKFLOW.md                         │  │
│  │  │   └── VIEWS_WORKFLOW.md                             │  │
│  │  ├── skills/               (I/O — 外部系统)            │  │
│  │  │   ├── outlook-skill/    (Outlook COM 后端)          │  │
│  │  │   ├── xlsx/             (Excel 读写)                │  │
│  │  │   └── skill-creator/    (新技能脚手架)              │  │
│  │  ├── tasks/                (任务队列)                  │  │
│  │  ├── memory/               (偏好记忆)                  │  │
│  │  └── process/              (操作流程)                  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## 功能概览

| 功能 | 描述 |
|------|------|
| **任务管理** | 详细任务追踪，包含状态、优先级、分类、地理位置、截止时间、RACI 利益相关方、父子关系、结构化 `Asks`（我欠的 / 别人欠我的）|
| **视图引擎** | `status T###`(或直接 `T###`) / `待我处理` / `等待` / `before {人}` / `review` —— 跨任务揭示逾期、欠回复、述职素材 |
| **邮件管理** | 通过原生 Outlook COM 查找、搜索、线程追踪、撰写邮件。匹配到任务时 AI 自动抽取 ask/decision/deadline 写入任务的结构化区块 |
| **邮件线程追踪** | 通过 Outlook ConversationID 跨文件夹查找完整对话线程 |
| **关联邮件发现** | 多策略搜索（线程 + 发件人 + 关键词）实现跨线程发现 |
| **记忆系统** | 用户偏好、认知盲点模式、外部联系人、成就（述职事实库）|
| **成就自动捕获** | 任务完成时 AI 从 `[decision]` / `[milestone]` / `[delivery]` 标签的 Timeline 抽取述职素材 |
| **流程管理** | 按地区分组的结构化流程文件，带索引和参考系统 |
| **定期任务** | 自动创建定期任务（月度报告、季度流程） |
| **Office 文档** | 通过 `xlsx` skill 处理 Excel 文件 |
| **可扩展技能** | 通过模块化技能系统添加新能力 |

## 技能

技能仅用于与外部系统交互（I/O）。业务逻辑（任务生命周期、RACI、事件记录、邮件撰写规则）直接写在 workflow 文件里。

| 技能 | 用途 | 外部系统 |
|------|------|----------|
| **outlook-skill** | 查找、线程、关联、撰写、回复、批量转发 | Microsoft Outlook (COM) |
| **xlsx** | Excel/电子表格文件读写 | `.xlsx`、`.csv` |
| **skill-creator** | 新技能脚手架 | (元) |

## 邮件命令

所有命令使用 `find-*` 命名约定：

| 命令 | 默认范围 | 用途 |
|------|----------|------|
| `find-recent` | 仅收件箱 | 查看最新邮件 |
| `find` | 仅收件箱 | 按主题/发件人/正文搜索 |
| `find-thread` | 收件箱 + 已发送 | 拉取完整对话链 |
| `find-related` | 收件箱 + 已发送 | 发现跨线程关联邮件 |
| `get-email` | — | 通过 entry_id 查看完整邮件 |

**策略：** 已发送邮件在任务文件中追踪（`## Email References`）。`find` 和 `find-recent` 默认仅搜索收件箱。线程和关联搜索自动包含已发送邮件以确保完整性。

## 项目结构

标记 ⭐ 的文件在**启动时加载**。其他文件**按需加载**。

```
BrainClaw/
├── CLAUDE.md                           # 系统提示词（单一可信源）
├── README.md                           # 英文说明
├── README_CN.md                        # 中文说明（本文件）
├── ARCHITECTURE.md                     # 系统架构
└── assistant_brain/
    ├── SOUL.md               ⭐ # 身份与价值观（不变的核心）
    ├── OPERATIONAL_RULES.md  ⭐ # 核心策略
    ├── CONFIG.md             ⭐ # 系统参数（用户信息、格式）
    ├── views_config.md       ⭐ # 视图命令的阈值与默认值
    ├── recurring_tasks.md    ⭐ # 定期任务定义
    ├── process/
    │   └── README.md         ⭐ # 流程索引（按地区分组）
    ├── workflows/               # 编排 + 业务逻辑（按需加载）
    │   ├── TASK_WORKFLOW.md
    │   ├── EMAIL_WORKFLOW.md
    │   ├── STAKEHOLDER_WORKFLOW.md
    │   ├── RECORDING_WORKFLOW.md
    │   └── VIEWS_WORKFLOW.md           # status/owed/waiting/before/review
    ├── contacts.md          ⭐ # 联系人唯一数据源（语气、邮箱、角色）
    ├── memory/                  # 用户衍生数据（系统从用户身上学到的）
    │   ├── preferences.md       ⭐ # 用户偏好（语气、时间格式等）
    │   ├── things_to_avoid.md   ⭐ # 认知盲点模式 + 战术 Don'ts
    │   ├── achievements.md         # 述职事实库（任务完成时自动喂养）
    │   ├── contacts.md             # 外部联系人（按需加载）
    │   └── tracking.md             # 已退役 — 功能转入任务的 Asks 区块
    ├── skills/                  # 与外部系统交互的 I/O
    │   ├── outlook-skill/        # Outlook COM — Python 后端 + CLI
    │   │   ├── SKILL.md          #   命令参考
    │   │   ├── scripts/          #   CLI 入口点
    │   │   └── backend/          #   搜索、撰写、会话管理
    │   ├── xlsx/                 # Excel 文件读写
    │   └── skill-creator/        # 新技能脚手架
    └── tasks/                   # 任务队列与历史
        ├── queue.md          ⭐ # 活跃任务 + 近期事件
        ├── FORMATS.md            # 任务格式规范
        ├── T0xx-xxx.md           # 活跃任务详情（按需加载）
        └── history/              # 已完成任务与月度归档
```

### 启动时加载的文件 (⭐)

以下文件在启动时加载，用于初始化助理：

| 文件 | 用途 |
|------|------|
| `SOUL.md` | 核心身份与原则 |
| `OPERATIONAL_RULES.md` | 行为策略与政策 |
| `CONFIG.md` | 用户设置与格式定义 |
| `memory/preferences.md` | 用户偏好 |
| `memory/things_to_avoid.md` | 认知盲点模式 + 战术 Don'ts |
| `views_config.md` | 视图命令的阈值与默认值 |
| `tasks/queue.md` | 活跃任务与近期事件 |
| `recurring_tasks.md` | 定期任务定义 |
| `contacts.md` | 联系人数据库 |
| `process/README.md` | 流程索引 |
| `skills/*/SKILL.md` frontmatter | 技能触发词与描述 |

其他所有文件（工作流文件、技能实现、详细利益相关方档案等）在需要特定操作时**按需加载**。

## 命令

> 直接用日常说法即可 —— 下面是例子,不是死板的命令。 AI 按意图匹配,不要求精确关键词。

| 想干啥 | 你可以这样说 | 系统怎么响应 |
|--------|------------|------------|
| **启动助理** | "start"、"启动"、"start assistant" | 加载 brain 文件,渲染按国家 → 优先级分组的完整任务列表,标记 overdue |
| **只想打招呼** | "hi"、"你好"、"help me"、"帮我" | 仅快速问候 — 模糊用语不会自动启动 |
| **某个任务啥状态** | "T033"、"T033 状态"、"查 T033"、"T033 怎么样了"、"看下 T033"、"status T033" | 一屏:当前卡点、欠的、近期决策 |
| **我欠谁啥** | "待我处理"、"我欠谁啥"、"我答应过啥"、"我有啥没回的"、"owed" | 跨任务汇总我的承诺,按对方分组,逾期优先 |
| **谁卡着我 / 谁没回** | "等待"、"我在等谁"、"啥事卡着"、"谁还没回我"、"waiting" | 跨任务汇总,按对方分组,按等待时长排序 |
| **会前预备** | "见 Beng 之前"、"明天和 Mridul 开会前"、"下午要见 X"、"before Beng" | 拉所有该人相关任务 + 议程草稿 |
| **述职 / 总结** | "述职"、"半年述职"、"Q2 做了啥"、"总结这半年"、"年度总结"、"review Q2 2026" | bullet 概要 + narrative 草稿,从 achievements.md 整理 |
| **看完整任务清单** | "全部任务"、"完整队列"、"show all" | 重新渲染启动同款分组任务列表 |
| **任务操作** | "新建任务"、"完成 T033"、"block T040"、"create/update/complete/block task" | 任务生命周期 |
| **邮件操作** | "查邮件"、"找 Beng 的邮件"、"draft email"、"reply"、"forward" | 邮件生命周期(现在自动抽取写入任务) |

## 任务管理特性

BrainClaw 提供企业级任务追踪：

- **丰富任务卡片**：状态、优先级、分类、地理位置（地理追踪）、截止时间、联系人、关键字、历史、备注
- **智能检测**：自动从上下文判断截止时间和优先级
- **智能关键字**：2-3个唯一标识符（请求ID、完整姓名、特定代码）便于追溯来源
- **历史追踪**：累加记录所有任务更新，包含时间戳和来源
- **父子任务**：主任务可以有子任务，用于复杂项目管理
- **地理追踪**：按区域追踪任务（Philippines, India, China, Singapore, APAC, Global）
- **定期任务**：自动创建定期任务（月度报告、季度流程）
- **邮件引用**：任务通过 Outlook entry_id 关联相关邮件，便于即时查找

### 关键字系统

BrainClaw 使用智能关键字系统帮助你追溯任务来源：

- **是什么**：每个任务2-3个唯一标识符（请求ID、完整姓名、特定代码）
- **为什么**：快速找到创建任务的原始邮件/文档
- **怎么做**：避免通用词汇，只使用特定标识符

**示例：**
- ✅ 好的：`CRT282911, Ashish Sah, Platform Developer II` → 找到精确邮件
- ✅ 好的：`Req 11695, Informatica PowerCenter` → 唯一请求
- ❌ 不好：`certification, approval, Salesforce` → 找到数百封邮件

## 记忆系统

BrainClaw 跨会话学习和记忆：

| 记忆文件 | 用途 |
|----------|------|
| `memory/preferences.md` | 用户偏好（时区、语气、时间格式）|
| `memory/things_to_avoid.md` | **Patterns**(认知盲点)+ **Tactical Don'ts**(输出格式错误)|
| `memory/achievements.md` | 述职事实库 — 任务完成时自动喂养;季度 × 类别两轴结构 |
| `memory/contacts.md` | 外部联系人（非同事）|
| `memory/tracking.md` | **已退役** — 功能转入任务的 `## Asks` 区块 + `owed`/`waiting` 视图 |
| `views_config.md` | (不是 memory — 系统配置) 视图命令的阈值和默认值。位于 `assistant_brain/` 根目录,不在 memory/ 下。 |

## 架构：工作流与技能

BrainClaw 采用分层架构，更好地组织代码：

```
CLAUDE.md (启动规则)
        ↓
OPERATIONAL_RULES.md (核心策略)
        ↓
┌──────────────────────────────────────────┐
│  Workflows（编排 + 业务逻辑）            │  ← 所有业务逻辑都在这里
│  - TASK_WORKFLOW                         │     RACI 规则、关键词提取、
│  - EMAIL_WORKFLOW                        │     事件记录、邮件撰写规范、
│  - STAKEHOLDER_WORKFLOW                  │     成就抽取、视图(status/owed/
│  - RECORDING_WORKFLOW                    │     waiting/before/...) 等
│  - VIEWS_WORKFLOW                        │
└──────────────┬───────────────────────────┘
               ↓ （仅在需要 I/O 时调用）
┌──────────────────────────────────────────┐
│  Skills（I/O — 外部系统）                │
│  - outlook-skill/  Outlook COM           │
│  - xlsx/           Excel 文件            │
│  - skill-creator/  元技能                │
└──────────────────────────────────────────┘
```

**核心原则**：业务逻辑全部用 markdown 写在 workflow 中，让 AI 直接读懂并执行。只有真正需要代码访问外部系统时才用 skill。两者都**按需加载**。

## 系统能力与限制

### 能做到的

| 能力 | 描述 |
|------|------|
| **状态持久化** | 基于文件的存储，跨会话保持记忆、日志和配置 |
| **交互式响应** | 用户触发后执行任务（请求-响应模式） |
| **模块化扩展** | 通过 `skills/` 添加新能力，无需修改核心代码 |
| **本地自治** | 所有数据留在本地；无需外部服务（除 AI IDE 本身） |
| **学习系统** | 从交互中学习并更新记忆文件 |
| **政策管理** | 结构化政策追踪带参考系统 |
| **定期任务** | 定期任务按计划自动触发 |
| **原生 Outlook** | 直接 Outlook COM 集成 — 无需云端、无需 API 密钥 |

### 不能做到的

| 限制 | 原因 |
|------|------|
| **自主执行** | 没有独立进程；需要用户在场 |
| **后台运行** | 没有守护进程；无法持续监控 |
| **远程接入** | 没有 API 端点；无法从 IM 或外部系统触发 |

### 系统本质

```
BrainClaw = 有状态请求-响应系统
         ≠ 持续运行系统
```

**核心约束：没有进程，只有对话。**

## 语言支持

- **系统文件**：英文（保持一致性）
- **命令**：英文 + 中文
- **用户内容**：任意语言

## 理念

> "AI 应该服务于每个人，而不仅仅是开发者。"

BrainClaw 弥合了强大 AI 工具与日常办公人员之间的鸿沟。通过使用 AI IDE 作为接口，我们绕过了传统障碍，同时保留了用户需要的能力。

## 通过 Skills 扩展

Skills 是存储在 `assistant_brain/skills/` 中的模块化能力。每个 skill 添加新功能而无需修改代码。使用 `skill-creator` skill 来构建你自己的 skill。

---

*坚信 AI 应该服务于每个人，而不仅仅是技术精英。*
