# accounts/permissions.py
from rest_framework.permissions import SAFE_METHODS, BasePermission


def _role(user):
    return getattr(getattr(user, "profile", None), "role", None)


class IsAuthenticatedJWT(BasePermission):
    """
    Works with DRF SimpleJWT. If JWT auth is configured in REST_FRAMEWORK,
    request.user will be authenticated when a valid token is provided.
    """

    def has_permission(self, request, view):
        return bool(getattr(request, "user", None) and request.user.is_authenticated)


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsPropertyManager(BasePermission):
    def has_permission(self, request, view):
        return _role(request.user) == "pm"


class IsConcierge(BasePermission):
    def has_permission(self, request, view):
        return _role(request.user) == "con"


class IsAgent(BasePermission):
    """Third-party rental manager."""

    def has_permission(self, request, view):
        return _role(request.user) == "agent"


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return _role(request.user) == "own"
