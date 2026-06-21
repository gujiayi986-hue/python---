# main.py
import os
import sys

# 强行把当前文件所在的文件夹添加到 Python 的搜索路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 下面是原来的代码
from crawler import crawl_history_pages

if __name__ == "__main__":
    print("🚀 开始初始化数据库并爬取全部历史新闻...")
    crawl_history_pages(max_pages=45)
    print("✅ 数据初始化完成！")
    print("请查看当前文件夹，你会看到新生成的 'sina_news.db' 文件和 'crawler.log' 日志文件。")