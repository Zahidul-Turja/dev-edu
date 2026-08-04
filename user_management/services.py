import random
import redis
from django.conf import settings
from core.exceptions import (
    OTPCooldownError,
    OTPExpiredError,
    OTPMaxAttemptsError,
    OTPInvalidError,
)

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


class OTPService:

    @staticmethod
    def _code_key(email):
        return f"otp:{email}:code"

    @staticmethod
    def _attempts_key(email):
        return f"otp:{email}:attempts"

    @staticmethod
    def _cooldown_key(email):
        return f"otp:{email}:cooldown"

    @classmethod
    def generate(cls, email):
        if redis_client.exists(cls._cooldown_key(email)):
            ttl = redis_client.ttl(cls._cooldown_key(email))
            raise OTPCooldownError(f"Please wait {ttl}s before requesting another OTP")

        code = f"{random.randint(0, 999999):06d}"
        redis_client.setex(cls._code_key(email), settings.OTP_EXPIRY_SECONDS, code)
        redis_client.delete(cls._attempts_key(email))
        redis_client.setex(
            cls._cooldown_key(email), settings.OTP_RESEND_COOLDOWN_SECONDS, 1
        )
        return code

    @classmethod
    def verify(cls, email, code):
        stored = redis_client.get(cls._code_key(email))
        if stored is None:
            raise OTPExpiredError("OTP expired or invalid. Please request a new one.")

        attempts = redis_client.incr(cls._attempts_key(email))
        redis_client.expire(cls._attempts_key(email), settings.OTP_EXPIRY_SECONDS)

        if attempts > settings.OTP_MAX_ATTEMPTS:
            redis_client.delete(cls._code_key(email))
            raise OTPMaxAttemptsError(
                "Too many incorrect attempts. Please request a new OTP."
            )

        if stored != code:
            raise OTPInvalidError("Incorrect OTP")

        redis_client.delete(cls._code_key(email), cls._attempts_key(email))
        return True
