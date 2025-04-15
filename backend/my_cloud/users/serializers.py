from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import User
from users.utils.validators import validate_username, validate_email, validate_password

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'full_name']
        extra_kwargs = {
            'username': {'validators': [validate_username]},
            'email': {'validators': [validate_email]},
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', '')
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'is_admin', 'storage_path']
        read_only_fields = ['id', 'is_admin', 'storage_path']

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        request = self.context.get('request')
        user = authenticate(request=request, username=username, password=password)
        if not user:
            raise serializers.ValidationError(
                _("Неверные имя пользователя или пароль"),
                code='authorization'
            )
        if not user.is_active:
            raise serializers.ValidationError(
                _("Аккаунт деактивирован"),
                code='inactive'
            )
        attrs['user'] = user
        return attrs
