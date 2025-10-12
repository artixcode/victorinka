from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(validators=[UniqueValidator(queryset=User.objects.all())])

    class Meta:
        model = User
        fields = ("id", "email", "password", "full_name")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Неверный email или пароль")
        if not user.is_active:
            raise serializers.ValidationError("Пользователь деактивирован")
        attrs["user"] = user
        return attrs

class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "is_email_verified")
        read_only_fields = fields
