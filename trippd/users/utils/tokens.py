from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Generates a token for activation based on the user's primary key, timestamp, and verification status. The token is valid until the user's verification status changes or a certain time has passed."""

    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp) + str(user.is_verified)
