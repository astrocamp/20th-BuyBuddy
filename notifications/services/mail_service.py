from django.urls import reverse
from anymail.message import AnymailMessage
from django.conf import settings


def send_email_notification(email, group, status):
    try:
        # TODO 需組裝團購頁面連結
        group_url = f"{settings.SITE_URL}{reverse('pages:homepage')}"

        # 使用 anymail 發送模板郵件
        mail = AnymailMessage(
            template_id="團主通知信",
            to=[email],
        )

        # 設定模板變數
        mail.merge_global_data = {
            "group_url": group_url,
            "group_name": group.name,
            "group_status": status,
        }

        mail.send()

    except Exception as e:
        print(e, "團主通知信發送失敗")


def send_bulk_email_notifications(emails, group, status):
    try:
        # TODO 需組裝團購頁面連結
        group_url = f"{settings.SITE_URL}{reverse('pages:homepage')}"

        # 使用 anymail 發送模板郵件
        mail = AnymailMessage(
            template_id="跟團者通知信",
            to=emails,
        )

        # 設定模板變數
        mail.merge_global_data = {
            "group_url": group_url,
            "group_name": group.name,
            "group_status": status,
        }

        mail.send()

    except Exception as e:
        print(e, "跟團者通知信發送失敗")
