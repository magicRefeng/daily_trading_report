# A股运行规律分析任务执行指南

> 本文档为运行规律分析任务的详细执行手册，由AI代理在任务启动时读取并严格执行。

## 任务目标
基于A股本周及历史数据，运用波浪理论、均线系统、量价关系、关键技术指标等方法，发现市场运行规律并预测下周走势。分析结果保存到本地、提交GitHub、同步飞书知识库、发送消息通知。晚报任务读取本分析结论作为参考。

## 工作目录
`/workspace/daily_trading_report`

## 代码仓库
- GitHub 仓库地址：`https://github.com/magicRefeng/daily_trading_report.git`
- GitHub Token：从环境变量 `GITHUB_TOKEN` 读取

## 飞书配置
优先从系统环境变量读取，本地开发环境可从 `config/feishu_config.env` 读取：
- 应用凭证：`FEISHU_APP_ID`、`FEISHU_APP_SECRET`
- 首页节点 token：`FEISHU_HOME_NODE_TOKEN`
- 历史报告节点 token：`FEISHU_HISTORY_NODE_TOKEN`
- 知识库 space_id：`FEISHU_SPACE_ID`
- 用户 open_id：`FEISHU_USER_OPEN_ID`
- 知识库首页链接：`FEISHU_HOME_URL`

## 飞书 API 工具
所有飞书操作通过 `script/feishu_api.py` 脚本完成，使用方法：
```bash
# 列出节点
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

> 注意：知识库节点的 `node_token` 和文档本身的 `obj_token` 是两个不同的 token。
> - 创建节点返回的 node 里同时有 `node_token` 和 `obj_token`
> - 更新文档内容用 `obj_token`
> - 移动节点、列节点用 `node_token`

## 日期变量
- `WEEK` = YYYYWW（本周，如 202637 表示2026年第37周）
- `WEEK_CN` = YYYY年第WW周（如 2026年第37周）
- `DATE` = YYYYMMDD（今日，如 20260913）
- `DATE_CN` = YYYY年MM月DD日（今日，如 2026年09月13日）
- `YEAR` = YYYY（当年，如 2026）
- `YEAR_CN` = YYYY年（当年，如 2026年）

---

## 步骤0：拉取代码仓库

定时任务在空沙盒中运行，必须先从 GitHub 拉取代码。

1. 切换到工作目录父级：
   ```bash
   cd /workspace
   ```
2. 如果仓库目录不存在，clone 仓库：
   ```bash
   git clone https://$GITHUB_TOKEN@github.com/magicRefeng/daily_trading_report.git
   ```
3. 进入仓库目录并拉取最新代码：
   ```bash
   cd /workspace/daily_trading_report
   git pull
   ```
4. 设置工作目录为仓库目录，后续所有操作均在此目录下执行

---

## 步骤1：前置检查

1. 获取当前北京时间，设置上述日期变量
2. 计算本周数（ISO周数）：`date +"%%V"` 获取当前ISO周数，拼接年份
3. 加载飞书配置：
   - 优先检查系统环境变量是否已设置 `FEISHU_APP_ID`
   - 若环境变量不存在，从本地配置文件读取：
     ```bash
     [ -f config/feishu_config.env ] && source config/feishu_config.env
     ```
4. 创建目录（如不存在）：
   ```bash
   mkdir -p analysis
   ```

---

## 步骤2：读取文件

1. 读取 `prompt/pattern_analysis_prompt.txt` —— 规律分析内容格式模板
2. 读取 `rules.md` —— 了解现有规则库（含波浪分析规则和历史发现规律）
3. 读取上一期规律分析（如果文件存在）：
   - 查找 `analysis/` 目录下最新的 `pattern_analysis_*.md` 文件
   - 提取上期的"下周走势预测"和"运行规律发现"内容，用于验证和对比
4. 读取本周所有日报（如存在）：
   - 遍历 `report/` 下本周日期对应的目录
   - 读取每天的 `day_summary_*.md`，收集本周市场表现数据

---

## 步骤3：收集市场数据（WebSearch）

| 类别 | 具体内容 |
|-----|---------|
| 周度指数数据 | 上证指数、深证成指、创业板指本周涨跌幅、收盘点位、周最高/最低点 |
| 月K线数据 | 上证指数月K线近期走势、月度均线（5月/10月/20月）、月度MACD/KDJ |
| 周K线数据 | 上证指数周K线近期走势、周度均线（5周/10周/20周/60周）、周度MACD信号 |
| 日K线数据 | 近5个交易日K线组合形态、日度均线（5日/10日/20日/60日）排列 |
| 短周期数据 | 60分钟/30分钟K线形态、短周期量价背离信号 |
| 关键点位 | 近期高低点（5日/20日/60日）、整数关口、前期高低点 |
| 成交量数据 | 两市日均成交额、周度成交量变化趋势 |
| 资金数据 | 北向资金周度净流入/流出、主力资金周度流向 |
| 历史相似形态 | 当前形态与历史上相似时期（如相同波浪位置、均线排列）的比对数据 |
| 市场情绪 | 周度涨跌家数比、涨停板统计、市场宽度指标 |

---

## 步骤4：生成运行规律分析报告

严格按照 `pattern_analysis_prompt.txt` 格式生成，确保以下章节完整：

### 4.1 本周市场回顾
- 主要指数周度表现（表格展示）
- 周成交量能变化
- 市场情绪指标

### 4.2 多周期K线规律分析（核心章节）

**月K线规律：**
- 当前月K线形态描述
- 历史相似月线形态比对（至少找2-3个历史案例）
- 月度均线系统多空排列
- 月度MACD/KDJ指标背离分析
- 月度关键支撑位和压力位

**周K线规律：**
- 当前周K线形态描述
- 历史相似周线形态比对
- 周度均线系统排列（5周/10周/20周/60周）
- 周度MACD金叉/死叉信号
- 周度关键点位

**日K线规律：**
- 近5日K线组合形态及含义
- 日度均线系统排列及粘合/发散状态
- 量价配合情况分析
- 跳空缺口统计

**60分钟/30分钟K线规律：**
- 短周期形态及趋势线
- 量价背离信号
- 关键转折点信号

### 4.3 关键点位分析
- 上证指数：支撑位（整数关口、前期低点、均线支撑、黄金分割）和压力位
- 创业板指：同上分析
- 下周运行区间预测

### 4.4 历史相似形态比对
- 当前形态与历史相似时期的比对
- 历史相似形态后的走势统计（上涨概率、平均涨幅、持续时间）
- 本次与历史的差异点

### 4.5 运行规律发现
- 本周新发现的规律
- 历史规律验证情况
- 规律的适用条件和失效条件

### 4.6 下周走势预测
- 趋势判断：明确看涨/看跌/震荡
- 预测区间：具体点位
- 关键时间窗口
- 概率分析：上涨/震荡/下跌概率

### 4.7 策略建议
- 仓位建议
- 板块轮动预判
- 风险控制要点

### 4.8 规律发现输出（格式固定）
```
###趋势分析 规则内容
###点位计算 规则内容
###波浪分析 规则内容
```
如无新规律，输出：`###无新规则`

---

## 步骤5：保存报告 + Git 提交

1. 保存报告为：`analysis/pattern_analysis_$WEEK.md`

2. 执行 git 提交推送：
   ```bash
   chmod +x script/auto_commit.sh
   ./script/auto_commit.sh 规律分析
   git push https://$GITHUB_TOKEN@github.com/magicRefeng/daily_trading_report.git HEAD:main
   ```

---

## 步骤6：同步到飞书知识库

### 6.1 处理规律分析节点

1. 列出首页子节点：
   ```bash
   python3 script/feishu_api.py list-nodes --space-id $FEISHU_SPACE_ID --parent-node-token $FEISHU_HOME_NODE_TOKEN
   ```
2. 查找 `title == "规律分析"` 的节点
3. 存在则复用，不存在则创建到首页下：
   ```bash
   python3 script/feishu_api.py create-node --space-id $FEISHU_SPACE_ID --parent-node-token $FEISHU_HOME_NODE_TOKEN --title "规律分析"
   ```

### 6.2 处理本周分析子节点

1. 列出"规律分析"节点的子节点
2. 查找 `title == "$WEEK_CN 运行规律分析"` 的子节点
3. 存在则复用，不存在则创建
4. 全量更新内容：
   ```bash
   python3 script/feishu_api.py update-doc --document-id <分析报告obj_token> --file "analysis/pattern_analysis_$WEEK.md"
   ```

---

## 步骤7：发送飞书消息通知

发送私聊消息，内容简洁（200字以内）：
```
📊 A股运行规律分析已生成（$WEEK_CN）

【趋势】下周看涨/看跌/震荡
【区间】上证指数 XXXX-XXXX点
【关键】关键支撑XXXX，关键压力XXXX
【规律】本周新发现X条规律
【概率】上涨XX% 震荡XX% 下跌XX%

分析全文：https://my.feishu.cn/wiki/<分析报告node_token>
知识库首页：$FEISHU_HOME_URL
```

发送命令：
```bash
python3 script/feishu_api.py send-msg --open-id $FEISHU_USER_OPEN_ID --text '消息内容'
```

---

## 步骤8：更新规则库

如果本次分析发现了新规律，更新 `rules.md`：
1. 在对应类别下添加新规则
2. 标注发现日期和适用条件
3. Git 提交规则库更新

---

## 任务完成

给用户简要摘要：
- 本周市场回顾要点（2-3句话）
- 多周期规律发现（3-5句话）
- 下周预测核心结论（2-3句话）
- 关键规律发现（2-3句话）
- 附飞书文档链接
