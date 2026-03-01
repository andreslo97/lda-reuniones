import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailSender:
    def __init__(self):
        self.host = os.getenv("LDA_SMTP_HOST", "")
        self.port = int(os.getenv("LDA_SMTP_PORT", "587"))
        self.tls = os.getenv("LDA_SMTP_TLS", "true").lower() == "true"
        self.user = os.getenv("LDA_SMTP_USER", "")
        self.password = os.getenv("LDA_SMTP_PASS", "")
        self.from_name = os.getenv("LDA_SMTP_FROM_NAME", "Reuniones")

        if not self.host or not self.user or not self.password:
            raise RuntimeError("Faltan variables SMTP en el .env (LDA_SMTP_HOST/USER/PASS).")

    def send_html(self, to_email: str, subject: str, html_body: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.from_name} <{self.user}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(self.host, self.port, timeout=20) as server:
            if self.tls:
                server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.user, [to_email], msg.as_string())
