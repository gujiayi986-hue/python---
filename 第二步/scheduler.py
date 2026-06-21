# scheduler.py
# 每隔 10 分钟运行一次增量爬取

import time
import schedule
from crawler import crawl_incremental

def job():
    print(f"\n🕐 {time.strftime('%Y-%m-%d %H:%M:%S')} 开始增量爬取...")
    crawl_incremental()

if __name__ == "__main__":
    print("🚀 定时爬虫启动，每10分钟抓取一次最新新闻...")
    # 先立即执行一次
    job()
    # 然后每 10 分钟执行一次
    schedule.every(10).minutes.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)