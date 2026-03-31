import html
from datetime import datetime
from typing import Protocol


class EmailTemplate(Protocol):
    """Protocol for email templates"""

    subject: str
    body: str
    html: bool = False

    def render(self) -> str:
        """Render template to string"""
        ...


class TwoFactorAuthTemplate:
    def __init__(self, code: str):
        self.subject = f'Your verification code: {code}'
        self.html = True
        self.body = f"""
        <html>
            <head>
                <title>NetVault Auth</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f0f4f8;
            ">
                <div style="
                    max-width: 600px;
                    margin: 40px auto;
                    padding: 30px;
                    background-color: #1E3A8A;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                ">
                    <h1 style="
                        color: #FFFFFF;
                        margin-bottom: 24px;
                        font-size: 26px;
                        text-align: center;
                    ">Email Verification</h1>

                    <p style="
                        font-size: 16px;
                        color: #DBEAFE;
                        margin-bottom: 10px;
                    ">Welcome,</p>

                    <p style="
                        font-size: 16px;
                        color: #DBEAFE;
                        margin-bottom: 20px;
                    ">To complete your sign-in, use the verification code below:</p>

                    <div style="
                        background-color: #DBEAFE;
                        border-radius: 8px;
                        padding: 20px;
                        margin: 25px 0;
                        text-align: center;
                    ">
                        <code style="
                            font-size: 36px;
                            font-weight: bold;
                            letter-spacing: 6px;
                            font-family: 'Courier New', monospace;
                            color: #1E3A8A;
                        ">{code}</code>
                    </div>

                    <div style="
                        font-size: 14px;
                        color: #BFDBFE;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid rgba(255, 255, 255, 0.1);
                        line-height: 1.6;
                    ">
                        <p style="margin: 5px 0;">• This code will expire in 10 minutes.</p>
                        <p style="margin: 5px 0;">• If you didn't request this code, please ignore this email.</p>
                    </div>
                </div>
            </body>
        </html>
        """

    def render(self) -> str:
        """Render template to string"""
        return self.body


class BucketAccessChangeTemplate:
    def __init__(
        self,
        bucket_name: str,
        permission: str,
        granted_by: str,
        date: str | None = None
    ):
        self.bucket_name = html.escape(bucket_name)
        self.permission = html.escape(permission)
        self.granted_by = html.escape(granted_by)
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.date = html.escape(date)

        self.subject = f'Access to bucket {self.bucket_name} has been updated'
        self.html = True

    def render(self) -> str:
        return f"""
        <html>
            <head>
                <title>NetVault Access Update</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f0f4f8;
            ">
                <div style="
                    max-width: 600px;
                    margin: 40px auto;
                    padding: 30px;
                    background-color: #1E3A8A;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                ">
                    <h1 style="
                        color: #FFFFFF;
                        margin-bottom: 24px;
                        font-size: 26px;
                        text-align: center;
                    ">Bucket Access Update</h1>
        
                    <p style="
                        font-size: 16px;
                        color: #DBEAFE;
                        margin-bottom: 10px;
                    ">Hello</p>
        
                    <p style="
                        font-size: 16px;
                        color: #DBEAFE;
                        margin-bottom: 20px;
                    ">The access permissions for bucket <strong style="color:#FFFFFF;">{self.bucket_name}</strong> have been updated.</p>
        
                    <div style="
                        background-color: #DBEAFE;
                        border-radius: 8px;
                        padding: 20px;
                        margin: 25px 0;
                    ">
                        <p style="margin:10px 0; color:#1E3A8A;"><strong>New permission:</strong> {self.permission}</p>
                        <p style="margin:10px 0; color:#1E3A8A;"><strong>Granted by:</strong> {self.granted_by}</p>
                        <p style="margin:10px 0; color:#1E3A8A;"><strong>Date:</strong> {self.date}</p>
                    </div>
        
                    <div style="
                        font-size: 14px;
                        color: #BFDBFE;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid rgba(255, 255, 255, 0.1);
                        line-height: 1.6;
                    ">
                        <p style="margin: 5px 0;">• If you didn't expect this change, please contact your administrator.</p>
                    </div>
                </div>
            </body>
        </html>
        """