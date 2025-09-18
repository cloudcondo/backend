# accounts/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Role, UnitAccess, UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserProfile
        fields = ["username", "email", "role"]


class UnitAccessSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    unit = serializers.PrimaryKeyRelatedField(read_only=False)

    class Meta:
        model = UnitAccess
        fields = ["id", "user", "unit", "access_type", "created_at"]
        read_only_fields = ["id", "created_at"]
