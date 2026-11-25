import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv


load_dotenv()


class EmailService:
    def __init__(self):
        self.sender = os.getenv("EMAIL_SENDER")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.smtp_server = os.getenv(
            "SMTP_SERVER",
            "smtp.gmail.com",
        )
        self.smtp_port = int(
            os.getenv(
                "SMTP_PORT",
                "587",
            )
        )

        if not self.sender:
            raise ValueError(
                "EMAIL_SENDER is missing in the .env file."
            )

        if not self.password:
            raise ValueError(
                "EMAIL_PASSWORD is missing in the .env file."
            )

    def send_html_email(
        self,
        recipient: str,
        subject: str,
        html_content: str,
    ) -> dict:
        recipient = recipient.strip().lower()

        try:
            message = MIMEMultipart("alternative")
            message["From"] = self.sender
            message["To"] = recipient
            message["Subject"] = subject

            message.attach(
                MIMEText(
                    html_content,
                    "html",
                    "utf-8",
                )
            )

            with smtplib.SMTP(
                self.smtp_server,
                self.smtp_port,
                timeout=30,
            ) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()

                server.login(
                    self.sender,
                    self.password,
                )

                refused = server.sendmail(
                    self.sender,
                    [recipient],
                    message.as_string(),
                )

            if refused:
                return {
                    "success": False,
                    "recipient": recipient,
                    "message": f"SMTP refused recipient: {refused}",
                }

            return {
                "success": True,
                "recipient": recipient,
                "message": "Email sent successfully.",
            }

        except Exception as error:
            return {
                "success": False,
                "recipient": recipient,
                "message": (
                    f"{type(error).__name__}: {error}"
                ),
            }