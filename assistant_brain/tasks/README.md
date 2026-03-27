# Tasks Directory

任务管理系统文档

---

## 目录结构

```
tasks/
├── README.md              # 本文档
├── queue.md               # 活跃任务队列（概览表格）
├── T001-xxx.md            # 活跃任务详情
├── T002-xxx.md
├── ...
└── history/               # 已完成任务归档
    ├── T007-xxx.md
    └── ...
```

---

## 命名规范

### 任务文件命名

```
T{编号}-{关键字1}-{关键字2}-{关键字3}.md
```

| 部分 | 说明 | 示例 |
|------|------|------|
| `T{编号}` | 任务编号，3位数字，递增 | T001, T002, T003 |
| `{关键字}` | 2-4个关键字，用 `-` 连接 | rhcsa-voucher-sukriti |

### 命名原则

1. **简洁** - 关键字控制在 2-4 个词
2. **可读** - 不打开文件就能知道内容
3. **可搜索** - 包含项目名、人员名等关键信息
4. **可排序** - 编号自动按创建时间排序

### 示例

```
✅ T001-rhcsa-voucher-sukriti.md     # 清晰：项目+事项+人员
✅ T002-q1-achievements.md            # 简洁：事项+类型
✅ T003-redhat-training-seats.md      # 项目+事项

❌ T001.md                           # 缺少关键字，不便识别
❌ T001_process_rhcsa_voucher.md     # 使用下划线，不统一
❌ T001-rhcsa-voucher-for-sukriti.md # 过长，冗余词
```

---

## 状态系统

### 状态标识

| 符号 | 状态 | 说明 |
|------|------|------|
| `📋` | Not Started | 待处理 / 需要行动 |
| `⏳` | In Progress | 进行中 / 等待信息 |
| `✅` | Completed | 已完成 → 移至 history/ |

### 状态流转

```
📋 Not Started → ⏳ In Progress → ✅ Completed → history/
```

---

## 优先级系统

| 级别 | 含义 | 触发条件 |
|------|------|----------|
| P1 | High | 紧急 / 截止日期临近 |
| P2 | Medium | 常规任务 |
| P3 | Low | 可延后处理 |

---

## 工作流程

### 新建任务

1. 查看 queue.md 获取下一个编号
2. 创建文件 `T{编号}-{关键字}.md`
3. 在 queue.md 添加表格条目
4. 填写任务详情模板

### 完成任务

1. 更新任务文件状态为 `✅`
2. 移动文件至 `history/`
3. 从 queue.md 移除条目
4. 在历史文件底部添加 `## Completion` 章节

---

## 任务模板

```markdown
# T{编号}: {任务标题}

**Status:** 📋 Not Started  
**Created:** {YYYY-MM-DD}  
**Priority:** P{1-3}  
**Category:** {Email/Slack/Meeting/Other}  
**Due:** {日期或TBD}

---

## Contacts
- **Requester:** 姓名 (邮箱)
- **Approver:** 姓名 (邮箱)

## Tags
`标签1`, `标签2`, `标签3`

---

## Timeline

|| Date | Source | Action |
||------|--------|--------|
|| {日期} | {来源} | {动作描述} |

---

## Current State
- [ ] 待办事项1
- [ ] 待办事项2

## Notes
备注信息
```

---

## 归档规则

- 已完成任务移至 `history/` 目录
- 编号保持不变（T007 永远是 T007）
- 可按编号追溯完整历史
