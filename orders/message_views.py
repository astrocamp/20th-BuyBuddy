from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Order, OrderMessage
from groups.models import Group


def get_order_messages(order):
    order_messages = (
        OrderMessage.objects.filter(order=order)
        .order_by("created_at")
        .select_related("sender")
    )

    joined_group_products = order.joined_group.joined_group_products.select_related(
        "product"
    ).all()

    return order_messages, joined_group_products


@login_required
def order_messages(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("group"), pk=order_id, user=request.user
    )

    order_messages, joined_group_products = get_order_messages(order)

    return render(
        request,
        "orders/messages/section.html",
        {
            "order_messages": order_messages,
            "order": order,
            "joined_group_products": joined_group_products,
        },
    )


@login_required
def group_owner_order_messages(request, order_id):
    order = get_object_or_404(Order.objects.select_related("group"), pk=order_id)
    get_object_or_404(Group, pk=order.group_id, owner=request.user)

    order_messages, joined_group_products = get_order_messages(order)

    return render(
        request,
        "orders/messages/section.html",
        {
            "order_messages": order_messages,
            "order": order,
            "joined_group_products": joined_group_products,
        },
    )


def create_message(sender, receiver, content, order):
    new_message = OrderMessage.objects.create(
        sender=sender,
        receiver=receiver,
        content=content,
        order=order,
    )
    return new_message


@login_required
@require_POST
def send_message(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("group", "user"), pk=order_id
    )
    group = order.group

    message_content = request.POST.get("message_content")
    update_message = False

    if message_content.strip():
        # 跟團者或開團主新增留言
        if order.user == request.user:
            create_message(request.user, group.owner, message_content, order)
            update_message = True
        elif group.owner == request.user:
            create_message(request.user, order.user, message_content, order)
            update_message = True
        else:
            messages.warning(request, "新增留言錯誤")
            return redirect("orders:my_orders")

    else:
        messages.warning(request, "留言內容不可為空")

    # 重查所有訊息，用 OOB
    order_messages = (
        OrderMessage.objects.filter(order=order)
        .order_by("created_at")
        .select_related("sender")
    )

    context = {
        "order_messages": order_messages,
        "partial_msg_show": True,
        "update_message": update_message,
    }

    return render(
        request,
        "orders/messages/messages_board_partial.html",
        context,
    )
