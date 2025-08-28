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
from .models import Order, Payment
from groups.models import JoinedGroup
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
    order = get_object_or_404(Order, pk=order_id)

    if not order.user == user:
        messages.error(request, "訂單發生錯誤，請稍後再試")
        return redirect("groups:index")

    if not order.is_pending():
        messages.warning(request, "訂單已付款，請至訂單紀錄查看")
        return redirect("orders:paid")

    payment = Payment.objects.create(order=order)

    package_id = f"pkg_{order.order_number}_{str(uuid.uuid4())[:8]}"

    payload = {
        "amount": int(order.amount),
        "currency": order.currency,
        "orderId": payment.payment_number,
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
                # TODO 改成導向訂單頁面
                return redirect("orders:pending")
        else:
            order.mark_payment_failed()
            messages.error(request, "系統發生錯誤，請稍後再試")
            return redirect("orders:pending")

    except requests.RequestException:
        # 處理所有網路相關錯誤（連線、超時等）
        order.mark_payment_failed()
        messages.error(request, "網路連線錯誤，請稍後再試")
        return redirect("orders:pending")

    except Exception:
        # 處理其他所有錯誤
        order.mark_payment_failed()
        messages.error(request, "取得付款資訊失敗，請稍後再試")
        return redirect("orders:pending")


def confirm(request):
    transaction_id = request.GET.get("transactionId")
    payment_number = request.GET.get("orderId")
    payment = get_object_or_404(Payment, payment_number=payment_number)

    if not transaction_id or not payment_number:
        payment.mark_as_failed()
        payment.save()
        messages.error(request, "付款發生錯誤，缺少必要付款資訊")
        return redirect("orders:payment_fail")

    order = payment.order

    # 檢查訂單是否是 pending 以外狀態
    if not order.is_pending():
        messages.info(request, "此訂單已經付款完成")
        # TODO 改成導向訂單頁面
        return redirect("orders:processing")

    # 檢查 payment 是否已經是 paid 狀態
    if payment.is_paid():
        messages.info(request, "此付款已經完成")
        # TODO 改成導向訂單頁面
        return redirect("orders:processing")

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
                payment.mark_as_paid()
                payment.save()
                order.mark_as_processing()
                order.save()
                messages.success(request, "付款成功，請至訂單頁面查看")
                return redirect("orders:processing")

            else:
                payment.mark_as_failed()
                payment.save()
                messages.error(request, "付款發生錯誤，請稍後再試")
                return redirect("orders:payment_fail")

        else:
            order.mark_payment_failed()
            messages.error(request, "系統發生錯誤，請稍後再試")
            return redirect("orders:payment_fail")

    except requests.RequestException:
        payment.mark_as_failed()
        payment.save()
        messages.error(request, "網路連線錯誤，請稍後再試")
        return redirect("orders:payment_fail")

    except Exception:
        payment.mark_as_failed()
        payment.save()
        messages.error(request, "付款確認失敗，請稍後再試")
        return redirect("orders:payment_fail")


def cancel(request):
    return render(request, "orders/payment_cancel.html")


def success(request):
    return render(request, "orders/payment_success.html")


def fail(request):
    return render(request, "orders/payment_fail.html")


@login_required
def my_orders(request):
    user = request.user
    tab = request.GET.get("tab", "all")
    auto_tab = request.GET.get("auto_tab")

    # 如果有 auto_tab，就用 auto_tab 作為初始內容
    display_tab = auto_tab if auto_tab else tab

    orders, joined_groups = get_orders_by_tab(user, display_tab)

    return render(
        request,
        "orders/my_orders/my_orders_section.html",
        {
            "orders": orders,
            "joined_groups": joined_groups,
            "current_tab": display_tab,
            "auto_tab": auto_tab,
        },
    )


@login_required
def my_orders_tab_content(request):
    print("123")
    user = request.user
    tab = request.GET.get("tab", "all")

    orders, joined_groups = get_orders_by_tab(user, tab)

    return render(
        request,
        "orders/my_orders/my_orders_list.html",
        {"orders": orders, "joined_groups": joined_groups},
    )


def get_orders_by_tab(user, tab):
    orders = []
    joined_groups = []

    # 找出所有訂單
    base_orders_query = (
        Order.objects.filter(user=user)
        .order_by("-updated_at")
        .select_related("group", "joined_group")
        .prefetch_related("joined_group__joined_group_products__product")
    )

    # 找出所有跟團紀錄
    base_joined_groups = (
        JoinedGroup.objects.filter(buyer=user, group__status="ongoing", deleted_at=None)
        .order_by("-updated_at")
        .select_related("group")
        .prefetch_related("joined_group_products__product")
    )

    if tab == "all":
        orders = base_orders_query.all()
        joined_groups = base_joined_groups.all()

    elif tab == "ongoing":
        joined_groups = base_joined_groups.all()

    elif tab == "pending":
        orders = base_orders_query.filter(order_status=Order.OrderStatus.PENDING)

    elif tab == "processing":
        orders = base_orders_query.filter(order_status=Order.OrderStatus.PROCESSING)

    elif tab == "shipped":
        orders = base_orders_query.filter(order_status=Order.OrderStatus.SHIPPED)

    elif tab == "completed":
        orders = base_orders_query.filter(order_status=Order.OrderStatus.COMPLETED)

    return orders, joined_groups


# 確認收貨
@login_required
@require_POST
def received(request, order_id):
    user = request.user
    order = get_object_or_404(Order, user=user, pk=order_id)

    if not order.is_shipped():
        messages.error(request, "此訂單無法確認收貨")
        return redirect("/orders/my-orders/?auto_tab=shipped")

    order.mark_as_completed()
    order.save()

    messages.success(request, "訂單已確認收貨")
    return redirect("/orders/my-orders/?auto_tab=completed")
