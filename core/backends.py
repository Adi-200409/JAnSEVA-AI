from django.contrib.auth.backends import ModelBackend
from core.models import SmartUser


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = SmartUser.objects.get(email=username)
            if user.check_password(password):
                return user
            return None
        except SmartUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return SmartUser.objects.get(pk=user_id)
        except SmartUser.DoesNotExist:
            return None