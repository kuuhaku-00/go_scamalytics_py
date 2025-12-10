# 方便用户直接运行： python main.py -i ips.txt -o out.csv
from cli.cli import Start
import sys

if __name__ == "__main__":
    Start(sys.argv[1:])
