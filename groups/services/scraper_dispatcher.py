import os
import requests
from typing import Dict, Any
from .scraper_service import scrape_product_url_sync as local_scraper_sync


def scrape_product(url: str) -> Dict[str, Any]:
    worker_url = os.getenv("SCRAPER_WORKER_URL")
    if not worker_url:
        # 備用方案：如果沒有設定 worker URL，就在 EC2 本地執行
        print("未設定 SCRAPER_WORKER_URL，將在本地 (EC2) 執行爬蟲")
        return local_scraper_sync(url)
        # 主要方案：將任務委派給遠端的地端 worker
    print(f"將爬取任務轉發至地端 Worker: {url}")
    try:
        response = requests.post(
            f"{worker_url}/scrape",
            json={"url": url},
            timeout=300,  # 等待 5 分鐘
        )
        response.raise_for_status()  # 如果狀態碼是 4xx 或 5xx，會拋出異常
        return response.json()
    except requests.RequestException as e:
        return {"success": False, "error": f"呼叫地端 Worker 失敗: {str(e)}"}
