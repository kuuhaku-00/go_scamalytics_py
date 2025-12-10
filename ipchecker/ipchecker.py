"""
ipchecker.ipchecker

提供 CheckIP(ip, user_agents_list) -> dict 功能。
目标：向 https://scamalytics.com/ip/{ip} 请求页面（随机或指定 User-Agent），
解析页面中显示的 "IP Fraud Risk API" JSON 块并返回一个字典，至少包含:
    {"ip": "...", "score": "...", "risk": "...", ...}
如果解析失败，会返回 {'ip': ip, 'error': '...'} 格式的结果。
"""

from __future__ import annotations
import requests
import random
import re
import json
from typing import List, Dict, Any, Optional

_DEFAULT_USER_AGENTS = [
    # 提供若干常见 UA 供随机选择；CLI 也允许用户传入自定义列表。
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

_REQUEST_TIMEOUT = 15  # seconds

def _choose_user_agent(user_agents: Optional[List[str]]) -> str:
    if user_agents:
        return random.choice(user_agents)
    return random.choice(_DEFAULT_USER_AGENTS)

def _fetch_page(ip: str, user_agent: str, session: Optional[requests.Session] = None) -> str:
    url = f"https://scamalytics.com/ip/{ip}"
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    s = session or requests.Session()
    resp = s.get(url, headers=headers, timeout=_REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text

def _extract_json_block_from_text(text: str) -> Optional[str]:
    """
    在页面文本中寻找 'IP Fraud Risk API' 后面紧跟的 JSON 对象块。
    我们尽量用“找到第一个 '{' 并用括号配对提取完整 JSON” 的方式，
    以便处理多行格式化 JSON。
    返回 JSON 字符串（如果成功），否则 None。
    """
    # 定位关键词
    marker_pos = text.find("IP Fraud Risk API")
    if marker_pos == -1:
        # 备用：有些页面可能直接包含 `"ip":"...","score":"..."` 但缺关键词
        marker_pos = 0

    # 从 marker_pos 向后找第一个 '{'
    start = text.find("{", marker_pos)
    if start == -1:
        return None

    # 用括号计数器向后扫描直到匹配闭合
    depth = 0
    i = start
    end = None
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        i += 1

    if end is None:
        return None

    candidate = text[start:end]

    # 清理 HTML 实体 / 多余的省略符号（网站示例有时会显示 "..."）
    # 将 HTML 标签移除（如果误包含）
    candidate = re.sub(r"<[^>]+>", "", candidate)

    # 有些页面会在片段中显示 "..." 或省略信息，我们不能解析含有 "..." 的 JSON
    # 将出现的三点替换为 null 或将其删除（如果存在）
    candidate = candidate.replace("...", "")

    # 进一步清理：去掉单行注释或尾随逗号（尝试修复小错误以便 json.loads 成功）
    # 去掉 JavaScript 注释
    candidate = re.sub(r"//.*?$", "", candidate, flags=re.MULTILINE)
    # 删除尾随逗号 (e.g., {"a":1,})
    candidate = re.sub(r",\s*}", "}", candidate)
    candidate = re.sub(r",\s*]", "]", candidate)

    return candidate

def _safe_json_loads(s: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(s)
    except Exception:
        # 如果解析失败，尝试使用更宽松的替换（例如将单引号换成双引号）
        try:
            s2 = s.replace("'", "\"")
            return json.loads(s2)
        except Exception:
            return None

def CheckIP(ip: str, user_agents_list: Optional[List[str]] = None, session: Optional[requests.Session] = None) -> Dict[str, Any]:
    """
    查询 scamalytics.com 对单个 IP 的页面并解析出结果。
    返回一个 dict，至少包含 ip 字段；在成功时返回 "score" 和 "risk" 等（字符串）。
    失败时返回 {'ip': ip, 'error': '...'}。
    """
    ua = _choose_user_agent(user_agents_list)
    try:
        text = _fetch_page(ip, ua, session=session)
    except requests.RequestException as e:
        return {"ip": ip, "error": f"http_error: {str(e)}"}

    json_block = _extract_json_block_from_text(text)
    if not json_block:
        # 作为降级尝试：在页面中直接用正则找到 "ip":"...", "score":"...", "risk":"..."
        m_ip = re.search(r'"ip"\s*:\s*"([^"]+)"', text)
        m_score = re.search(r'"score"\s*:\s*"([^"]+)"', text)
        m_risk = re.search(r'"risk"\s*:\s*"([^"]+)"', text)
        if m_ip or m_score or m_risk:
            result = {"ip": ip}
            if m_ip:
                result["ip"] = m_ip.group(1)
            if m_score:
                result["score"] = m_score.group(1)
            if m_risk:
                result["risk"] = m_risk.group(1)
            return result
        return {"ip": ip, "error": "no_json_block_found"}

    parsed = _safe_json_loads(json_block)
    if not parsed:
        # 返回原始 json_block 以便用户调试
        return {"ip": ip, "error": "json_parse_failed", "raw": json_block[:200]}

    # 保证返回至少 ip, score, risk 三个字段
    out = {"ip": parsed.get("ip", ip)}
    if "score" in parsed:
        out["score"] = parsed.get("score")
    if "risk" in parsed:
        out["risk"] = parsed.get("risk")
    # 复制其他常见字段（如果存在）
    for k in ("is_blacklisted_external", "operator", "hostname", "asn"):
        if k in parsed:
            out[k] = parsed[k]

    # 将剩余字段以 flat 的方式并入（可选）
    # 出于简洁默认不全部并入；用户可以从 parsed 获取全部信息。
    out["_raw_parsed"] = parsed  # 如果用户需要全部信息可查看这个键

    return out
