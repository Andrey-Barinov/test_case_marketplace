import smtplib
from email.mime.text import MIMEText

from src.celery_conf import celery_app
from src.settings import settings


@celery_app.task
def send_email_after_successful_registration(to_email: str):
    # Настройки SMTP
    smtp_server = settings.SMTP_SERVER
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD

    # Создание письма
    subject = "Успешная регистрация"
    body = "Поздравляем! Вы успешно зарегистрировались."
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email

    # Отправка письма
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
    except Exception as e:
        print(f"Ошибка отправки письма: {e}")
