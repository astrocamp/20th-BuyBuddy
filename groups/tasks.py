from BuyBuddy.celery_app import app
from django.utils import timezone
from groups.models import Group
import logging

@app.task
def check_deadline():
	try:
		expired_groups = Group.objects.filter(deadline__lt=timezone.now(), status="ongoing")
		updated_count = expired_groups.update(status="failed")
		return f"總共更新 {updated_count} 筆過期資料"
		
	except Exception as e:
		logging.getLogger(__name__).exception("執行 check_deadline 任務時發生錯誤")
		return f"執行失敗: {str(e)}"