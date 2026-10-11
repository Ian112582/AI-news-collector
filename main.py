import os
import urllib.parse
import feedparser
import requests
from openai import OpenAI

# ---------------------------------------------------------
# 1. 設定關鍵字與抓取數量
# ---------------------------------------------------------
ZH_KEYWORDS = ["台積電", "景碩", "日月光"]
EN_KEYWORDS = ["SPCX", "TSLA", "Quantum Computer", "GE Vernova"]

MAX_ARTICLES = 3  # 每個關鍵字抓取的文章數量

# ---------------------------------------------------------
# 2. 安全讀取環境變數
# ---------------------------------------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

def fetch_google_news(keyword, lang="zh-TW"):
    """抓取 Google News RSS (支援指定語言與地區)"""
    encoded_keyword = urllib.parse.quote(keyword)
    
    if lang == "en":
        rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=en-US&gl=US&ceid=US:en"
    else:
        rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        
    feed = feedparser.parse(rss_url)
    return feed.entries[:MAX_ARTICLES]

def analyze_with_ai(title, link, is_foreign=False):
    """呼叫 OpenAI 進行評分與摘要 (自動繁體中文輸出)"""
    
    if is_foreign:
        prompt = f"""
        這是一篇外國英文新聞標題：
        標題：{title}
        連結：{link}

        請將標題與內容理解後，【完全使用繁體中文】輸出以下格式：
        【中文翻譯標題】：請將原標題翻譯成流暢的繁體中文
        【重要程度】：1 到 5 顆星（例如：⭐⭐⭐⭐）
        【繁體中文摘要】：用 60 字以內摘要這篇新聞的核心重點與影響。
        """
    else:
        prompt = f"""
        請閱讀以下新聞標題並進行分析：
        標題：{title}
        連結：{link}

        請使用繁體中文輸出以下格式：
        【重要程度】：1 到 5 顆星（例如：⭐⭐⭐⭐）
        【一句話摘要】：用 50 字以內摘要這篇新聞的核心內容。
        """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一位專業的半導體與科技財經新聞分析師，請一律使用繁體中文回答。"},
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
    final_report = "📰 **每日產業與投資情報摘要**\n\n"
    
    # 1. 處理中文新聞
    if ZH_KEYWORDS:
        final_report += "🇹🇼 **【台股供應鏈焦點】**\n"
        for kw in ZH_KEYWORDS:
            final_report += f"🔍 關鍵字：{kw}\n"
            articles = fetch_google_news(kw, lang="zh-TW")
            
            if not articles:
                final_report += "今日無相關新聞。\n\n"
                continue
                
            for i, article in enumerate(articles, 1):
                analysis = analyze_with_ai(article.title, article.link, is_foreign=False)
                final_report += f"\n{i}. [{article.title}]({article.link})\n"
                final_report += f"{analysis}\n"
                final_report += "---------------------\n"
            final_report += "\n"

    # 2. 處理英文新聞
    if EN_KEYWORDS:
        final_report += "🌎 **【國際外電與前瞻科技】**\n"
        for kw in EN_KEYWORDS:
            final_report += f"🔍 關鍵字：{kw}\n"
            articles = fetch_google_news(kw, lang="en")
            
            if not articles:
                final_report += "今日無相關外電。\n\n"
                continue
                
            for i, article in enumerate(articles, 1):
                analysis = analyze_with_ai(article.title, article.link, is_foreign=True)
                final_report += f"\n{i}. 原文連結：[點此閱讀文章]({article.link})\n"
                final_report += f"{analysis}\n"
                final_report += "---------------------\n"
            final_report += "\n"
        
    # 發送給 Telegram
    send_telegram_message(final_report)
    print("情報摘要已成功發送！")

if __name__ == "__main__":
    main()
