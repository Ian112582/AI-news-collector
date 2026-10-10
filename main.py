import os
import urllib.parse
import feedparser
import requests
from openai import OpenAI

# 1. 設定你的關鍵字與查詢數量
KEYWORDS = ["美股", "AI"]  # 可自由修改或增加關鍵字
MAX_ARTICLES_PER_KEYWORD = 3      # 每個關鍵字抓取最新的前幾篇

# 2. 讀取安全環境變數
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

def fetch_google_news(keyword):
    """抓取 Google News RSS"""
    encoded_keyword = urllib.parse.quote(keyword)
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(rss_url)
    return feed.entries[:MAX_ARTICLES_PER_KEYWORD]

def analyze_with_ai(title, link):
    """呼叫 OpenAI 進行評分與摘要"""
    prompt = f"""
    請閱讀以下新聞標題並進行分析：
    標題：{title}
    連結：{link}

    請輸出以下格式：
    【重要程度】：1 到 5 顆星（例如：⭐⭐⭐⭐）
    【一句話摘要】：用 50 字以內摘要這篇新聞的核心內容與對產業的影響。
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一位專業的科技新聞分析師。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def send_telegram_message(message):
    """發送訊息到 Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload)

def main():
    final_report = "📰 **每日 AI 新聞情報摘要**\n\n"
    
    for kw in KEYWORDS:
        final_report += f"🔍 **關鍵字：{kw}**\n"
        articles = fetch_google_news(kw)
        
        if not articles:
            final_report += "今日無相關新聞。\n\n"
            continue
            
        for i, article in enumerate(articles, 1):
            title = article.title
            link = article.link
            
            # AI 評分摘要
            analysis = analyze_with_ai(title, link)
            
            final_report += f"\n{i}. [{title}]({link})\n"
            final_report += f"{analysis}\n"
            final_report += "---------------------\n"
        final_report += "\n"
        
    # 發送給 Telegram
    send_telegram_message(final_report)
    print("今日新聞摘要已成功發送！")

if __name__ == "__main__":
    main()
