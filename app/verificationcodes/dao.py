from app.dao.base import BaseDAO
from app.verificationcodes.models import VerificationCode

class VerificationCodeDAO(BaseDAO):
    model = VerificationCode