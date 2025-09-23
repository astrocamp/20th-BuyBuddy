import sys
import os 
from flask import Flask, request, jsonify
from groups.services.scraper_service import scrape_product_url_sync
import django
import logging


project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
	sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BuyBuddy.settings')
django.setup()

logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/scrape", methods=["POST"])
def handle_scrape_request():
	request_data = request.get_json()
	if not request_data or "url" not in request_data:
		logger.warning("請求中缺少 'url' 參數")
		return jsonify({"success": False, "error": "請求中缺少 'url' 參數"}), 400
	
	url_to_scrape = request_data["url"]
	logger.info(f"--- [Local Worker] 收到爬取任務: {url_to_scrape} ---")

	try:
		scrape_result = scrape_product_url_sync(url_to_scrape)

		logger.info(f"--- [Local Worker] 爬取完成，返回 JSON 結果 ---")
		return jsonify(scrape_result)
	
	except Exception as e:
		logger.exception(f"--- [Local Worker] 爬取過程中發生錯誤: {e} ---")
		return jsonify({"success": False, "error": f"爬取失敗: {str(e)}"}), 500

if __name__ == "__main__":
	logger.info("--- [Local Worker] 啟動中，監聽 http://127.0.0.1:5000 ---")
	app.run(host="0.0.0.0", port=5001)





		

