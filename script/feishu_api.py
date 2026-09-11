#!/usr/bin/env python3
"""
飞书 API 工具脚本
封装飞书知识库、文档、消息等常用 API 操作。
配置从环境变量读取，也支持从 config/feishu_config.env 读取。
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error

FEISHU_BASE = "https://open.feishu.cn/open-apis"


def load_config():
    """优先从环境变量读取，不存在则尝试从 feishu_config.env 读取"""
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "config", "feishu_config.env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


def get_tenant_token():
    """获取 tenant_access_token"""
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        raise ValueError("FEISHU_APP_ID 或 FEISHU_APP_SECRET 未设置")

    url = f"{FEISHU_BASE}/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    if result.get("code") != 0:
        raise Exception(f"获取token失败: {result}")
    return result["tenant_access_token"]


def api_call(method, path, token=None, data=None, params=None):
    """通用 API 调用"""
    url = f"{FEISHU_BASE}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise Exception(f"API调用失败 {method} {path}: {e.code} {error_body}")


# ===== Wiki 操作 =====

def list_wiki_nodes(space_id, parent_node_token, page_size=50):
    """列出知识库指定父节点下的子节点"""
    token = get_tenant_token()
    all_nodes = []
    page_token = ""
    while True:
        params = {"parent_node_token": parent_node_token, "page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        result = api_call("GET", f"/wiki/v2/spaces/{space_id}/nodes", token=token, params=params)
        if result.get("code") != 0:
            raise Exception(f"获取节点列表失败: {result}")
        items = result.get("data", {}).get("items", [])
        all_nodes.extend(items)
        page_token = result.get("data", {}).get("page_token", "")
        if not result.get("data", {}).get("has_more", False) or not page_token:
            break
    return all_nodes


def create_wiki_node(space_id, parent_node_token, title, obj_type="docx"):
    """创建知识库节点"""
    token = get_tenant_token()
    data = {
        "obj_type": obj_type,
        "node_type": "origin",
        "parent_node_token": parent_node_token,
        "title": title,
    }
    result = api_call("POST", f"/wiki/v2/spaces/{space_id}/nodes", token=token, data=data)
    if result.get("code") != 0:
        raise Exception(f"创建节点失败: {result}")
    return result.get("data", {}).get("node", {})


def move_wiki_node(space_id, node_token, target_parent_token):
    """移动知识库节点"""
    token = get_tenant_token()
    data = {"target_parent_token": target_parent_token}
    result = api_call("POST", f"/wiki/v2/spaces/{space_id}/nodes/{node_token}/move", token=token, data=data)
    if result.get("code") != 0:
        raise Exception(f"移动节点失败: {result}")
    return result.get("data", {}).get("node", {})


def get_wiki_node_info(space_id, token_field, token_value):
    """获取节点信息（通过 node_token 或 obj_token）"""
    token = get_tenant_token()
    params = {"token": token_value, "obj_type": "docx"}
    if token_field == "node_token":
        params["token_type"] = "node"
    else:
        params["token_type"] = "obj"
    result = api_call("GET", f"/wiki/v2/spaces/{space_id}/nodes/{token_value}", token=token)
    if result.get("code") != 0:
        raise Exception(f"获取节点信息失败: {result}")
    return result.get("data", {}).get("node", {})


# ===== 文档操作 =====

def get_doc_blocks(document_id):
    """获取文档的所有子块"""
    token = get_tenant_token()
    all_blocks = []
    page_token = ""
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        result = api_call("GET", f"/docx/v1/documents/{document_id}/blocks", token=token, params=params)
        if result.get("code") != 0:
            raise Exception(f"获取文档块失败: {result}")
        items = result.get("data", {}).get("items", [])
        all_blocks.extend(items)
        page_token = result.get("data", {}).get("page_token", "")
        if not result.get("data", {}).get("has_more", False) or not page_token:
            break
    return all_blocks


def delete_doc_block(document_id, block_id):
    """删除文档块"""
    token = get_tenant_token()
    result = api_call("DELETE", f"/docx/v1/documents/{document_id}/blocks/{block_id}", token=token)
    if result.get("code") != 0:
        raise Exception(f"删除块失败: {result}")
    return True


def convert_markdown_to_blocks(markdown_text):
    """将 Markdown 转换为飞书文档块结构"""
    token = get_tenant_token()
    data = {"content": markdown_text, "content_type": "markdown"}
    result = api_call("POST", "/docx/v1/documents/blocks/convert", token=token, data=data)
    if result.get("code") != 0:
        raise Exception(f"转换Markdown失败: {result}")
    return result.get("data", {}).get("blocks", [])


def clean_table_blocks(blocks):
    """清理表格块的额外字段（飞书创建API不接受这些字段）"""
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get("block_type") == 31:  # table
            table = block.get("table", {})
            if isinstance(table, dict):
                # 移除 cells（API不接受）
                table.pop("cells", None)
                # 移除 property.merge_info
                prop = table.get("property", {})
                if isinstance(prop, dict):
                    prop.pop("merge_info", None)
        # 递归清理子块（children 可能是字符串 ID 列表或对象列表）
        children = block.get("children", [])
        if children and isinstance(children[0], dict):
            clean_table_blocks(children)


def insert_blocks_to_doc(document_id, parent_block_id, blocks, index=0):
    """使用嵌套块API插入文档内容（支持扁平结构）"""
    token = get_tenant_token()
    clean_table_blocks(blocks)

    # 收集所有被引用为子块的 block_id（这些不是顶层块）
    child_ids = set()
    for b in blocks:
        for child_id in b.get("children", []):
            if isinstance(child_id, str):
                child_ids.add(child_id)

    # 顶层块 = 不被任何块引用为子块的块
    top_level_ids = [b["block_id"] for b in blocks if b.get("block_id") and b.get("block_id") not in child_ids]

    # 清理所有块的 parent_id（API不接受此字段）
    for b in blocks:
        b.pop("parent_id", None)

    # 一次性发送所有块
    data = {
        "index": index,
        "children_id": top_level_ids,
        "descendants": blocks,
    }
    result = api_call("POST", f"/docx/v1/documents/{document_id}/blocks/{parent_block_id}/descendant",
                      token=token, data=data, params={"document_revision_id": "-1"})
    if result.get("code") != 0:
        raise Exception(f"插入块失败: {result}")
    return True


def update_doc_content(document_id, markdown_text):
    """全量更新文档内容（用 Markdown 替换所有现有内容）"""
    # 1. 获取现有子块并删除
    blocks = get_doc_blocks(document_id)
    for block in blocks:
        try:
            delete_doc_block(document_id, block["block_id"])
        except Exception:
            pass  # 删除失败的跳过

    # 2. 转换 Markdown 为块
    new_blocks = convert_markdown_to_blocks(markdown_text)

    if not new_blocks:
        return True

    # 3. 插入新块到文档根节点
    insert_blocks_to_doc(document_id, document_id, new_blocks, index=0)
    return True


def create_docx(title):
    """创建一篇新的 docx 文档"""
    token = get_tenant_token()
    data = {"title": title}
    result = api_call("POST", "/docx/v1/documents", token=token, data=data)
    if result.get("code") != 0:
        raise Exception(f"创建文档失败: {result}")
    return result.get("data", {}).get("document", {})


# ===== 消息操作 =====

def send_message(receive_id, text, receive_id_type="open_id"):
    """发送文本消息"""
    token = get_tenant_token()
    data = {
        "receive_id": receive_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}),
    }
    result = api_call("POST", f"/im/v1/messages", token=token, data=data,
                      params={"receive_id_type": receive_id_type})
    if result.get("code") != 0:
        raise Exception(f"发送消息失败: {result}")
    return result.get("data", {})


# ===== 命令行入口 =====

def main():
    load_config()

    parser = argparse.ArgumentParser(description="飞书 API 工具")
    subparsers = parser.add_subparsers(dest="command")

    # 列出节点
    p_list = subparsers.add_parser("list-nodes", help="列出知识库节点")
    p_list.add_argument("--space-id", required=True)
    p_list.add_argument("--parent-node-token", required=True)

    # 创建节点
    p_create = subparsers.add_parser("create-node", help="创建知识库节点")
    p_create.add_argument("--space-id", required=True)
    p_create.add_argument("--parent-node-token", required=True)
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--obj-type", default="docx")

    # 移动节点
    p_move = subparsers.add_parser("move-node", help="移动知识库节点")
    p_move.add_argument("--space-id", required=True)
    p_move.add_argument("--node-token", required=True)
    p_move.add_argument("--target-parent-token", required=True)

    # 更新文档内容
    p_update = subparsers.add_parser("update-doc", help="用Markdown更新文档内容")
    p_update.add_argument("--document-id", required=True)
    p_update.add_argument("--file", required=True, help="Markdown文件路径")

    # 发送消息
    p_msg = subparsers.add_parser("send-msg", help="发送文本消息")
    p_msg.add_argument("--open-id", required=True)
    p_msg.add_argument("--text", required=True, help="消息内容")

    args = parser.parse_args()

    if args.command == "list-nodes":
        nodes = list_wiki_nodes(args.space_id, args.parent_node_token)
        print(json.dumps(nodes, ensure_ascii=False, indent=2))

    elif args.command == "create-node":
        node = create_wiki_node(args.space_id, args.parent_node_token, args.title, args.obj_type)
        print(json.dumps(node, ensure_ascii=False, indent=2))

    elif args.command == "move-node":
        node = move_wiki_node(args.space_id, args.node_token, args.target_parent_token)
        print(json.dumps(node, ensure_ascii=False, indent=2))

    elif args.command == "update-doc":
        with open(args.file, "r") as f:
            content = f.read()
        update_doc_content(args.document_id, content)
        print(json.dumps({"status": "ok", "document_id": args.document_id}, ensure_ascii=False))

    elif args.command == "send-msg":
        result = send_message(args.open_id, args.text)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
