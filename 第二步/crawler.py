# crawler.py
# 核心抓取逻辑 100% 移植自你成功运行的 CSV 脚本

import requests
import json
import time
import random
import logging
from db_helper import save_news, get_max_news_id, init_db
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ---------- 以下是你 CSV 脚本里 100% 成功的函数（一字不改） ----------
def find_matching_parenthesis(text, start):
    count = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            count += 1
        elif text[i] == ')':
            count -= 1
            if count == 0:
                return i
    return -1

def extract_jsonp(text):
    start = text.find('(')
    if start == -1:
        return None
    end = find_matching_parenthesis(text, start)
    if end == -1:
        return None
    json_str = text[start+1:end].strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logging.warning(f"JSON解析失败: {e}")
        return None

def fetch_news(page=1, size=20):
    """使用队友提供的完整浏览器指纹和Cookie进行请求（稳定破解缓存）"""
    # 使用队友代码里的完整 Base URL（不带 callback 后缀）
    base_url = "https://app.cj.sina.com.cn/api/news/pc"
    
    # 【关键】使用队友从浏览器复制的完整 Headers，特别是 Cookie
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://finance.sina.com.cn/",
        "Sec-Ch-Ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "script",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-site",
        # 这是队友的稳定利器！直接从浏览器复制过来的身份凭证
        "Cookie": "UOR=cn.bing.com,finance.sina.com.cn,; SINAGLOBAL=111.203.16.88_1778660054.857994; Apache=1.203.69.82_1781675727.105329; ULV=1781676825849:2:1:1:1.203.69.82_1781675727.105329:1778660056281"
    }
    
    # 构造参数（和队友完全一致）
    params = {
        "page": page,
        "size": size,
        "tag": 0,
        "id": "",
        "type": 0,
        "_": int(time.time() * 1000)
    }
    
    try:
        resp = requests.get(base_url, headers=headers, params=params, timeout=10)
        resp.encoding = 'utf-8'
        text = resp.text
        
        # 【兼容处理】队友的代码能解析 JSON 也能解析 JSONP，我们照搬这个逻辑
        data = None
        # 尝试直接解析 JSON
        try:
            data = json.loads(text)
        except:
            # 如果失败，尝试提取 JSONP 括号里的内容（兼容我们之前的 extract_jsonp 逻辑）
            import re
            match = re.search(r'\(({.*})\)', text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                except:
                    pass
        
        if not data:
            logging.warning(f"第 {page} 页数据解析失败")
            return None
            
        return data
        
    except Exception as e:
        logging.error(f"第{page}页抓取出错: {e}")
        return None

def parse_news(data):
    # 和你 CSV 完全一样的解析逻辑（保留了 ext 字段）
    try:
        feed_list = data['result']['data']['feed']['list']
        parsed = []
        for item in feed_list:
            tags = [tag['name'] for tag in item.get('tag', [])]
            parsed.append({
                'id': item.get('id'),
                'content': item.get('rich_text', ''),
                'create_time': item.get('create_time'),
                'view_num': item.get('view_num', ''),
                'comment_num': item.get('comment_num', 0),
                'tags': ', '.join(tags),
                'docurl': item.get('docurl', ''),
                'ext': item.get('ext', ''),  # 加上 ext，和 CSV 版本完全一致
            })
        return parsed
    except KeyError as e:
        logging.warning(f"解析数据时缺少字段: {e}")
        return []

# ---------- 历史数据全量爬取（带断点续爬） ----------
def crawl_history_pages(max_pages=45):
    init_db()
    local_max_id = get_max_news_id()
    if local_max_id > 0:
        logging.info(f"检测到本地已有数据，最大ID: {local_max_id}")
    
    total_new_count = 0
    for page in range(1, max_pages + 1):
        delay = random.uniform(1, 2.5)
        logging.info(f"正在抓取第 {page} 页 (延时 {delay:.2f}s)...")
        time.sleep(delay)
        
        data = fetch_news(page, 20)
        if not data:
            logging.warning(f"第 {page} 页无数据，停止翻页")
            break
        
        news_list = parse_news(data)
        if not news_list:
            continue
        
        # 断点续爬：如果当前页第一条 ID 小于等于本地最大 ID，说明遇到旧数据了
        first_id_in_page = news_list[0]['id']
        if local_max_id > 0 and first_id_in_page <= local_max_id:
            logging.info(f"遇到已存在的旧数据 (ID: {first_id_in_page} <= {local_max_id})，停止回溯")
            break
        
        inserted = save_news(news_list)
        total_new_count += inserted
        logging.info(f"第 {page} 页入库 {inserted} 条 (本页解析 {len(news_list)} 条)")
        
        if inserted == 0:
            logging.info("本页数据全部重复，停止爬取")
            break
    
    logging.info(f"🎉 历史数据抓取完成！本次新增入库 {total_new_count} 条")
    return total_new_count
# ========== 新增：增量爬取函数（只抓最新一页，用于定时任务） ==========
def crawl_incremental():
    """
    增量爬取：只抓最新一页（20条），通过与本地最大ID对比，只入库新增的新闻。
    这个函数专门给定时调度器（scheduler.py）调用。
    """
    # 确保数据库表存在
    init_db()
    
    # 获取本地已存的最大新闻ID
    local_max_id = get_max_news_id()
    logging.info(f"当前本地最大ID: {local_max_id}，开始检查最新新闻...")
    
    # 只请求第一页（最新20条）
    data = fetch_news(page=1, size=20)
    if not data:
        logging.warning("增量抓取失败：未获取到数据")
        return 0
    
    # 解析新闻列表
    news_list = parse_news(data)
    if not news_list:
        logging.warning("增量抓取失败：解析数据为空")
        return 0
    
    # 【关键】筛选出比本地最大ID更新的新闻（即真正的新增内容）
    new_items = []
    for item in news_list:
        # 如果新闻ID大于本地最大ID，说明是没存过的新新闻
        if item['id'] > local_max_id:
            new_items.append(item)
    
    # 如果有新新闻，入库
    if new_items:
        inserted = save_news(new_items)
        logging.info(f"📈 本次增量抓取发现 {len(new_items)} 条新新闻，成功入库 {inserted} 条")
        
        # 打印前3条预览（方便你肉眼确认）
        for i, item in enumerate(new_items[:3]):
            logging.info(f"  → 新增: {item['create_time']} - {item['content'][:40]}...")
        return inserted
    else:
        logging.info("⏳ 暂无新新闻发布")
        return 0