class OTPCooldownError(Exception):
    pass


class OTPExpiredError(Exception):
    pass


class OTPMaxAttemptsError(Exception):
    pass


class OTPInvalidError(Exception):
    pass
