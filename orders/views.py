from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from dotenv import load_dotenv
from django.contrib import messages
import os
import uuid
import json
import hmac
import hashlib
import base64
import requests

load_dotenv()


def checkout(request):
    return render(request, "orders/checkout.html")


def create_headers(body, uri):

    nonce = str(uuid.uuid4())
    secret_key = os.getenv("LINE_CHANNEL_SECRET_KEY")
    body_to_json = json.dumps(body)
    message = secret_key + uri + body_to_json + nonce

    binary_message = message.encode()
    binary_secret_key = secret_key.encode()

    hash = hmac.new(binary_secret_key, binary_message, hashlib.sha256)
    signature = base64.b64encode(hash.digest()).decode()

    headers = {
        "Content-Type": "application/json",
        "X-LINE-ChannelId": os.getenv("LINE_CHANNEL_ID"),
        "X-LINE-Authorization-Nonce": nonce,
        "X-LINE-Authorization": signature,
    }

    return headers


@require_POST
def request(request):
    order_id = f"order_{str(uuid.uuid4())}"
    package_id = f"package_{str(uuid.uuid4())}"

    payload = {
        "amount": 100,
        "currency": "TWD",
        "orderId": order_id,
        "packages": [
            {
                "id": package_id,
                "amount": 100,
                "products": [
                    {"id": 1, "name": "測試商品", "quantity": 1, "price": 100}
                ],
            }
        ],
        "redirectUrls": {
            "confirmUrl": f"https://{os.getenv('HOSTNAME')}/orders/payment/confirm",
            "cancelUrl": f"https://{os.getenv('HOSTNAME')}/orders/payment/cancel",
        },
    }

    signature_uri = os.getenv("LINE_SIGNATURE_REQUEST_URI")
    headers = create_headers(payload, signature_uri)
    body = json.dumps(payload)
    url = f"{os.getenv('LINE_SANDBOX_URL')}{os.getenv('LINE_SIGNATURE_REQUEST_URI')}"

    try:
        response = requests.post(url, headers=headers, data=body)

        if response.status_code == 200:
            data = response.json()
            if data["returnCode"] == "0000":
                return redirect(data["info"]["paymentUrl"]["web"])
            else:
                messages.error(request, "付款發生錯誤，請稍後再試")
                return render(request, "orders/checkout.html")
        else:
            messages.error(request, "系統發生錯誤，請稍後再試")
            return render(request, "orders/checkout.html")

    except Exception:
        messages.error(request, "取得付款資訊失敗，請稍後再試")
        return render(request, "orders/checkout.html")


def confirm(request):
    transaction_id = request.GET.get("transactionId")
    order_id = request.GET.get("orderId")

    if not transaction_id or not order_id:
        messages.error(request, "付款發生錯誤，缺少必要付款資訊")
        return render(request, "orders/payment_fail.html")

    payload = {
        "amount": 100,
        "currency": "TWD",
    }

    signature_uri = f"/v3/payments/{transaction_id}/confirm"
    headers = create_headers(payload, signature_uri)
    url = f"{os.getenv('LINE_SANDBOX_URL')}/v3/payments/{transaction_id}/confirm"
    body = json.dumps(payload)

    try:
        response = requests.post(url, headers=headers, data=body)
        if response.status_code == 200:
            data = response.json()
            if data["returnCode"] == "0000":
                return render(request, "orders/payment_success.html")
            else:
                messages.error(request, "付款發生錯誤，請稍後再試")
                return render(request, "orders/payment_fail.html")
        else:
            messages.error(request, "系統發生錯誤，請稍後再試")
            return render(request, "orders/payment_fail.html")

    except Exception:
        messages.error(request, "付款發生錯誤，請稍後再試")
        return render(request, "orders/payment_fail.html")


def cancel(request):
    return render(request, "orders/payment_cancel.html")
