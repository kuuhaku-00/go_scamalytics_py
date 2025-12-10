# go-scamalytics (Python port)

功能：从 scamalytics.com 抓取 IP 的 fraud score / risk（不使用官方 API），支持批量 CSV 导出。



原项目是GitHub上 [Allespro/go-scamalytics](https://github.com/Allespro/go-scamalytics) ，使用的语言是go，用不惯，就转换为了python版本，计划与另一个py项目整合



**本项目使用uv管理**



### 无uv环境初始化

```
uv init
uv add -r .\requirements.txt
```

### 若有`pyproject.toml`

```
# 1. 同步所有依赖（uv 会自动读取 pyproject.toml）
uv sync

# 2. 激活虚拟环境
uv shell

# 3. 或者在虚拟环境中运行单条命令
uv run python main.py
```



### 创建ua.txt

```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15
Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/122.0
Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Mobile/15E148 Safari/604.1
Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36
Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36
Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)
Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)
curl/8.1.2
Wget/1.21.3
python-requests/2.31.0
```



### 创建`ips.txt`

每行一个ip

```
223.5.5.5
8.8.8.8
114.114.114.114
```



### 运行命令

```
uv run python main.py -i ips.txt -o results.csv -u ua.txt -t 20
```



