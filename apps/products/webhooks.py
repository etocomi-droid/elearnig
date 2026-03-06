import logging

import stripe
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.contacts.models import Contact, ContactTag, ActivityLog
from apps.emails.models import ScenarioSubscription
from apps.members.models import Enrollment
from apps.products.models import Order

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
@require_POST
def stripe_webhook_view(request):
    """Stripe Webhook エンドポイント"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        logger.error('Stripe webhook: Invalid payload')
        return HttpResponseBadRequest('Invalid payload')
    except stripe.error.SignatureVerificationError:
        logger.error('Stripe webhook: Invalid signature')
        return HttpResponseBadRequest('Invalid signature')

    # イベントタイプに応じた処理
    if event['type'] == 'checkout.session.completed':
        _handle_checkout_session_completed(event['data']['object'])
    else:
        logger.info(f'Stripe webhook: Unhandled event type: {event["type"]}')

    return HttpResponse(status=200)


def _handle_checkout_session_completed(session):
    """checkout.session.completed イベント処理"""
    metadata = session.get('metadata', {})
    order_id = metadata.get('order_id')
    contact_id = metadata.get('contact_id')

    if not order_id or not contact_id:
        logger.warning(f'Stripe webhook: Missing metadata in session {session.get("id")}')
        return

    # Order を取得して completed に更新
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f'Stripe webhook: Order {order_id} not found')
        return

    order.status = 'completed'
    order.stripe_payment_intent_id = session.get('payment_intent', '') or ''
    order.completed_at = timezone.now()
    order.save(update_fields=['status', 'stripe_payment_intent_id', 'completed_at'])

    # Contact を取得
    try:
        contact = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        logger.error(f'Stripe webhook: Contact {contact_id} not found')
        return

    # OrderItem ごとに購入後アクションを実行
    for item in order.items.select_related('product').all():
        product = item.product
        _execute_post_purchase_actions(contact, product)

    # ActivityLog に購入を記録
    product_names = [
        item.product.name for item in order.items.select_related('product').all()
    ]
    ActivityLog.objects.create(
        contact=contact,
        action='purchase',
        detail={
            'order_id': order.id,
            'total_amount': order.total_amount,
            'products': product_names,
            'stripe_session_id': session.get('id', ''),
        },
    )

    logger.info(f'Stripe webhook: Order {order_id} completed successfully')


def _execute_post_purchase_actions(contact, product):
    """購入後アクションを実行"""

    # grant_course: コースへのアクセス権付与
    if product.grant_course:
        Enrollment.objects.get_or_create(
            contact=contact,
            course=product.grant_course,
        )
        logger.info(
            f'Post-purchase: Enrolled contact {contact.id} '
            f'in course {product.grant_course.id}'
        )

    # add_tag: タグ付与
    if product.add_tag:
        ContactTag.objects.get_or_create(
            contact=contact,
            tag=product.add_tag,
        )
        logger.info(
            f'Post-purchase: Added tag {product.add_tag.id} '
            f'to contact {contact.id}'
        )

    # start_scenario: シナリオ開始
    if product.start_scenario:
        ScenarioSubscription.objects.get_or_create(
            contact=contact,
            scenario=product.start_scenario,
            defaults={
                'current_step': 0,
                'is_active': True,
            },
        )
        logger.info(
            f'Post-purchase: Started scenario {product.start_scenario.id} '
            f'for contact {contact.id}'
        )
