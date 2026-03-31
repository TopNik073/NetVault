import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aioboto3
from botocore.exceptions import ClientError

from src.core.config import config
from src.core.logger import get_logger

from src.services.ses.base import AbstractEmailService
from src.services.ses.templates import TwoFactorAuthTemplate, BucketAccessChangeTemplate

logger = get_logger(__name__)


class YandexSESService(AbstractEmailService):
    def __init__(self):
        self.session = aioboto3.Session()
        self._endpoint = config.YC_POSTBOX_ENDPOINT
        self._region = config.YC_POSTBOX_REGION
        self._sender = config.MAIL_FROM
        self._access_key = config.YC_POSTBOX_ACCESS_KEY
        self._secret_key = config.YC_POSTBOX_SECRET_KEY.get_secret_value()

    @staticmethod
    def _html_to_text(html: str) -> str:
        return re.sub(r'<[^>]+>', '', html).strip()

    async def send_email(
        self,
        to_email: str | list[str],
        subject: str,
        html_body: str,
        text_body: str | None = None,
        charset: str = "UTF-8"
    ) -> None:
        destinations = [to_email] if isinstance(to_email, str) else to_email
        text_body = text_body or self._html_to_text(html_body)

        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = self._sender
        msg['To'] = ', '.join(destinations)

        msg_body = MIMEMultipart('alternative')
        text_part = MIMEText(text_body.encode(charset), 'plain', charset)
        html_part = MIMEText(html_body.encode(charset), 'html', charset)
        msg_body.attach(text_part)
        msg_body.attach(html_part)
        msg.attach(msg_body)

        raw_message = str(msg)
        raw_message_bytes = bytes(raw_message, charset)

        try:
            async with self.session.client(
                'sesv2',
                region_name=self._region,
                endpoint_url=self._endpoint,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
            ) as client:
                await client.send_email(
                    FromEmailAddress=self._sender,
                    Destination={'ToAddresses': destinations},
                    Content={'Raw': {'Data': raw_message_bytes}}
                )

        except ClientError as e:
            error_message = e.response.get('Error', {}).get('Message', 'Unknown error')
            logger.error(f"Yandex Postbox ClientError: {error_message}")  # noqa: G004
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in Postbox: {e}")  # noqa: G004
            raise

    async def send_verification_email(self, user_email: str, token: str) -> None:
        template = TwoFactorAuthTemplate(code=token)
        await self.send_email(
            to_email=user_email,
            subject=f"Your Code: {token}",
            html_body=template.render(),
        )

    async def send_bucket_permission_changed_email(
            self,
            user_email: str,
            bucket_name: str,
            permission: str,
            granted_by: str,
            date: str | None = None
    ) -> None:
        template = BucketAccessChangeTemplate(
            bucket_name=bucket_name,
            permission=permission,
            granted_by=granted_by,
            date=date
        )

        await self.send_email(
            to_email=user_email,
            subject=template.subject,
            html_body=template.render(),
        )