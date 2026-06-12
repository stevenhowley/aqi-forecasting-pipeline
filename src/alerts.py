import os
import smtplib
from email.message import EmailMessage

ALERT_EMAIL = os.getenv("ALERT_EMAIL")
ALERT_EMAIL_PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _send_email(subject: str, body: str) -> None:
    if not ALERT_EMAIL or not ALERT_EMAIL_PASSWORD:
        print("⚠️  Email credentials not configured — skipping notification.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = ALERT_EMAIL
    msg["To"] = ALERT_EMAIL
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(ALERT_EMAIL, ALERT_EMAIL_PASSWORD)
        smtp.send_message(msg)
    print(f"📧 Email sent: {subject}")


def send_alert_email(location_name: str, forecast_aqi: int, target_date, threshold: int) -> None:
    subject = f"⚠️ AQI Alert: {location_name} forecast {forecast_aqi}"
    body = (
        f"Air quality alert for {location_name}.\n\n"
        f"Forecast AQI: {forecast_aqi}\n"
        f"Target date: {target_date}\n"
        f"Threshold: {threshold}\n\n"
        f"Monitor conditions at https://www.airnow.gov/"
    )
    _send_email(subject, body)


def send_all_clear_email(location_name: str, forecast_aqi: int, target_date, threshold: int) -> None:
    subject = f"✅ AQI All-Clear: {location_name}"
    body = (
        f"Air quality has returned to acceptable levels for {location_name}.\n\n"
        f"Forecast AQI: {forecast_aqi}\n"
        f"Target date: {target_date}\n"
        f"Now below threshold of {threshold}.\n"
    )
    _send_email(subject, body)
