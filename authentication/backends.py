from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


User = get_user_model()


class UsernameOrEmailBackend(ModelBackend):
    """Authenticate against either username or email (case-insensitive)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        try:
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            User().set_password(password)  # mitigate timing attacks
            return None
        except User.MultipleObjectsReturned:
            # Fall through — prefer exact username match
            user = User.objects.filter(username__iexact=username).first()
            if user is None:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
