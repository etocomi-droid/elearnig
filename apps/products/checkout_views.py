import stripe
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest

from apps.contacts.models import Contact
from apps.products.models import Product, Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


def checkout_create_view(request, product_id):
    """Stripe Checkout セッション作成"""
    if request.method != 'POST':
        return HttpResponseBadRequest('POST method required.')

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    project = product.project

    email = request.POST.get('email', '').strip()
    name = request.POST.get('name', '').strip()

    if not email:
        return HttpResponseBadRequest('メールアドレスは必須です。')

    # Contact を取得または作成
    contact, created = Contact.objects.get_or_create(
        project=project,
        email=email,
        defaults={'name': name},
    )
    if not created and name and not contact.name:
        contact.name = name
        contact.save(update_fields=['name'])

    # Order を pending で作成
    order = Order.objects.create(
        project=project,
        contact=contact,
        status='pending',
        total_amount=product.price,
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        price=product.price,
        quantity=1,
    )

    # Stripe Checkout Session 作成
    success_url = request.build_absolute_uri('/checkout/success/') + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = request.build_absolute_uri('/checkout/cancel/')

    session_params = {
        'payment_method_types': ['card'],
        'customer_email': email,
        'metadata': {
            'order_id': str(order.id),
            'contact_id': str(contact.id),
            'project_id': str(project.id),
        },
        'success_url': success_url,
        'cancel_url': cancel_url,
    }

    if product.product_type == 'subscription' and product.billing_interval:
        # サブスクリプション
        session_params['mode'] = 'subscription'
        session_params['line_items'] = [{
            'price_data': {
                'currency': 'jpy',
                'unit_amount': product.price,
                'recurring': {
                    'interval': product.billing_interval,
                },
                'product_data': {
                    'name': product.name,
                    'description': product.description or product.name,
                },
            },
            'quantity': 1,
        }]
    else:
        # 単品購入
        session_params['mode'] = 'payment'
        session_params['line_items'] = [{
            'price_data': {
                'currency': 'jpy',
                'unit_amount': product.price,
                'product_data': {
                    'name': product.name,
                    'description': product.description or product.name,
                },
            },
            'quantity': 1,
        }]

    # Stripe Price ID が設定済みならそちらを使用
    if product.stripe_price_id:
        session_params['line_items'] = [{
            'price': product.stripe_price_id,
            'quantity': 1,
        }]

    try:
        session = stripe.checkout.Session.create(**session_params)
    except stripe.error.StripeError as e:
        order.status = 'cancelled'
        order.save(update_fields=['status'])
        return render(request, 'products/checkout_error.html', {
            'error_message': str(e),
        })

    # セッションIDを保存
    order.stripe_session_id = session.id
    order.save(update_fields=['stripe_session_id'])

    return redirect(session.url)


def checkout_success_view(request):
    """決済成功ページ"""
    session_id = request.GET.get('session_id', '')
    return render(request, 'products/checkout_success.html', {
        'session_id': session_id,
    })


def checkout_cancel_view(request):
    """決済キャンセルページ"""
    return render(request, 'products/checkout_cancel.html')
