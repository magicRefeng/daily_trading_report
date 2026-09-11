# A股市场报告自动化系统

## 系统概述
本系统通过AI代理自动生成A股市场晨报和晚报，建立反馈闭环机制，持续提升分析质量。

## 文件结构
```
├── config/                     # 配置文件目录（敏感信息，不提交）
│   ├── feishu_config.env.example  # 飞书配置示例模板
│   └── feishu_config.env          # 飞书配置（实际使用，需自行创建）
├── prompt/                     # 提示词与任务指南
│   ├── morning_report_prompt.txt  # 晨报内容提示词
│   ├── evening_report_prompt.txt  # 晚报内容提示词（含复盘+波浪分析）
│   ├── morning_task_guide.md     # 晨报任务执行手册（完整流程）
│   └── evening_task_guide.md     # 晚报任务执行手册（完整流程）
├── script/                     # 脚本目录
│   ├── auto_commit.sh            # 自动提交脚本
│   └── feishu_api.py             # 飞书API工具脚本（自建应用直连）
├── AGENTS.md                   # AI代理使用指南
├── README.md                   # 项目说明文档
├── rules.md                    # 规则库（自动更新）
└── report/                     # 报告目录
    ├── YYYYMMDD/               # 近期日报（首页保留最近7个交易日）
    │   ├── morning_report_YYYYMMDD.md
    │   ├── evening_report_YYYYMMDD.md
    │   └── day_summary_YYYYMMDD.md   # 当日交易信息动态（日期节点内容）
    ├── monthly/                # 月度复盘总结（活跃月份）
    │   └── YYYYMM_monthly_report.md
    ├── yearly/                 # 年度复盘总结（当前年份）
    │   └── YYYY_yearly_report.md
    └── history/                # 历史归档
        └── YYYY/
            ├── YYYY_yearly_report.md      # 年度总结（历史版）
            └── M月/
                ├── YYYYMM_monthly_report.md  # 月度总结（历史版）
                └── YYYYMMDD/
                    ├── morning_report_YYYYMMDD.md
                    ├── evening_report_YYYYMMDD.md
                    └── day_summary_YYYYMMDD.md
```

### 归档规则
- **平时**：`report/` 下保留最近7个交易日的日期目录
- **当月第一个交易日**：上个月的所有日报全部归档到 `history/YYYY/MM/` 下，`report/` 下只保留当月
- **月度总结**：`monthly/` 和 `history/YYYY/MM/` 各存一份
- **年度总结**：`yearly/` 和 `history/YYYY/` 各存一份

## 核心功能

### 晨报（早上9点）
- 前日市场回顾与隔夜动态
- **今日核心判断**（趋势、点位、板块、资金面）
- **投资策略建议**（仓位、持仓结构、操作条件）

### 晚报（晚上8点）
- 当日市场回顾与热点分析
- **波浪理论多周期分析**（核心特色功能）
  - 月K、周K、日K、60分、30分五个周期波浪分析
  - Mermaid波浪结构示意图
  - 多周期共振判断与操作级别建议
  - 波浪目标位测算与演变路径推演
- **晨报复盘模块**（核心特色功能）
  - 核心判断回顾：逐项对比晨报预测与实际结果
  - 准确率量化评估：趋势、点位、板块准确率统计
  - 偏差根因分析：信息缺失/逻辑误判/情绪面误读等
  - 分析检查清单：沉淀为可复用的规则
  - 新规则发现：持续优化分析框架

### 反馈闭环机制
```
晨报预测 → 实际行情 → 晚报复盘 → 规则沉淀 → 优化晨报
```

### 规则库自动更新
晚报复盘后，系统会自动：
1. 从晚报中提取新规则（格式：`###类别 规则内容`）
2. 追加到 `rules.md` 对应章节
3. 自动提交规则库更新

### 飞书知识库同步
报告生成后自动同步到飞书知识库，目录结构：
```
首页
├── YYYY年M月月度总结            ← 当月月度总结（方便查看）
├── 近期日报（最近7个交易日）
│   └── YYYY年MM月DD日 交易信息动态   ← 内容来自 day_summary 文件
│       ├── A股晨报
│       └── A股晚报
└── 历史报告
    └── YYYY年                      ← 节点内容即年度总结
        └── YYYY年M月               ← 节点内容即月度总结
            └── YYYY年MM月DD日 交易信息动态
                ├── A股晨报
                └── A股晚报
```

- 日期父节点内容来自 `day_summary_YYYYMMDD.md`（晨报生成后写半成品，晚报生成后更新为完整版）
- 首页挂"当月月度总结"节点，方便快速查看
- 历史报告的年节点内容即年度总结，月节点内容即月度总结
- 超过7天的日报自动归档到历史报告的年/月目录下
- 当月第一个交易日：上个月日报全部归档

### 飞书消息通知
每次任务完成后，通过飞书私聊推送通知，包含核心数据摘要和报告链接。
通知由飞书自建应用机器人发送，需先在飞书中与机器人建立会话。

### 飞书 API 工具脚本
`script/feishu_api.py` 封装了飞书自建应用的常用 API 操作，使用时通过环境变量或配置文件读取凭证：
```bash
# 列出知识库节点
python3 script/feishu_api.py list-nodes --space-id $FEISHU_SPACE_ID --parent-node-token $FEISHU_HOME_NODE_TOKEN

# 创建节点
python3 script/feishu_api.py create-node --space-id $FEISHU_SPACE_ID --parent-node-token <父token> --title "标题"

# 移动节点
python3 script/feishu_api.py move-node --space-id $FEISHU_SPACE_ID --node-token <节点token> --target-parent-token <目标token>

# 更新文档内容（用Markdown文件全量替换）
python3 script/feishu_api.py update-doc --document-id <文档obj_token> --file <本地md文件路径>

# 发送消息
python3 script/feishu_api.py send-msg --open-id $FEISHU_USER_OPEN_ID --text "消息内容"
```

## 快速开始

### 1. 配置飞书信息

```bash
# 复制示例配置文件
cp config/feishu_config.env.example config/feishu_config.env

# 编辑配置，填入以下信息：
# - FEISHU_APP_ID：飞书自建应用 App ID
# - FEISHU_APP_SECRET：飞书自建应用 App Secret
# - FEISHU_SPACE_ID：知识库 space_id
# - FEISHU_HOME_NODE_TOKEN：首页节点 token
# - FEISHU_HISTORY_NODE_TOKEN：历史报告节点 token
# - FEISHU_USER_OPEN_ID：用户 open_id（自建应用下的，用于消息通知）
# - FEISHU_HOME_URL：知识库首页链接
# - GITHUB_TOKEN：GitHub Personal Access Token（用于代码拉取/推送）
```

> 注意：`config/feishu_config.env` 已加入 `.gitignore`，不会被提交到仓库，请勿将真实 token 泄露。
> 飞书自建应用需开启「机器人」能力并添加知识库读写、消息发送权限。

### 2. 生成晨报
```bash
# 使用AI代理读取提示词并生成晨报
# 读取 prompt/morning_report_prompt.txt
# 生成 report/YYYYMMDD/morning_report_YYYYMMDD.md
# 执行 ./script/auto_commit.sh 晨报
```

### 3. 生成晚报
```bash
# 使用AI代理读取提示词并生成晚报
# 读取 prompt/evening_report_prompt.txt
# 生成 report/YYYYMMDD/evening_report_YYYYMMDD.md
# 执行 ./script/auto_commit.sh 晚报
```

### 4. 自动提交
脚本会自动：
- 创建日期文件夹
- 检查文件是否存在
- 执行 git add 和 git commit
- 生成规范的提交信息

## 复盘维度说明

| 维度 | 晨报输出 | 晚报复盘 | 评估方式 |
|-----|---------|---------|---------|
| 趋势判断 | 看涨/看跌/震荡 | 实际涨跌 | 方向一致性 |
| 点位预测 | 具体支撑/压力位 | 实际高低点 | 误差百分比 |
| 板块预判 | 看涨/看跌板块 | 实际涨跌幅 | 方向准确性 |
| 资金面 | 北向资金预期 | 实际流向 | 金额误差 |
| 成交量 | 放量/缩量/平量 | 实际成交额 | 判断准确性 |
| 波浪分析 | 波浪位置参考 | 浪型验证与修正 | 浪型判断准确率 |

## 数据来源
- 官方数据：国家统计局、央行、交易所公告
- 权威媒体：新华社、央视财经、证券时报、中国证券报
- 数据平台：同花顺、东方财富、Wind资讯
- 研究机构：券商晨报、行业研究报告

## 注意事项
1. 确保已安装Git并配置好用户信息
2. 脚本需要执行权限：`chmod +x script/auto_commit.sh`
3. 文件命名必须符合规范，否则脚本无法识别
4. 提交信息会自动生成，无需手动编辑
5. 复盘结果会自动更新检查清单，用于持续优化分析质量
6. AI代理应严格按照提示词要求的格式输出，便于自动化处理