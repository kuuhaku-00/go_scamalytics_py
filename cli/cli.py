"""
命令行工具:
- 支持参数:
    -i INPUT_FILE    (每行一个 IP)
    -o OUTPUT_CSV    (输出 CSV 文件路径)
    -u UA_FILE       (每行一个 User-Agent，可选)
    -t THREADS       (并发线程数, default 10)
示例:
    python -m go_scamalytics_py.cli.cli -i ips.txt -o out.csv -u ualist.txt -t 20
"""

import argparse
import csv
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from pathlib import Path
from tqdm import tqdm

from ipchecker import CheckIP

def read_lines_strip(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def process_ip(ip: str, user_agents: List[str]):
    return CheckIP(ip, user_agents)

def Start(argv: List[str] = None):
    p = argparse.ArgumentParser(description="go-scamalytics Python CLI (scrape scamalytics.com)")
    p.add_argument("-i", "--input", required=True, help="Input file with one IP per line")
    p.add_argument("-o", "--output", required=True, help="Output CSV file")
    p.add_argument("-u", "--useragents", required=False, help="File with one User-Agent per line (optional)")
    p.add_argument("-t", "--threads", type=int, default=10, help="Number of concurrent threads (default 10)")
    args = p.parse_args(argv)

    if not os.path.isfile(args.input):
        raise SystemExit(f"Input file not found: {args.input}")

    ips = read_lines_strip(args.input)
    user_agents = []
    if args.useragents and os.path.isfile(args.useragents):
        user_agents = read_lines_strip(args.useragents)

    results = []
    # 并发查找
    with ThreadPoolExecutor(max_workers=args.threads) as ex:
        futures = {ex.submit(process_ip, ip, user_agents): ip for ip in ips}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Checking IPs"):
            ip = futures[fut]
            try:
                res = fut.result()
            except Exception as e:
                res = {"ip": ip, "error": f"exception: {str(e)}"}
            results.append(res)

    # 写 CSV: 包含固定列 ip, score, risk, error; 其余字段放入 raw_json 列（转成字符串）
    out_fields = ["ip", "score", "risk", "error", "raw_json"]
    out_path = args.output
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=out_fields)
        writer.writeheader()
        for r in results:
            row = {
                "ip": r.get("ip"),
                "score": r.get("score", ""),
                "risk": r.get("risk", ""),
                "error": r.get("error", ""),
                "raw_json": ""
            }
            if "_raw_parsed" in r:
                try:
                    import json
                    row["raw_json"] = json.dumps(r["_raw_parsed"], ensure_ascii=False)
                except Exception:
                    row["raw_json"] = str(r["_raw_parsed"])
            # 如果解析失败，但 raw 字段在返回中（例如解析失败返回 partial raw string）
            if "raw" in r and not row["raw_json"]:
                row["raw_json"] = r["raw"]
            writer.writerow(row)

    print(f"Wrote {len(results)} records to {out_path}")
