import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .factories import UserFactory
from users.utils.validators import (
    validate_username,
    validate_email,
    validate_password,
)

User = get_user_model()


class TestValidateUsername:
    @pytest.mark.parametrize(
        "username,valid",
        [
            ("user1", True),
            ("User1", True),
            ("u123", True),
            ("User1234567890123456", True),  
            ("1user", False), 
            ("us", False),  
            ("user12345678901234567", False), 
            ("user@name", False), 
            ("user имя", False), 
        ],
    )
    def test_username_validation(self, username, valid):
        if valid:
            validate_username(username)
        else:
            with pytest.raises(ValidationError):
                validate_username(username)


class TestValidateEmail:
    @pytest.mark.parametrize(
        "email,valid",
        [
            ("test@example.com", True),
            ("test.user+tag@sub.example.com", True),
            ("test@example", False),
            ("test@.com", False),
            ("test@com", False),
            ("@example.com", False),
        ],
    )
    @pytest.mark.django_db
    def test_email_format_validation(self, email, valid):
        if valid:
            validate_email(email)
        else:
            with pytest.raises(ValidationError):
                validate_email(email)

    def test_email_unique_validation(self, db):
        user = UserFactory(email="unique@example.com")

        validate_email(user.email, instance=user)

        with pytest.raises(ValidationError):
            validate_email(user.email)

        validate_email("another@example.com")


class TestValidatePassword:
    @pytest.mark.parametrize(
        "password,valid",
        [
            ("Test123!", True),  # valid
            ("short", False),  # too short
            ("nouppercase123!", False),  # no uppercase
            ("NoDigits!", False),  # no digits
            ("NoSpecial123", False),  # no special chars
        ],
    )
    def test_password_validation(self, password, valid):
        if valid:
            validate_password(password)
        else:
            with pytest.raises(ValidationError):
                validate_password(password)

    def test_password_validation_messages(self):
        with pytest.raises(ValidationError) as excinfo:
            validate_password("short")
        assert "минимум 6 символов" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            validate_password("alllower1!")
        assert "хотя бы одну заглавную букву" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            validate_password("NoDigits!")
        assert "хотя бы одну цифру" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            validate_password("Test1234")
        assert "хотя бы один специальный символ" in str(excinfo.value)