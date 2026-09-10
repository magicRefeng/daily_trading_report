# A股晨报任务执行指南

> 本文档为晨报定时任务的详细执行手册，由AI代理在任务启动时读取并严格执行。

## 任务目标
生成今日A股晨报，生成当日交易信息动态（晨报版），保存到本地并提交git推送到GitHub，同步到飞书知识库（按年/月层级归档），最后发送飞书消息通知。

## 工作目录
`/workspace`

## 飞书配置
从 `config/feishu_config.env` 读取以下配置：
- 首页节点 token：`FEISHU_HOME_NODE_TOKEN`
- 历史报告节点 token：`FEISHU_HISTORY_NODE_TOKEN`
- 知识库 space_id：`FEISHU_SPACE_ID`
- 用户 open_id：`FEISHU_USER_OPEN_ID`
- 知识库首页链接：`FEISHU_HOME_URL`

## 日期变量
- `DATE` = YYYYMMDD（今日，如 20260911）
- `DATE_CN` = YYYY年MM月DD日（今日，如 2026年09月11日）
- `MONTH` = YYYYMM（当月，如 202609）
- `MONTH_CN` = YYYY年M月（当月，如 2026年9月）
- `YEAR` = YYYY（当年，如 2026）
- `YEAR_CN` = YYYY年（当年，如 2026年）
- `PREV_DATE` = 上一个交易日的 YYYYMMDD（往前推算，跳过周末和节假日）

---

## 步骤1：前置检查

1. 获取当前北京时间，设置上述日期变量
2. 判断今日是否为交易日（周一至周五，节假日跳过）
3. 读取飞书配置文件：
   ```bash
   source /workspace/config/feishu_config.env
   ```
4. 计算上一个交易日日期 `PREV_DATE`（往前倒推，跳过周末）
5. 判断今日是否为当月第一个交易日：
   - 检查 `report/` 目录下是否存在当月日期的目录
   - 若不存在，则今日为当月第一个交易日
6. 创建目录（如不存在）：
   ```bash
   mkdir -p /workspace/report/$DATE
   mkdir -p /workspace/report/history
   ```

---

## 步骤2：读取文件

1. 读取 `/workspace/prompt/morning_report_prompt.txt` —— 晨报内容格式模板
2. 读取上一交易日的晚报（按日期查找，不遍历）：
   - 先查：`/workspace/report/$PREV_DATE/evening_report_$PREV_DATE.md`
   - 若不存在，查：`/workspace/report/history/${PREV_YEAR}/${PREV_MONTH}/$PREV_DATE/evening_report_$PREV_DATE.md`
   - 提取内容：
     - 复盘要点（准确率、偏差分析）
     - 波浪理论分析结论（当前波浪位置、关键点位）
     - 新发现的规则
3. 读取 `/workspace/rules.md` —— 了解现有规则库

---

## 步骤3：收集市场信息（WebSearch）

收集隔夜及今日早盘相关信息：

| 类别 | 具体内容 |
|-----|---------|
| 隔夜美股 | 道琼斯、标普500、纳斯达克涨跌幅、收盘点位 |
| 欧洲市场 | 英国富时100、德国DAX、法国CAC40表现 |
| 大宗商品 | 原油（WTI/布伦特）、黄金、铜的价格变动 |
| 汇率 | 美元指数、人民币汇率（离岸/在岸）、美债收益率 |
| 今日关注 | 重要经济数据发布、政策消息、公司公告 |
| 资金面 | 北向资金昨日流向、南向资金 |
| A股昨日 | 主要指数收盘点位、涨跌幅、成交额 |
| 波浪参考 | 隔夜外盘走势对波浪形态的可能影响 |

---

## 步骤4：生成晨报

严格按照 `morning_report_prompt.txt` 的格式生成，确保包含以下内容：

1. **昨日晚报复盘要点**
   - 昨日市场回顾
   - 复盘准确率总结
   - 波浪理论分析结论引用
   - 关键规则应用提示

2. **隔夜市场动态**
   - 美股三大指数表现
   - 欧洲、亚太市场
   - 大宗商品、汇率

3. **今日关注事项**
   - 重要数据发布
   - 政策事件
   - 新股申购、限售解禁

4. **板块与个股分析**
   - 今日重点关注板块
   - 潜在热点催化剂
   - 风险板块提示

5. **核心判断（必须结构化）**
   - 趋势判断（看涨/看跌/震荡）+ 预测区间 + 核心逻辑
   - 关键点位（强支撑、弱支撑、强压力、弱压力）
   - 板块预判（看涨、看跌、风险板块）
   - 资金面判断（北向资金预期、成交量预期）
   - 风险预警（高/中/低风险）
   - **波浪理论参考**：当前波浪位置、关键支撑/压力位的波浪验证

6. **投资策略建议**
   - 仓位建议（具体比例）
   - 持仓结构建议
   - 买卖条件与止损位
   - 操作策略（短线/中线）

7. **信息来源**
   - 列出主要数据来源，标注截止时间

---

## 步骤5：本地保存 + 生成当日交易信息动态（晨报版）+ Git 提交

1. 保存晨报为：`/workspace/report/$DATE/morning_report_$DATE.md`

2. 生成当日交易信息动态（晨报版半成品）：
   文件路径：`/workspace/report/$DATE/day_summary_$DATE.md`
   内容结构：
   ```markdown
   # $DATE_CN 交易信息动态

   ## 一、晨报精华
   ### 核心判断
   - 趋势：看涨/看跌/震荡，区间XXXX-XXXX点
   - 波浪参考：当前处于X浪X子浪，关注XXXX点

   ### 板块预判
   - 看涨：XXX、XXX
   - 看跌：XXX、XXX

   ### 策略建议
   - 仓位：XX%
   - 操作要点：XXX

   ### 风险提示
   - 高风险：XXX
   - 中风险：XXX

   ## 二、晚报精华
   （待晚间更新）

   ## 三、今日复盘与经验总结
   （待晚间更新）
   ```

3. 执行 git 提交推送：
   ```bash
   cd /workspace
   chmod +x script/auto_commit.sh
   ./script/auto_commit.sh 晨报
   ```

---

## 步骤6：同步到飞书知识库

### 6.1 处理日期父节点

1. 列出首页子节点（使用配置中的 space_id 和首页 node token）：
   ```bash
   lark-cli wiki +node-list --space-id $FEISHU_SPACE_ID --parent-node-token $FEISHU_HOME_NODE_TOKEN --page-all --as user --format json
   ```
2. 查找 `title == "$DATE_CN 交易信息动态"` 的节点
3. 存在则复用，不存在则创建到首页下

### 6.2 处理晨报子节点

1. 列出日期父节点的子节点
2. 查找 `title == "A股晨报"` 的子节点
3. 存在则复用，不存在则创建
4. 将晨报内容 overwrite 更新：
   ```bash
   lark-cli docs +update --doc <晨报obj_token> --command overwrite --doc-format markdown --content "@/workspace/report/$DATE/morning_report_$DATE.md" --as user --format json
   ```

### 6.3 更新日期父节点内容（从 day_summary 文件读取）

直接读取本地 `day_summary_$DATE.md` 文件，overwrite 更新到日期父节点：
```bash
lark-cli docs +update --doc <日期父obj_token> --command overwrite --doc-format markdown --content "@/workspace/report/$DATE/day_summary_$DATE.md" --as user --format json
```

---

## 步骤7：归档清理

### 归档规则
- **平时**：`report/` 下保留最近7个交易日的日期目录
- **当月第一个交易日**：上个月的所有日报全部归档到 `history/YYYY/MM/` 下，`report/` 下只剩今日

### 执行步骤

1. **如果今日是当月第一个交易日**：
   - 遍历 `report/` 下所有日期目录（排除 history、monthly、yearly）
   - 将所有上个月的日期目录移动到 `history/YYYY/MM/` 下
   - 飞书端：首页下上个月的所有日期节点，移动到历史报告 → 对应年节点 → 对应月节点下

2. **日常归档（保留7个交易日）**：
   - 列出 `report/` 下所有日期目录（排除 history、monthly、yearly）
   - 按日期从新到旧排序
   - 如果数量 > 7，超出部分（最旧的）逐个归档：
     1. 提取年月 YYYY MM
     2. 本地移动：`mkdir -p /workspace/report/history/YYYY/MM && mv /workspace/report/$OLD_DATE /workspace/report/history/YYYY/MM/`
     3. 飞书移动：
        ```bash
        lark-cli wiki +move --node-token <旧日期node_token> --target-parent-token <对应月node_token> --as user --format json
        ```
     4. 确保历史报告下有对应年节点和月节点（不存在则创建）

---

## 步骤8：发送飞书消息通知

发送私聊消息，内容简洁（200字以内）：
```
📈 A股晨报已生成（$DATE_CN）

【趋势】看涨/看跌/震荡，区间XXXX-XXXX点
【波浪】当前处于X浪X子浪，关注XXXX点支撑/压力
【板块】看涨：XXX、XXX；看跌：XXX、XXX
【策略】仓位XX%，XXX操作

晨报全文：https://my.feishu.cn/wiki/<晨报node_token>
知识库首页：$FEISHU_HOME_URL
GitHub仓库：https://github.com/magicRefeng/daily_trading_report
```

发送命令：
```bash
lark-cli im +messages-send --user-id $FEISHU_USER_OPEN_ID --as user --markdown $'消息内容'
```

---

## 任务完成

给用户简要摘要：
- 核心判断（3-5句话）
- 策略建议（3-5句话）
- 波浪分析参考（3-5句话）
- 附飞书文档链接
