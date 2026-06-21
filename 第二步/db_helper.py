# db_helper.py
import sqlite3
import logging
import os  # 加上这一行

# 【新增】自动获取当前代码所在的文件夹路径，数据库就生成在这里
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'sina_news.db')  # 数据库会直接放在 Sina_Project 文件夹里



def init_db():
    """初始化数据库，创建一张名叫 news 的表"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            news_id INTEGER PRIMARY KEY,          -- 新闻ID，作为唯一主键去重
            content TEXT,                         -- 新闻正文
            publish_time TEXT,                    -- 发布时间
            crawl_time TEXT DEFAULT CURRENT_TIMESTAMP, -- 爬虫入库时间（自动生成）
            source_url TEXT,                      -- 详情页链接
            view_num TEXT,                        -- 阅读量
            comment_num INTEGER,                  -- 评论数
            tags TEXT                             -- 标签
        )
    ''')
    conn.commit()
    conn.close()

def get_max_news_id():
    """获取当前数据库中最大的新闻ID，用于断点续爬（明天用）"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(news_id) FROM news')
    result = cursor.fetchone()[0]
    conn.close()
    return result if result is not None else 0

def save_news(news_list):
    """
    批量保存新闻到数据库
    如果 news_id 已经存在，则自动忽略（这就是去重）
    """
    if not news_list:
        return 0
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 插入语句，IGNORE 表示如果主键重复就跳过
    insert_sql = '''
        INSERT OR IGNORE INTO news 
        (news_id, content, publish_time, source_url, view_num, comment_num, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    
    data_to_insert = []
    for item in news_list:
        data_to_insert.append((
            item.get('id'),
            item.get('content', ''),
            item.get('create_time'),
            item.get('docurl', ''),
            item.get('view_num', ''),
            item.get('comment_num', 0),
            item.get('tags', '')
        ))
    
    cursor.executemany(insert_sql, data_to_insert)
    conn.commit()
    inserted_count = cursor.rowcount  # 返回实际插入了多少条
    conn.close()
    return inserted_count