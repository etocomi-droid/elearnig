import logging
from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.contacts.models import ActivityLog
from apps.emails.models import ScenarioSubscription, ScenarioStep, EmailLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'シナリオメールの配信処理を実行します。cronやCelery Beatで定期実行してください。'

    def handle(self, *args, **options):
        now = timezone.now()
        sent_count = 0
        failed_count = 0
        completed_count = 0

        # アクティブな購読を取得
        active_subscriptions = (
            ScenarioSubscription.objects
            .filter(is_active=True, scenario__is_active=True)
            .select_related('scenario', 'contact')
        )

        for subscription in active_subscriptions:
            # 現在のステップの次のステップを取得
            next_step_number = subscription.current_step + 1
            try:
                next_step = ScenarioStep.objects.get(
                    scenario=subscription.scenario,
                    step_number=next_step_number,
                    is_active=True,
                )
            except ScenarioStep.DoesNotExist:
                # 次のアクティブなステップが無い場合、完了済みとしてマーク
                subscription.is_active = False
                subscription.save()
                completed_count += 1
                self.stdout.write(
                    f'  Subscription {subscription.pk} completed '
                    f'(contact={subscription.contact.email}, '
                    f'scenario={subscription.scenario.name})'
                )
                continue

            # 配信タイミングの計算
            # subscribed_at からの累積遅延を計算（前のステップの遅延も合算）
            total_delay = timedelta()
            preceding_steps = ScenarioStep.objects.filter(
                scenario=subscription.scenario,
                step_number__lte=next_step_number,
                is_active=True,
            ).order_by('step_number')

            for step in preceding_steps:
                total_delay += timedelta(days=step.delay_days, hours=step.delay_hours)

            scheduled_time = subscription.subscribed_at + total_delay

            if scheduled_time > now:
                # まだ配信タイミングではない
                continue

            # 既に送信済みかチェック
            already_sent = EmailLog.objects.filter(
                contact=subscription.contact,
                scenario_step=next_step,
                email_type='scenario',
                status='sent',
            ).exists()

            if already_sent:
                # 既送信済みならステップを進める
                subscription.current_step = next_step_number
                subscription.save()
                continue

            # メール送信
            contact = subscription.contact
            try:
                send_mail(
                    subject=next_step.subject,
                    message=next_step.body_text or '',
                    from_email=None,  # settings.DEFAULT_FROM_EMAIL を使用
                    recipient_list=[contact.email],
                    html_message=next_step.body_html,
                    fail_silently=False,
                )

                # EmailLog に記録
                EmailLog.objects.create(
                    contact=contact,
                    subject=next_step.subject,
                    email_type='scenario',
                    status='sent',
                    scenario_step=next_step,
                )

                # アクティビティログに記録
                ActivityLog.objects.create(
                    contact=contact,
                    action='scenario_email_sent',
                    detail={
                        'scenario_id': subscription.scenario.pk,
                        'scenario_name': subscription.scenario.name,
                        'step_number': next_step.step_number,
                        'subject': next_step.subject,
                    },
                )

                # ステップを進める
                subscription.current_step = next_step_number
                subscription.save()

                sent_count += 1
                self.stdout.write(
                    f'  Sent step {next_step_number} to {contact.email} '
                    f'(scenario: {subscription.scenario.name})'
                )

                # 最後のステップかチェック
                has_more_steps = ScenarioStep.objects.filter(
                    scenario=subscription.scenario,
                    step_number__gt=next_step_number,
                    is_active=True,
                ).exists()

                if not has_more_steps:
                    subscription.is_active = False
                    subscription.save()
                    completed_count += 1
                    self.stdout.write(
                        f'  Subscription {subscription.pk} completed '
                        f'(all steps done)'
                    )

            except Exception as e:
                # 送信失敗を記録
                EmailLog.objects.create(
                    contact=contact,
                    subject=next_step.subject,
                    email_type='scenario',
                    status='failed',
                    scenario_step=next_step,
                )
                failed_count += 1
                logger.error(
                    f'Failed to send scenario email to {contact.email}: {e}'
                )
                self.stderr.write(
                    self.style.ERROR(
                        f'  Failed to send to {contact.email}: {e}'
                    )
                )

        # 結果のサマリー
        self.stdout.write(
            self.style.SUCCESS(
                f'\nScenario email processing complete: '
                f'sent={sent_count}, failed={failed_count}, '
                f'completed={completed_count}'
            )
        )
