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
from users.models import UserAddress
from users.forms import UserAddressForm
from .models import Order, Payment
from groups.models import JoinedGroup, Group
from products.models import JoinedGroupProduct
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Sum, F, Q, Prefetch


REQUIRED_ADDR_FIELDS = (
    "recipient_name",
    "phone",
    "postal_code",
    "county",
    "district",
    "road",
    "detail",
)


@login_required
def ship_address(request, order_id):
    addresses = UserAddress.objects.filter(user=request.user).order_by("-is_default")
    default_address = addresses.filter(is_default=True).first()

    # 如果預設地址裡有 None，跳轉到個人頁面請他修改
    default_is_not_complete = any(
        getattr(default_address, field) in (None, "") for field in REQUIRED_ADDR_FIELDS
    )

    if default_is_not_complete:
        messages.warning(request, "請先更新預設地址，再至訂單結帳")
        return redirect("users:profiles")

    order = get_object_or_404(
        Order, pk=order_id, order_status=Order.OrderStatus.PENDING
    )
    blank_address_form = UserAddressForm()

    return render(
        request,
        "orders/ship_address.html",
        {
            "addresses": addresses,
            "order": order,
            "user_address_form": blank_address_form,
            "current_step": 1,
        },
    )


@login_required
def check_order(request, order_id):
    user = request.user
    order = get_object_or_404(
        Order, pk=order_id, user=user, order_status=Order.OrderStatus.PENDING
    )

    # 從新增地址路徑來的
    # 是 GET 、有 address_id
    if request.method == "GET" and request.GET.get("address_id"):
        address_id = request.GET.get("address_id")

    # 從選擇地址路徑來的
    # 是 POST 、有 name = ship-address 的 input
    elif request.method == "POST" and request.POST.get("ship-address"):
        ship_address_val = request.POST.get("ship-address")
        address_id = ship_address_val.replace("address-", "")

    # 都不是，代表沒選地址
    else:
        messages.error(request, "請選擇一個收貨地址")
        return redirect("orders:ship_address", order_id=order_id)

    address = get_object_or_404(UserAddress, pk=address_id, user=user)

    # 檢查這筆地址是否完整
    missing = [field for field in REQUIRED_ADDR_FIELDS if not getattr(address, field)]
    if missing:
        messages.error(request, "這個地址資料不完整，請先進行編輯")
        return redirect("users:profile")

    # 存地址快照
    order.apply_address(address)

    joined_group = (
        JoinedGroup.objects.filter(order=order)
        .prefetch_related("joined_group_products__product")
        .first()
    )
    joined_group_products = joined_group.joined_group_products.all()

    return render(
        request,
        "orders/check_order.html",
        {
            "order": order,
            "joined_group": joined_group,
            "joined_group_products": joined_group_products,
            "current_step": 2,
        },
    )


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
    order = get_object_or_404(Order, pk=order_id)
    if not order.user == request.user:
        messages.error(request, "訂單發生錯誤，請稍後再試")
        return redirect(f"{reverse('orders:my_orders')}?auto_tab=pending")

    if not order.is_pending():
        messages.warning(request, "訂單已付款，請至訂單紀錄查看")
        return redirect(f"{reverse('orders:my_orders')}?auto_tab=processing")

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
            "confirmUrl": f"https://{settings.HOSTNAME}/orders/my-orders/payment/confirm",
            "cancelUrl": f"https://{settings.HOSTNAME}/orders/my-orders/payment/cancel",
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

                payment.mark_as_failed()
                messages.error(request, "付款發生錯誤，請稍後再試")
                return redirect(f"{reverse('orders:my_orders')}?auto_tab=pending")
        else:
            payment.mark_as_failed()
            messages.error(request, "系統發生錯誤，請稍後再試")
            return redirect(f"{reverse('orders:my_orders')}?auto_tab=pending")

    except requests.RequestException:
        # 處理所有網路相關錯誤（連線、超時等）
        payment.mark_as_failed()
        messages.error(request, "網路連線錯誤，請稍後再試")
        return redirect(f"{reverse('orders:my_orders')}?auto_tab=pending")

    except Exception:
        # 處理其他所有錯誤
        payment.mark_as_failed()
        messages.error(request, "取得付款資訊失敗，請稍後再試")
        return redirect(f"{reverse('orders:my_orders')}?auto_tab=pending")


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
        return redirect(f"{reverse('orders:my_orders')}?auto_tab=pending")

    # 檢查 payment 是否已經是 paid 狀態
    if payment.is_paid():
        messages.info(request, "此付款已經完成")
        # TODO 改成導向訂單頁面
        return redirect(f"{reverse('orders:my_orders')}?auto_tab=pending")

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
                return redirect(f"{reverse('orders:my_orders')}?auto_tab=processing")

            else:
                payment.mark_as_failed()
                payment.save()
                messages.error(request, "付款發生錯誤，請稍後再試")
                return redirect("orders:payment_fail")

        else:
            payment.mark_as_failed()
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


# 我跟團的訂單
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
        "orders/my_orders/section.html",
        {
            "orders": orders,
            "joined_groups": joined_groups,
            "current_sub_tab": display_tab,
            "auto_tab": auto_tab,
        },
    )


@login_required
def my_orders_tab_content(request):
    user = request.user
    tab = request.GET.get("tab", "all")

    orders, joined_groups = get_orders_by_tab(user, tab)

    return render(
        request,
        "orders/my_orders/list.html",
        {
            "orders": orders,
            "joined_groups": joined_groups,
            "current_sub_tab": tab,
        },
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
        .annotate(
            total_amount=Sum(
                F('joined_group__joined_group_products__product__price')
                * F('joined_group__joined_group_products__quantity'),
            )
        )
    )

    # 找出所有跟團紀錄
    base_joined_groups = (
        JoinedGroup.objects.filter(
            buyer=user,
            group__status="ongoing",
            deleted_at=None,
        )
        .order_by("-updated_at")
        .select_related("group")
        .prefetch_related(
            Prefetch(
                "joined_group_products",
                queryset=JoinedGroupProduct.objects.filter(
                    deleted_at=None
                ).select_related("product"),
            )
        )
        .annotate(
            total_amount=Sum(
                F('joined_group_products__product__price')
                * F('joined_group_products__quantity'),
                filter=Q(joined_group_products__deleted_at=None),
            )
        )
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


# 我開團的訂單
@login_required
def owned_orders(request):
    user = request.user
    tab = request.GET.get("tab", "all")
    auto_tab = request.GET.get("auto_tab")

    # 如果有 auto_tab，就用 auto_tab 作為初始內容
    display_tab = auto_tab if auto_tab else tab

    ongoing_groups, reached_groups = get_data_by_tab(user, display_tab)

    return render(
        request,
        "orders/owned_orders/section.html",
        {
            "ongoing_groups": ongoing_groups,
            "reached_groups": reached_groups,
            "current_sub_tab": display_tab,
            "auto_tab": auto_tab,
        },
    )


@login_required
def owned_orders_tab_content(request):
    user = request.user
    tab = request.GET.get("tab", "all")

    ongoing_groups, reached_groups = get_data_by_tab(user, tab)

    return render(
        request,
        "orders/owned_orders/list.html",
        {
            "ongoing_groups": ongoing_groups,
            "reached_groups": reached_groups,
            "current_sub_tab": tab,
        },
    )


def get_data_by_tab(user, tab):
    ongoing_groups = []
    reached_groups = []

    base_groups_query = (
        Group.objects.filter(owner=user)
        .order_by("-created_at")
        .select_related("owner")
        .prefetch_related("products", "order_set")
    )

    if tab == "all":
        ongoing_groups = base_groups_query.filter(status="ongoing")
        reached_groups = base_groups_query.filter(status="reached")
    elif tab == "ongoing":
        ongoing_groups = base_groups_query.filter(status="ongoing")
    elif tab == "reached":
        reached_groups = base_groups_query.filter(status="reached")
    return ongoing_groups, reached_groups


# 跟團者列表
@login_required
def buyer_list(request, group_id):
    group = get_object_or_404(Group, id=group_id, owner=request.user)

    orders = []
    buyers = []

    all_orders = (
        Order.objects.filter(
            group_id=group_id, group__status="reached"
        )
        .prefetch_related(
            "joined_group__joined_group_products__product",
        )
        .annotate(
            total_amount=Sum(
                F('joined_group__joined_group_products__product__price')
                * F('joined_group__joined_group_products__quantity')
            )
        )
    )

    ongoing_groups = (
        JoinedGroup.objects.filter(group_id=group_id, group__status="ongoing")
        .select_related("buyer")
        .prefetch_related(
            "joined_group_products__product",
        )
        .annotate(
            total_amount=Sum(
                F('joined_group_products__product__price')
                * F('joined_group_products__quantity')
            )
        )
    )

    

    if group.status == "ongoing":
        # 團購進行中，顯示跟團者
        buyers = ongoing_groups
    else:
        # 團購已達標或其他狀態，顯示訂單
        orders = all_orders


    return render(
        request,
        "orders/owned_orders/buyers_list.html",
        {'group': group, 'orders': orders, 'buyers': buyers},
    )


# 確認收貨
@login_required
@require_POST
def received(request, order_id):
    user = request.user
    order = get_object_or_404(Order, user=user, pk=order_id)

    if order.order_status == Order.OrderStatus.COMPLETED:
        messages.info(request, "此訂單已完成，無需重複確認收貨")
        return redirect(f"{reverse('orders:my_orders')}?auto_tab=completed")

    if not order.is_shipped():
        messages.error(request, "此訂單無法確認收貨")
        return redirect(f"{reverse('orders:my_orders')}?auto_tab=shipped")

    order.mark_as_completed()
    order.save()

    messages.success(request, "訂單已確認收貨")
    return redirect(f"{reverse('orders:my_orders')}?auto_tab=completed")


# 確認出貨
@login_required
@require_POST
def shipped(request, order_id):
    order = get_object_or_404(Order, pk=order_id, group__owner=request.user)

    if order.order_status == Order.OrderStatus.SHIPPED:
        messages.info(request, "此訂單已出貨，無需重複確認出貨")
        return redirect('orders:buyer_list', group_id=order.group.id)

    if not order.is_processing():
        messages.error(request, "此訂單無法確認出貨")
        return redirect('orders:buyer_list', group_id=order.group.id)

    order.mark_as_shipped()
    order.save()

    messages.success(request, "訂單已確認出貨")
    return redirect('orders:buyer_list', group_id=order.group.id)