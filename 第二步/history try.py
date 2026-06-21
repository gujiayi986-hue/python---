import json
import time
from playwright.sync_api import sync_playwright


def fetch_sina_news_final(stop_count=50):
    all_news = []
    seen_ids = set()
    print(f"🚀 启动浏览器，目标爬取: {stop_count} 条...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        def handle_response(response):
            url = response.url
            if "app.cj.sina.com.cn/api/news/pc" in url:
                try:
                    body = response.text()
                    json_str = body
                    if "try{" in body and "jQuery" in body:
                        json_str = body[body.index("(")+1:body.rindex("})") + 1]

                    data = json.loads(json_str)
                    news_list = data.get('result', {}).get('data', {}).get('feed', {}).get('list', [])

                    if news_list:
                        for item in news_list:
                            news_id = item.get('id')
                            title = item.get('rich_text', '').strip()
                            time_str = item.get('create_time', '')

                            if news_id and news_id not in seen_ids and title:
                                seen_ids.add(news_id)
                                all_news.append({
                                    "news_id": news_id,
                                    "content": title,
                                    "publish_time": time_str,
                                    "view_num": item.get('view_num', ''),
                                    "comment_num": item.get('comment_num', 0),
                                    "tags": ', '.join([tag['name'] for tag in item.get('tag', [])]),
                                    "source_url": item.get('docurl', '')
                                })
                                print(f"✅ 已获取 {len(all_news):>3} 条: {time_str} - {title[:30]}...")
                except Exception as e:
                    print(f"❌ 解析响应时出错: {e}")

        page.on("response", handle_response)
        page.goto("https://finance.sina.com.cn/7x24/", wait_until="domcontentloaded")
        print("🌐 页面加载完成，开始模拟滚动...")

        no_new_data_count = 0

        while len(all_news) < stop_count:
            count_before = len(all_news)
            page.evaluate("window.scrollBy(0, 2000)")
            try:
                page.wait_for_load_state('networkidle', timeout=5000)
            except:
                pass
            time.sleep(1)

            if len(all_news) > count_before:
                no_new_data_count = 0
            else:
                no_new_data_count += 1
                print(f"⚠️ 第 {no_new_data_count} 次滚动未获取到新数据...")
                if no_new_data_count >= 10:
                    print("🛑 连续10次无新数据，停止滚动。")
                    break

        browser.close()

    return all_news[:stop_count]


if __name__ == "__main__":
    news = fetch_sina_news_final(stop_count=1000)
    print(f"\n🎉 最终获取到 {len(news)} 条新闻!")
    
    # 保存为 JSON 文件（供队友合并）
    with open('history_news.json', 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
    print("💾 历史数据已保存到 history_news.json，请将此文件发给队友！")