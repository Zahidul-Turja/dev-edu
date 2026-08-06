from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from core.models import OTPPurpose


@shared_task
def send_otp_email(recipient_email: str, code: str, purpose: OTPPurpose.choices):
    subject = (
        "Your DevEdu verification code"
        if purpose == OTPPurpose.SIGNUP
        else "Your DevEdu password reset code"
    )
    from_email = settings.EMAIL_HOST_USER
    to = [recipient_email]

    text_content = f"Your OTP code is {code}. It expires in {settings.OTP_EXPIRY_SECONDS // 60} minutes."  # fallback for non-HTML clients

    html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f9f9f9;">
            <div style="max-width: 500px; margin: auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
            <h2 style="text-align: center; color: #333333;">Verify Your Email</h2>
            <p style="font-size: 16px; color: #555;">Use the OTP below to verify your email address. It expires in {settings.OTP_EXPIRY_SECONDS // 60} minutes.</p>
            <table style="margin: 20px auto; border-spacing: 15px 0;">
                <tr>
                    {''.join([f'<td style="width: 50px; height: 60px; text-align: center; vertical-align: middle; font-size: 24px; font-weight: bold; background-color: #eef2f7; border: 2px solid #ddd; border-radius: 8px; color: #333;">{digit}</td>' for digit in code])}
                </tr>
            </table>
            <p style="font-size: 14px; color: #999; text-align: center;">If you are not expecting any OTP from us then ignore this email. Also please do not share it with anyone.</p>
            </div>
        </body>
        </html>
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
