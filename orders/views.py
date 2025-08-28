from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
import uuid
import json
import hmac
import hashlib
import base64
import requests
from groups.models import Group, JoinedGroup
from .models import Order
from django.contrib.auth.decorators import login_required


def create_headers(body, uri):

    nonce = str(uuid.uuid4())
    secret_key = settings.LINE_CHANNEL_SECRET_KEY
    body_to_json = json.dumps(body)
    message = secret_key + uri + body_to_json + nonce

    binary_message = message.encode()
    binary_secret_key = secret_key.encode()

    signature_hash = hmac.new(binary_secret_key, binary_message, hashlib.sha256)
    signature = base64.b64encode(signature_hash.digest()).decode()

    headers = {
        "Content-Type": "application/json",
        "X-LINE-ChannelId": settings.LINE_CHANNEL_ID,
        "X-LINE-Authorization-Nonce": nonce,
        "X-LINE-Authorization": signature,
    }

    return headers


@require_POST
@login_required
def request(request, order_id):
    user = request.user

    order = get_object_or_404(Order, user=user, pk=order_id)

    if order.payment_status == order.PaymentStatus.PAID:
        messages.warning(request, "訂單已付款，請至訂單紀錄查看")
        return redirect("orders:paid")

    order.generate_order_number()
    package_id = f"pkg_{order.number}_{str(uuid.uuid4())[:8]}"

    payload = {
        "amount": int(order.amount),
        "currency": order.currency,
        "orderId": order.number,
        "packages": [
            {
                "id": package_id,
                "amount": int(order.amount),
                "products": [
                    {
                        "name": f"{order.group.name} - 訂單",
                        "quantity": 1,
                        "price": int(order.amount),
                    }
                ],
            }
        ],
        "redirectUrls": {
            "confirmUrl": f"https://{settings.HOSTNAME}/orders/payment/confirm",
            "cancelUrl": f"https://{settings.HOSTNAME}/orders/payment/cancel",
        },
    }

    signature_uri = settings.LINE_SIGNATURE_REQUEST_URI
    headers = create_headers(payload, signature_uri)
    body = json.dumps(payload)
    url = f"{settings.LINE_SANDBOX_URL}{settings.LINE_SIGNATURE_REQUEST_URI}"

    try:
        response = requests.post(url, headers=headers, data=body, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data["returnCode"] == "0000":
                return redirect(data["info"]["paymentUrl"]["web"])

            else:
                # DEVLOG: 印出錯誤
                error_code = data.get("returnCode")
                error_msg = data.get("returnMessage", "未知錯誤")
                print(f"❌ LINE Pay Error: {error_code} - {error_msg}")

                order.mark_payment_failed()
                messages.error(request, "付款發生錯誤，請稍後再試")
                return render(request, "orders/checkout.html")
        else:
            order.mark_payment_failed()
            messages.error(request, "系統發生錯誤，請稍後再試")
            return render(request, "orders/checkout.html")

    except requests.RequestException:
        # 處理所有網路相關錯誤（連線、超時等）
        order.mark_payment_failed()
        messages.error(request, "網路連線錯誤，請稍後再試")
        return render(request, "orders/checkout.html")

    except Exception:
        # 處理其他所有錯誤
        order.mark_payment_failed()
        messages.error(request, "取得付款資訊失敗，請稍後再試")
        return render(request, "orders/checkout.html")


def confirm(request):
    transaction_id = request.GET.get("transactionId")
    order_id = request.GET.get("orderId")

    if not transaction_id or not order_id:
        messages.error(request, "付款發生錯誤，缺少必要付款資訊")
        return render(request, "orders/payment_fail.html")

    order = get_object_or_404(Order, number=order_id)

    payload = {
        "amount": int(order.amount),
        "currency": order.currency,
    }

    signature_uri = f"/v3/payments/{transaction_id}/confirm"
    headers = create_headers(payload, signature_uri)
    url = f"{settings.LINE_SANDBOX_URL}/v3/payments/{transaction_id}/confirm"
    body = json.dumps(payload)

    try:
        response = requests.post(url, headers=headers, data=body, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["returnCode"] == "0000":
                if order.mark_as_paid():
                    return render(request, "orders/payment_success.html")
                else:
                    messages.error(request, "訂單狀態異常，可能重複付款")
                    return render(request, "orders/payment_fail.html")
            else:
                order.mark_payment_failed()
                messages.error(request, "付款發生錯誤，請稍後再試")
                return render(request, "orders/payment_fail.html")
        else:
            order.mark_payment_failed()
            messages.error(request, "系統發生錯誤，請稍後再試")
            return render(request, "orders/payment_fail.html")

    except requests.RequestException:
        order.mark_payment_failed()
        messages.error(request, "網路連線錯誤，請稍後再試")
        return render(request, "orders/payment_fail.html")

    except Exception:
        order.mark_payment_failed()
        messages.error(request, "付款確認失敗，請稍後再試")
        return render(request, "orders/payment_fail.html")


def cancel(request):
    return render(request, "orders/payment_cancel.html")


# 全部跟團訂單
@login_required
def my_orders(request):
    # 找出使用者
    user = request.user

    # 找出所有跟團紀錄
    joined_groups = (
        JoinedGroup.objects.filter(buyer=user, group__status="ongoing")
        .select_related("group")
        .order_by("-updated_at")
        .prefetch_related("joined_group_products__product")
    )

    # 找出所有訂單
    orders = (
        Order.objects.filter(user=user)
        .order_by("-created_at")
        .select_related("group", "joined_group")
        .prefetch_related("joined_group__joined_group_products__product")
    )

    return render(
        request,
        "orders/my_orders.html",
        {"orders": orders, "joined_groups": joined_groups},
    )


# 未成團
@login_required
def ongoing(request):
    # 找出使用者
    user = request.user

    # 找出所有跟團且未成團紀錄
    joined_groups = (
        JoinedGroup.objects.filter(buyer=user, group__status="ongoing")
        .select_related("group")
        .order_by("-updated_at")
        .prefetch_related("joined_group_products__product")
    )

    return render(
        request,
        "orders/ongoing_orders.html",
        {"joined_groups": joined_groups},
    )


# 待付款
@login_required
def pending(request):
    # 找出使用者
    user = request.user
    # 找出待付款訂單
    orders = (
        Order.objects.filter(user=user, payment_status=Order.PaymentStatus.PENDING)
        .order_by("-created_at")
        .select_related("group", "joined_group")
        .prefetch_related("joined_group__joined_group_products__product")
    )

    return render(
        request,
        "orders/pending_orders.html",
        {"orders": orders},
    )


# 已付款待出貨
@login_required
def paid(request):
    # 找出使用者
    user = request.user
    # 找出所有訂單
    orders = (
        Order.objects.filter(
            user=user,
            payment_status=Order.PaymentStatus.PAID,
            order_status=Order.OrderStatus.PROCESSING,
        )
        .order_by("-created_at")
        .select_related("group", "joined_group")
        .prefetch_related("joined_group__joined_group_products__product")
    )

    return render(
        request,
        "orders/paid_orders.html",
        {"orders": orders},
    )


# 已出貨
@login_required
def shipped(request):
    # 找出使用者
    user = request.user
    # 找出所有訂單
    orders = (
        Order.objects.filter(
            user=user,
            payment_status=Order.PaymentStatus.PAID,
            order_status=Order.OrderStatus.SHIPPED,
        )
        .order_by("-created_at")
        .select_related("group", "joined_group")
        .prefetch_related("joined_group__joined_group_products__product")
    )

    return render(
        request,
        "orders/shipped_orders.html",
        {"orders": orders},
    )


# 已完成
@login_required
def completed(request):
    # 找出使用者
    user = request.user
    # 找出所有訂單
    orders = (
        Order.objects.filter(
            user=user,
            payment_status=Order.PaymentStatus.PAID,
            order_status=Order.OrderStatus.COMPLETED,
        )
        .order_by("-created_at")
        .select_related("group", "joined_group")
        .prefetch_related("joined_group__joined_group_products__product")
    )

    return render(
        request,
        "orders/completed_orders.html",
        {"orders": orders},
    )


# 確認收貨
@login_required
@require_POST
def received(request, order_id):
    # 找出使用者
    user = request.user

    # 找出訂單
    order = get_object_or_404(Order, user=user, pk=order_id)

    if order.mark_as_completed():
        messages.success(request, "訂單已確認收貨")
    else:
        messages.error(request, "無法確認收貨，訂單狀態不正確")

    return redirect("orders:completed")
