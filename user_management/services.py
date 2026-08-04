import random
import redis
from django.conf import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_response=True)


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
        if redis_client.exists(cls._cooldown_key(email=email)):
            ttl = redis_client.ttl(cls._cooldown_key(email=email))
            raise Exception(f"Please wait {ttl}s before requesting another OTP")

        code = f"{random.randint(0, 9999)}:04d"
        redis_client.setex(
            name=cls._code_key(email), time=settings.OTP_EXPIRY_SECONDS, value=code
        )
        redis_client.delete(cls._attempts_key)
        redis_client.setex(
            name=cls._cooldown_key(email), time=settings.OTP_EXPIRY_SECONDS
        )
        return code

    @classmethod
    def verify(cls, email, code):
        stored = redis_client.get(cls._code_key(email))
        if stored is None:
            raise Exception("OTP expired or invalid.")

        attempts = redis_client.incr(cls._attempts_key(email), amount=1)
        redis_client.expire(cls._attempts_key(email), settings.OTP_EXPIRY_SECONDS)

        if attempts > settings.OTP_MAX_ATTEMPTS:
            redis_client.delete(cls._code_key(email))
            raise Exception("Too many incorrect attempts. Please request a new OTP.")

        if stored != code:
            raise Exception("Incorrect OTP")

        redis_client.delete(cls._code_key(email), cls._attempts_key(email))
        return True
