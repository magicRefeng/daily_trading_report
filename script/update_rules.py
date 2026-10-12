#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新 rules.md 规则库。

从标准输入读取新规则（每行格式：`###类别 规则内容`），按类别插入到 rules.md
对应章节的末尾，并对全文已有规则去重。最后更新"最后更新"时间行。

用法：
    echo "$NEW_RULES" | python3 script/update_rules.py "2026-10-12 12:31" "2026年10月12日晚报"
"""

import sys
import re

CATS = ["趋势分析", "点位计算", "板块选择", "风险识别", "资金面分析", "波浪分析"]
HEAD_RE = re.compile(r'^##\s+(' + '|'.join(CATS) + r')规则\s*$')
RULE_RE = re.compile(r'^\s*-\s+(.*\S)\s*$')
SHOP_RE = re.compile(r'^###(' + '|'.join(CATS) + r')\s+(.*\S)\s*$')


def main():
    update_time = sys.argv[1] if len(sys.argv) > 1 else ""
    source = sys.argv[2] if len(sys.argv) > 2 else "晚报"

    # 读取新规则（按类别分组，保持顺序）
    new_rules = {c: [] for c in CATS}
    for line in sys.stdin:
        m = SHOP_RE.match(line.rstrip('\n'))
        if m:
            new_rules[m.group(1)].append(m.group(2))

    path = "rules.md"
    with open(path, encoding='utf-8') as f:
        lines = f.read().split('\n')

    # 已有规则集合（用于去重）
    existing = set()
    for ln in lines:
        m = RULE_RE.match(ln)
        if m:
            existing.add(m.group(1))

    # 各章节标题所在行号
    head_idx = {}
    for i, ln in enumerate(lines):
        m = HEAD_RE.match(ln)
        if m:
            head_idx[m.group(1)] = i

    added = 0
    for cat in CATS:
        todo = [r for r in new_rules[cat] if r not in existing]
        if not todo:
            continue
        if cat not in head_idx:
            print("警告：rules.md 中缺少『%s规则』章节，跳过" % cat, file=sys.stderr)
            continue
        start = head_idx[cat]
        # 章节末尾 = 标题之后第一条非规则行（下一个标题 / 空行 / 分隔线）
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if not RULE_RE.match(lines[j]):
                end = j
                break
        lines[end:end] = ["- " + r for r in todo]
        existing.update(todo)
        added += len(todo)
        # 同步更新该标题之后新增行导致的后续标题行号偏移
        for c in CATS:
            if c in head_idx and head_idx[c] >= end:
                head_idx[c] += len(todo)
        for r in todo:
            print("  新增规则[%s]: %s" % (cat, r))

    # 更新"最后更新"行（仅保留一条，其余历史"更新于"标记不再追加）
    if update_time:
        stamp = "*最后更新：%s，来源：%s*" % (update_time, source)
        done = False
        for i, ln in enumerate(lines):
            if ln.startswith("*最后更新"):
                lines[i] = stamp
                done = True
        if not done:
            lines += ["", "---", "", stamp, ""]

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    if added == 0:
        print("本次复盘无新规则（均已存在）")
    else:
        print("规则库更新完成，共新增 %d 条" % added)


if __name__ == '__main__':
    main()