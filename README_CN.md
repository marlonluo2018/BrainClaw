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
3. 使用 [`assistant_brain/prompts/SYSTEM_PROMPT.md`](assistant_brain/prompts/SYSTEM_PROMPT.md) 作为唯一系统提示词；`AGENTS.md` 和 `CLAUDE.md` 是为不同工具生成的兼容副本
4. 将工作区设置为 BrainClaw 文件夹

### 可重复开发环境（可选）

核心运行时仅使用 Python 标准库。如需运行测试和静态检查：

```powershell
py -3 -m pip install -r requirements-dev.txt
py -3 assistant_brain/scripts/doctor.py
```

`pyproject.toml` 中还定义了 `documents` 和 `outlook` 可选依赖。

> **隐私：** 真实 `assistant_brain/contacts.md` 仅供本地使用；新环境请从 `assistant_brain/contacts.example.md` 复制创建。如果旧版本中该文件已经被 Git 追踪，仅添加 `.gitignore` 不会把它从索引或历史中删除；这需要单独执行隐私迁移。

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
│  │  系统提示词  (prompts/SYSTEM_PROMPT.md)              │  │
│  │  "启动时，读取 brain 文件..."                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                        ↓                                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Brain 文件 (assistant_brain/)                        │  │
│  │  ├── workflows/            (编排 + 业务逻辑)           │  │
│  │  │   ├── TASK_WORKFLOW.md                              │  │
│  │  │   ├── EMAIL_WORKFLOW.md                             │  │
│  │  │   ├── PROCESS_WORKFLOW.md                           │  │
│  │  │   ├── REDHAT_WORKFLOW.md                            │  │
│  │  │   └── VIEWS_WORKFLOW.md                             │  │
│  │  ├── skills/               (I/O — 外部系统)            │  │
│  │  │   ├── outlook_com_skill/    (Outlook COM 后端)      │  │
│  │  │   ├── xlsx-ibm/            (Excel 读写)              │  │
│  │  │   ├── bluepage-skill/   (W3 统一 Profile)           │  │
│  │  │   ├── enrollment-downloader/ (报名名册下载)          │  │
│  │  │   └── skill-creator/    (新技能脚手架)              │  │
│  │  ├── tasks/                (任务队列)                  │  │
│  │  └── process/              (操作流程)                  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## 功能概览

| 功能 | 描述 |
|------|------|
| **任务管理** | 详细任务追踪，包含状态、优先级、分类、地理位置、截止时间、RACI 利益相关方、父子关系、结构化 `Asks`（我欠的 / 别人欠我的）|
| **任务优先规则** | 当被询问任何任务的状态、排期或进度时，系统**总是**首先检查任务文件（单一可信源），然后再检索邮件或外部资源。 |
| **视图引擎** | `status T###`（或直接 `T###`）/ `待我处理` / `等待` / `before {人}` / `digest` / `timesheet` —— 跨任务揭示逾期、欠回复、待办事项、周报和工时 |
| **邮件管理** | 通过原生 Outlook COM 查找、搜索、线程追踪和撰写邮件。同步管道先生成结构化证据包，再由单一语义分类器判断邮件与任务的归属，随后通过 Schema、快照时效与跨记录校验进行原子应用；确定性代码不再用置信度阈值替模型做决定，未匹配邮件也不会被自动忽略。 |
| **精简四步邮件流** | 邮件发送/回复的强制流：1. 获取线程/上下文 → 2. 通过 `get-email` 完整读取历史邮件（零猜测、无假定）→ 3. 撰写草稿（To/CC、Subject、纯文本正文；“无冗余原则”防止重复已有参数事实）→ 4. **仅**在当前轮次获得显式授权批复后执行发送。 |
| **邮件线程追踪** | ConversationID 提供强线程连续性证据；同线程新邮件仍由语义分类器结合完整任务范围作最终判断。 |
| **关联邮件发现** | 多策略搜索（线程 + 发件人 + 关键词）实现跨线程发现 |
| **报名名册与短名单** | 基于 Playwright 自动下载 YourLearning 课程报名名册。评估注册情况、自动交叉比对人员 headcount 数据库、排除历史重复/非正式/非特定 geo 员工、按照职级和岗位打分，并向 Excel 导出高亮显色、清晰明了的学员入选（绿色）与备份名单（黄色），方便与 LDM 分享。 |
| **Blue Pages 员工查询** | 通过 IBM W3 Unified Profile/Blue Pages API 快速查询 CNUM、员工类型、上下级汇报关系（经理和下属）、Slack 账号和 HR 在职状态。 |
| **流程智能** | 自动匹配任务到流程模板，建议下一步行动+联系人。Email sync 时检测未记录的流程步骤，重复模式自动固化为流程文件 |
| **催办自动化** | 检测超期任务，自动起草语气适配的催办邮件，追踪催办历史 |
| **网页搜索与浏览** | 通过 Tavily MCP 搜索网页、提取页面内容、爬取站点、深度调研 |
| **周报生成** | 自动生成过去一周的任务活动、完成情况、关键事件摘要 |
| **工时生成** | 按 Geo → Category 分组进行自上而下工时分配，含 EPD 编号 |
| **定期任务** | 自动创建定期任务（月度报告、季度流程） |
| **Office 文档** | 通过 `xlsx-ibm` skill 创建/读取/编辑/分析 Excel 文件 |
| **可扩展技能** | 通过模块化技能系统添加新能力 |

## 技能

技能仅用于与外部系统交互（I/O）。它们是挂载在 `assistant_brain/skills/` 下的独立仓库，本仓库不追踪其内容。业务逻辑仍直接写在 workflow 文件中。

| 技能 | 用途 | 外部系统 |
|------|------|----------|
| **outlook_com_skill** | 查找、线程、关联、撰写、回复、全部回复、转发、重定向、批量转发 | Microsoft Outlook (COM) |
| **xlsx-ibm** | 创建、读取、编辑、分析 Excel/电子表格文件 | `.xlsx`、`.xlsm`、`.csv` |
| **bluepage-skill** | 查询 IBM 员工 Profile、Slack ID、汇报关系、在职状态 | IBM Blue Pages (W3 Unified Profile API) |
| **enrollment-downloader** | 基于 Playwright 自动下载和评估 YourLearning 班级报名名册 | IBM YourLearning / E&C Manager |
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
| `compose` / `reply` / `forward` / `redirect` | — | 发送邮件（发送后自动输出 EntryID） |

**策略：** 已发送邮件在任务文件中追踪（`## Email References`）。`find` 和 `find-recent` 默认仅搜索收件箱。线程和关联搜索自动包含已发送邮件以确保完整性。

**EntryID 追踪：** 所有发送命令（`compose`、`reply`、`forward`、`redirect`）发送后自动输出邮件的 `EntryID`。用于在任务 Timeline 中添加 `<!-- email:ID -->` 标记，实现可靠的邮件追溯。追踪遵循统一的**关键邮件标准**（收发一致）：包含请求/审批/决策/承诺的邮件、交付/请求交付物的邮件、任务里程碑邮件、或可能需要后续回复/转发的邮件。纯 FYI 确认（"noted"、"thanks"、"got it"）豁免。

**邮件到任务分类（模型中心）：**

1. **确定性证据准备** — 构建活动任务目录，收集 EntryID、ConversationID、业务标识符、联系人、词汇和范围证据。
2. **语义归属判断** — 单一分类器审查所有非噪音邮件，包括日历项和没有候选任务的邮件，并完整读取所有可能相关的任务文件。
3. **校验后写入** — 分类器生成符合 Schema 且包含显式匹配元数据复核的计划；确定性程序校验快照与跨记录约束，并原子写入时间线、Asks、字段、标签、联系人、RACI、备注和忽略池。

不再使用人为置信度分数或确定性归属阈值。候选原因只是显式证据，不是结论。同一封邮件在内容确实涉及多个独立任务事件时，可以更新多个任务；唯一性按 `(task, entry_id)` 校验。每次任务更新都会复核 Scope、Exclude、Tags、Contacts/RACI 和稳定标识符，避免新证据只留在 Timeline 文字里。活动任务结构由 `validate_tasks.py` 按 `task_file.schema.json` 校验。`latest-candidates.json` 是分类器的权威输入，`latest.md` 仅用于人工诊断。发件主题应使用可识别的公开标识符，但绝不能包含 EPD 编号或 Class ID。详见 [ARCHITECTURE.md 第 4.5 节](ARCHITECTURE.md)。

## 项目结构

标记 ⭐ 的文件在**启动时加载**。其他文件**按需加载**。

```
BrainClaw/
├── AGENTS.md                     # 生成的兼容提示词副本
├── CLAUDE.md                     # 生成的兼容提示词副本
├── README.md                     # 英文说明
├── README_CN.md                  # 中文说明（本文件）
├── ARCHITECTURE.md               # 系统架构
└── assistant_brain/
    ├── prompts/
    │   └── SYSTEM_PROMPT.md      # 唯一系统提示词
    ├── views_config.md       ⭐  # 视图阈值与默认值
    ├── recurring_tasks.md    ⭐  # 定期任务定义
    ├── contacts.md           ⭐  # 本地隐私联系人数据
    ├── contacts.example.md       # 可安全提交的脱敏模板
    ├── formats/
    │   ├── EMAIL_SYNC_FORMAT.md          # 邮件同步排版规范
    │   ├── email_sync_candidates.schema.json
    │   ├── email_sync_plan.schema.json
    │   └── task_file.schema.json         # 活动任务契约
    ├── process/
    │   ├── README.md         ⭐  # 本地流程索引
    │   └── process.schema.json   # 版本化流程 Schema
    ├── workflows/                # 编排与业务逻辑
    ├── scripts/                  # 白名单运行时/质量工具；任务脚本默认仅本地保存
    ├── skills/                   # 独立仓库；主仓库不追踪
    └── tasks/                    # 本地隐私任务文件与历史
```

### 启动时加载的文件 (⭐)

启动时运行 `py -3 assistant_brain/scripts/dashboard.py`，输出面板信息。以下文件在启动时加载：

| 文件 | 用途 |
|------|------|
| `views_config.md` | 视图命令的阈值与默认值 |
| `tasks/T*.md` + `tasks/history/` | 活跃及归档任务元数据；近期事件由 `dashboard.py` 动态生成 |
| `recurring_tasks.md` | 定期任务定义 |
| `contacts.md` | 联系人数据库（含流程角色速查表）|
| `process/README.md` | 流程索引 |
| `skills/*/SKILL.md` frontmatter | 技能触发词与描述 |

其他所有文件（工作流文件、技能实现等）在需要特定操作时**按需加载**。

## 命令

> 直接用日常说法即可 —— 下面是例子,不是死板的命令。 AI 按意图匹配,不要求精确关键词。

| 想干啥 | 你可以这样说 | 系统怎么响应 |
|--------|------------|------------|
| **启动助理** | "start"、"启动"、"start assistant" | 加载 brain 文件,渲染按国家 → 优先级分组的完整任务列表,标记 overdue |
| **只想打招呼** | "hi"、"你好"、"help me"、"帮我" | 仅快速问候 — 模糊用语不会自动启动 |
| **某个任务啥状态** | "T033"、"T033 状态"、"查 T033"、"T033 怎么样了"、"看下 T033"、"status T033" | 一屏:当前卡点、欠的、近期决策 |
| **我欠谁啥** | "待我处理"、"我欠谁啥"、"我答应过啥"、"我有啥没回的"、"owed" | 跨任务汇总我的承诺,按对方分组,逾期优先 |
| **谁卡着我 / 谁没回** | "等待"、"我在等谁"、"啥事卡着"、"谁还没回我"、"waiting" | 跨任务汇总,按对方分组,按等待时长排序 |
| **会前预备** | "见 Beng 之前"、"明天 and Mridul 开会前"、"下午要见 X"、"before Beng" | 拉所有该人相关任务 + 议程草稿 |
| **员工/部门查询** | "who is Beng"、"bluepages HONG YANG"、"reports to X" | 通过 Blue Pages 查询 Profile 详情、Slack、汇报关系和组织结构 |
| **班级名册/评估** | "download roster T134"、"check enrollment 10580795"、"evaluate roster" | 连接浏览器自动下载名册、交叉比对人员信息并输出带高亮显色的短名单 Excel |
| **看完整任务清单** | "全部任务"、"完整队列"、"show all" | 重新渲染启动同款分组任务列表 |
| **任务操作** | "新建任务"、"完成 T033"、"block T040"、"create/update/complete/block task" | 任务生命周期 |
| **流程推进** | "next step T033"、"推进 T033"、"下一步"、"固化流程" | 匹配流程模板，建议下一步行动+联系人；固化重复模式 |
| **催办 / 追踪** | "follow up"、"催办"、"chase"、"nudge T033"、"提醒一下" | 检测超期任务，起草语气适配的催办邮件 |
| **邮件操作** | "查邮件"、"找 Beng 的邮件"、"draft email"、"reply"、"forward" | 邮件生命周期(现在自动抽取写入任务) |
| **网页搜索** | "search DO188"、"搜索"、"查一下"、"look up"、"查看网页" | 通过 Tavily 搜索或提取网页内容 |
| **周报** | "digest"、"周报"、"weekly summary"、"this week" | 自动生成过去7天的任务活动摘要 |
| **工时** | "timesheet"、"工时"、"time allocation" | 按 Geo → Category 分组的工时分配表 |

## 任务管理特性

BrainClaw 提供企业级任务追踪：

- **丰富任务卡片**：状态、优先级、分类、地理位置（地理追踪）、截止时间、联系人、关键字、历史、备注
- **智能检测**：自动从上下文判断截止时间和优先级
- **智能关键字**：2-3个唯一标识符（请求ID、完整姓名、特定代码）便于追溯来源
- **历史追踪**：累加记录所有任务更新，包含时间戳 and 来源
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

## 架构：工作流与技能

BrainClaw 采用分层架构，更好地组织代码：

```
assistant_brain/prompts/SYSTEM_PROMPT.md (唯一系统提示词)
        ↓ 生成兼容副本：AGENTS.md + CLAUDE.md
        ↓
┌──────────────────────────────────────────┐
│  Workflows（编排 + 业务逻辑）            │  ← 所有业务逻辑都在这里
│  - TASK_WORKFLOW                         │     流程匹配、自动推进、
│  - EMAIL_WORKFLOW                        │     关键词提取、邮件撰写、
│  - PROCESS_WORKFLOW                      │     流程学习与固化、催办自动化、
│  - REDHAT_WORKFLOW                       │     网页搜索、周报与工时生成、
│  - VIEWS_WORKFLOW                        │     视图、Red Hat 受众与短名单筛选
└──────────────┬───────────────────────────┘
               ↓ （仅在需要 I/O 时调用）
┌──────────────────────────────────────────┐
│  Skills（I/O — 外部系统）                │
│  - outlook_com_skill/  Outlook COM       │
│  - xlsx-ibm/   Excel 文件            │
│  - bluepage-skill/  W3 Profile API       │
│  - enrollment-downloader/  YourLearning  │
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
| **网页搜索与浏览** | 通过 Tavily MCP 搜索网页、提取页面、深度调研 |
| **本地自治** | 所有数据留在本地；无需外部服务（除 AI IDE + Tavily API） |
| **学习系统** | 从交互中学习并更新记忆文件 |
| **流程智能** | 自动匹配流程模板、推进建议、未记录步骤检测、模式固化 |
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

Skills 是挂载在 `assistant_brain/skills/` 下的独立仓库。每个 skill 可以独立版本控制，BrainClaw 主仓库通过 `SKILL.md` 按需加载。

---

*坚信 AI 应该服务于每个人，而不仅仅是技术精英。*
