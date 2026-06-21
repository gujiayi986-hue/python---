# view_data.py
# 专门用于查看数据库内容的工具脚本

import sqlite3
import os
import pandas as pd

# ===== 【关键修复】自动定位到当前脚本所在的文件夹 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'sina_news.db')
# =====================================================

def check_db_exists():
    """检查数据库文件是否存在"""
    if not os.path.exists(DB_FILE):
        print(f"❌ 数据库文件 {DB_FILE} 不存在！")
        print(f"💡 请确保 {os.path.basename(DB_FILE)} 和这个脚本在同一个文件夹中。")
        return False
    print(f"✅ 找到数据库: {DB_FILE}")
    return True
def get_total_count():
    """获取新闻总条数"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM news")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def show_latest(n=10):
    """显示最新的 n 条新闻（按发布时间倒序）"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT news_id, publish_time, content, view_num, tags 
        FROM news 
        ORDER BY publish_time DESC 
        LIMIT ?
    """, (n,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("📭 数据库为空")
        return
    
    print(f"\n📰 最新 {len(rows)} 条新闻：")
    print("-" * 80)
    for row in rows:
        news_id, pub_time, content, view_num, tags = row
        # 内容截断，避免太长
        content_short = content[:60] + "..." if len(content) > 60 else content
        print(f"ID: {news_id}")
        print(f"时间: {pub_time}")
        print(f"内容: {content_short}")
        print(f"阅读: {view_num}  | 标签: {tags}")
        print("-" * 40)

def show_earliest(n=10):
    """显示最早的 n 条新闻（按发布时间正序）"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT news_id, publish_time, content, view_num, tags 
        FROM news 
        ORDER BY publish_time ASC 
        LIMIT ?
    """, (n,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("📭 数据库为空")
        return
    
    print(f"\n📰 最早 {len(rows)} 条新闻：")
    print("-" * 80)
    for row in rows:
        news_id, pub_time, content, view_num, tags = row
        content_short = content[:60] + "..." if len(content) > 60 else content
        print(f"ID: {news_id}")
        print(f"时间: {pub_time}")
        print(f"内容: {content_short}")
        print(f"阅读: {view_num}  | 标签: {tags}")
        print("-" * 40)

def show_statistics():
    """显示基本统计信息"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 总条数
    cursor.execute("SELECT COUNT(*) FROM news")
    total = cursor.fetchone()[0]
    
    # 最早和最晚时间
    cursor.execute("SELECT MIN(publish_time), MAX(publish_time) FROM news")
    min_time, max_time = cursor.fetchone()
    
    # 各标签统计
    cursor.execute("""
        SELECT tags, COUNT(*) as cnt 
        FROM news 
        WHERE tags != '' 
        GROUP BY tags 
        ORDER BY cnt DESC
    """)
    tag_stats = cursor.fetchall()
    
    conn.close()
    
    print("\n📊 数据库统计信息")
    print("=" * 50)
    print(f"总新闻数: {total} 条")
    if min_time and max_time:
        print(f"时间范围: {min_time}  ~  {max_time}")
    else:
        print("时间范围: 暂无数据")
    
    if tag_stats:
        print("\n🏷️ 标签分布:")
        for tags, cnt in tag_stats:
            print(f"  {tags}: {cnt} 条")
    else:
        print("\n暂无标签数据")

def export_to_csv(filename='exported_news.csv', limit=None):
    """导出数据到CSV文件（可选导出全部或限制条数）"""
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT news_id, publish_time, content, view_num, comment_num, tags, source_url, crawl_time FROM news"
    if limit:
        query += f" ORDER BY publish_time DESC LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("📭 没有数据可导出")
        return
    
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"✅ 已导出 {len(df)} 条数据到 {filename}")

def main():
    if not check_db_exists():
        return
    
    print("🔍 数据库查看器")
    print("1. 显示统计信息")
    print("2. 显示最新 10 条")
    print("3. 显示最早 10 条")
    print("4. 显示最新 N 条（自定义）")
    print("5. 导出全部数据到 CSV（需安装 pandas）")
    print("0. 退出")
    
    choice = input("请选择操作 (0-5): ").strip()
    
    if choice == '1':
        show_statistics()
    elif choice == '2':
        show_latest(10)
    elif choice == '3':
        show_earliest(10)
    elif choice == '4':
        try:
            n = int(input("请输入要显示的条数: "))
            show_latest(n)
        except ValueError:
            print("❌ 请输入有效数字")
    elif choice == '5':
        try:
            import pandas as pd
            limit = input("请输入要导出的条数（留空导出全部）: ").strip()
            if limit:
                export_to_csv(limit=int(limit))
            else:
                export_to_csv()
        except ImportError:
            print("❌ 未安装 pandas，无法导出。请安装 pandas: pip install pandas")
    elif choice == '0':
        print("👋 退出")
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()
