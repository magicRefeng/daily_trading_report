#!/bin/bash

# 自动提交脚本：晨报或晚报生成完成后执行git提交
# 使用方法：./auto_commit.sh [晨报|晚报]

# 获取当前日期
CURRENT_DATE=$(date +%Y%m%d)
CURRENT_DATE_CN=$(date +%Y年%m月%d日)

# 创建报告目录和日期文件夹（如果不存在）
mkdir -p report/$CURRENT_DATE

# 根据参数确定报告类型
if [ "$1" = "晨报" ]; then
    FILE_NAME="morning_report_${CURRENT_DATE}.md"
    COMMIT_MSG="添加${CURRENT_DATE_CN}A股晨报"
elif [ "$1" = "晚报" ]; then
    FILE_NAME="evening_report_${CURRENT_DATE}.md"
    COMMIT_MSG="添加${CURRENT_DATE_CN}A股晚报"
else
    echo "错误：请指定报告类型（晨报或晚报）"
    echo "使用方法：./auto_commit.sh [晨报|晚报]"
    exit 1
fi

# 检查文件是否存在
FILE_PATH="report/${CURRENT_DATE}/${FILE_NAME}"
if [ ! -f "$FILE_PATH" ]; then
    echo "错误：文件 $FILE_PATH 不存在"
    exit 1
fi

# 执行git提交
echo "正在提交 $FILE_PATH ..."
git add "$FILE_PATH"
git commit -m "$COMMIT_MSG"

# 如果是晚报，自动更新规则库和文档
if [ "$1" = "晚报" ]; then
    echo "检测到晚报提交，正在自动更新规则库和文档..."
    
    # 获取当前日期作为更新时间
    UPDATE_TIME=$(date "+%Y-%m-%d %H:%M")
    
    # ============ 更新规则库 ============
    NEW_RULES=$(grep -E "^###" "$FILE_PATH" | grep -v "无新规则" | grep -v "^###文档更新" | grep -v "^###AGENTS" | grep -v "^###README")
    
    if [ -n "$NEW_RULES" ]; then
        echo "" >> rules.md
        echo "---" >> rules.md
        echo "*更新于 ${UPDATE_TIME}，来源：${CURRENT_DATE_CN}晚报*" >> rules.md
        echo "" >> rules.md
        
        while IFS= read -r rule; do
            CATEGORY=$(echo "$rule" | sed -n 's/^###\([^ ]*\).*/\1/p')
            RULE_CONTENT=$(echo "$rule" | sed 's/^###[^ ]* //')
            
            case "$CATEGORY" in
                趋势分析)
                    sed -i '/^## 趋势分析规则$/,/^## /{
                        /^## /i\
                        - '"${RULE_CONTENT}"'
                    }' rules.md 2>/dev/null || true
                    ;;
                点位计算)
                    sed -i '/^## 点位计算规则$/,/^## /{
                        /^## /i\
                        - '"${RULE_CONTENT}"'
                    }' rules.md 2>/dev/null || true
                    ;;
                板块选择)
                    sed -i '/^## 板块选择规则$/,/^## /{
                        /^## /i\
                        - '"${RULE_CONTENT}"'
                    }' rules.md 2>/dev/null || true
                    ;;
                风险识别)
                    sed -i '/^## 风险识别规则$/,/^## /{
                        /^## /i\
                        - '"${RULE_CONTENT}"'
                    }' rules.md 2>/dev/null || true
                    ;;
                资金面分析)
                    sed -i '/^## 资金面分析规则$/,/^## /{
                        /^## /i\
                        - '"${RULE_CONTENT}"'
                    }' rules.md 2>/dev/null || true
                    ;;
            esac
            
            echo "  新增规则[$CATEGORY]: $RULE_CONTENT"
        done <<< "$NEW_RULES"
        
        sed -i "s/\*最后更新：.*/\*最后更新：${UPDATE_TIME}，来源：${CURRENT_DATE_CN}晚报\*/" rules.md
        echo "规则库更新完成"
    else
        echo "本次复盘无新规则"
    fi
    
    # ============ 自动更新AGENTS.md ============
    echo "检查AGENTS.md更新..."
    
    # 提取AGENTS.md更新内容
    AGENTS_UPDATE=$(sed -n '/### AGENTS.md更新/,/### README.md更新/p' "$FILE_PATH" | head -n -1 | tail -n +2)
    
    if [ -n "$AGENTS_UPDATE" ] && [ "$AGENTS_UPDATE" != "" ]; then
        echo "应用AGENTS.md更新..."
        
        # 提取新的晨报流程（如果存在）
        NEW_MORNING_FLOW=$(echo "$AGENTS_UPDATE" | sed -n '/晨报生成流程/,/^$/p' | sed '1d;$d')
        
        if [ -n "$NEW_MORNING_FLOW" ]; then
            # 备份原文件
            cp AGENTS.md AGENTS.md.bak
            
            # 替换晨报流程部分
            sed -i '/^### 晨报生成流程$/,/^### 晚报复盘格式/p' AGENTS.md.bak
            
            # 使用awk进行更复杂的替换
            awk -v new_flow="$NEW_MORNING_FLOW" '
                /^### 晨报生成流程/ { print; print "```"; print new_flow; print "```"; skip=1; next }
                /^### 晚报复盘格式/ { skip=0 }
                !skip { print }
            ' AGENTS.md.bak > AGENTS.md.new
            
            mv AGENTS.md.new AGENTS.md
            rm -f AGENTS.md.bak
            
            echo "AGENTS.md晨报流程已更新"
        fi
        
        # 提取新的晚报流程（如果存在）
        NEW_EVENING_FLOW=$(echo "$AGENTS_UPDATE" | sed -n '/晚报生成流程/,/^$/p' | sed '1d;$d')
        
        if [ -n "$NEW_EVENING_FLOW" ]; then
            cp AGENTS.md AGENTS.md.bak
            
            awk -v new_flow="$NEW_EVENING_FLOW" '
                /^### 晚报生成流程/ { print; print "```"; print new_flow; print "```"; skip=1; next }
                /^## 输出格式要求/ { skip=0 }
                !skip { print }
            ' AGENTS.md.bak > AGENTS.md.new
            
            mv AGENTS.md.new AGENTS.md
            rm -f AGENTS.md.bak
            
            echo "AGENTS.md晚报流程已更新"
        fi
    fi
    
    # ============ 自动更新README.md ============
    echo "检查README.md更新..."
    
    README_UPDATE=$(sed -n '/### README.md更新/,/### 无需更新/p' "$FILE_PATH" | head -n -1 | tail -n +2)
    
    if [ -n "$README_UPDATE" ] && [ "$README_UPDATE" != "" ]; then
        echo "应用README.md更新..."
        
        # 提取新的核心功能描述（如果存在）
        NEW_CORE_FUNC=$(echo "$README_UPDATE" | sed -n '/## 核心功能/,/^## /p' | head -n -1 | tail -n +2)
        
        if [ -n "$NEW_CORE_FUNC" ]; then
            cp README.md README.md.bak
            
            awk -v new_func="$NEW_CORE_FUNC" '
                /^## 核心功能/ { print; print new_func; skip=1; next }
                /^## 快速开始/ { skip=0 }
                !skip { print }
            ' README.md.bak > README.md.new
            
            mv README.md.new README.md
            rm -f README.md.bak
            
            echo "README.md核心功能已更新"
        fi
    fi
    
    # 提交所有更新
    git add rules.md AGENTS.md README.md 2>/dev/null
    git commit -m "自动更新文档：${CURRENT_DATE_CN}晚报复盘后" 2>/dev/null || echo "文档无变化，跳过提交"
fi

# 自动推送到远程仓库
echo "正在推送到 GitHub 远程仓库..."
git push origin main 2>&1
if [ $? -eq 0 ]; then
    echo "推送成功：已同步到 GitHub"
else
    echo "警告：推送失败，请检查网络或仓库权限"
fi

echo "提交完成：$COMMIT_MSG"