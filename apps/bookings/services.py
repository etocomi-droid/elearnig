import json
import logging

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Google Calendar連携サービス"""

    def __init__(self, calendar_integration):
        self.integration = calendar_integration

    def _get_service(self):
        """Creates google-api-python-client service using service account credentials."""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            if not self.integration.credentials_json:
                return None

            credentials_info = json.loads(self.integration.credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/calendar'],
            )
            service = build('calendar', 'v3', credentials=credentials)
            return service
        except Exception as e:
            logger.error(f'Google Calendar service creation failed: {e}')
            return None

    def get_busy_times(self, date_min, date_max):
        """指定期間のビジー時間を取得する。(start_dt, end_dt)のタプルのリストを返す。"""
        try:
            service = self._get_service()
            if not service:
                return []

            body = {
                'timeMin': date_min.isoformat(),
                'timeMax': date_max.isoformat(),
                'items': [{'id': self.integration.calendar_id}],
            }
            result = service.freebusy().query(body=body).execute()
            busy_times = []
            for period in result.get('calendars', {}).get(
                self.integration.calendar_id, {}
            ).get('busy', []):
                from datetime import datetime
                start_dt = datetime.fromisoformat(period['start'])
                end_dt = datetime.fromisoformat(period['end'])
                busy_times.append((start_dt, end_dt))
            return busy_times
        except Exception as e:
            logger.error(f'Google Calendar get_busy_times failed: {e}')
            return []

    def create_event(self, booking):
        """カレンダーイベントを作成する。イベントIDを返す。"""
        try:
            service = self._get_service()
            if not service:
                return None

            event = {
                'summary': f'{booking.booking_type.name} - {booking.contact}',
                'description': (
                    f'予約タイプ: {booking.booking_type.name}\n'
                    f'ゲスト: {booking.contact}\n'
                    f'メモ: {booking.guest_memo}'
                ),
                'start': {
                    'dateTime': booking.start_datetime.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'dateTime': booking.end_datetime.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
            }
            result = service.events().insert(
                calendarId=self.integration.calendar_id, body=event
            ).execute()
            return result.get('id')
        except Exception as e:
            logger.error(f'Google Calendar create_event failed: {e}')
            return None

    def delete_event(self, event_id):
        """カレンダーイベントを削除する。成功したらTrueを返す。"""
        try:
            service = self._get_service()
            if not service:
                return False

            service.events().delete(
                calendarId=self.integration.calendar_id, eventId=event_id
            ).execute()
            return True
        except Exception as e:
            logger.error(f'Google Calendar delete_event failed: {e}')
            return False


class ZoomService:
    """Zoom連携サービス"""

    TOKEN_URL = 'https://zoom.us/oauth/token'
    API_BASE = 'https://api.zoom.us/v2'

    def __init__(self, zoom_integration):
        self.integration = zoom_integration

    def _get_access_token(self):
        """Server-to-Server OAuthでアクセストークンを取得する。"""
        try:
            import requests

            if not all([
                self.integration.account_id,
                self.integration.client_id,
                self.integration.client_secret,
            ]):
                return None

            response = requests.post(
                self.TOKEN_URL,
                auth=(self.integration.client_id, self.integration.client_secret),
                params={
                    'grant_type': 'account_credentials',
                    'account_id': self.integration.account_id,
                },
            )
            response.raise_for_status()
            return response.json().get('access_token')
        except Exception as e:
            logger.error(f'Zoom get_access_token failed: {e}')
            return None

    def create_meeting(self, booking):
        """Zoomミーティングを作成する。{id, join_url, start_url}を返す。"""
        try:
            import requests

            access_token = self._get_access_token()
            if not access_token:
                return None

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }
            data = {
                'topic': f'{booking.booking_type.name} - {booking.contact}',
                'type': 2,  # Scheduled meeting
                'start_time': booking.start_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                'duration': booking.booking_type.duration_minutes,
                'timezone': 'Asia/Tokyo',
            }
            response = requests.post(
                f'{self.API_BASE}/users/me/meetings',
                headers=headers,
                json=data,
            )
            response.raise_for_status()
            result = response.json()
            return {
                'id': str(result.get('id', '')),
                'join_url': result.get('join_url', ''),
                'start_url': result.get('start_url', ''),
            }
        except Exception as e:
            logger.error(f'Zoom create_meeting failed: {e}')
            return None

    def delete_meeting(self, meeting_id):
        """Zoomミーティングを削除する。成功したらTrueを返す。"""
        try:
            import requests

            access_token = self._get_access_token()
            if not access_token:
                return False

            headers = {
                'Authorization': f'Bearer {access_token}',
            }
            response = requests.delete(
                f'{self.API_BASE}/meetings/{meeting_id}',
                headers=headers,
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f'Zoom delete_meeting failed: {e}')
            return False
