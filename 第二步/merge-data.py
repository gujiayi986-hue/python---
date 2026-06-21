# merge_history.py
# 把队友的历史数据合并到你的数据库里

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = 'sina_news.db'

def merge_history_json(json_file='history_news.json'):
    if not os.path.exists(json_file):
        print(f"❌ 找不到 {json_file}")
        print("💡 请确认队友已运行脚本并生成了 history_news.json 文件，且放在此目录下")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        history_list = json.load(f)
    
    print(f"📂 读取到 {len(history_list)} 条历史新闻")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted_count = 0
    skipped_count = 0
    
    for item in history_list:
        cursor.execute("SELECT news_id FROM news WHERE news_id = ?", (item['news_id'],))
        existing = cursor.fetchone()
        
        if existing:
            skipped_count += 1
            continue
        
        cursor.execute("""
            INSERT INTO news 
            (news_id, content, publish_time, crawl_time, source_url, view_num, comment_num, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item['news_id'],
            item['content'],
            item['publish_time'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            item.get('source_url', ''),
            item.get('view_num', ''),
            item.get('comment_num', 0),
            item.get('tags', '')
        ))
        inserted_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ 合并完成！")
    print(f"   - 新增 {inserted_count} 条")
    print(f"   - 跳过 {skipped_count} 条重复数据")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM news")
    total = cursor.fetchone()[0]
    conn.close()
    print(f"📊 当前数据库总条数：{total} 条")

if __name__ == "__main__":
    merge_history_json()