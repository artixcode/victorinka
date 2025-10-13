from rest_framework.permissions import BasePermission

class IsRoomHost(BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(obj, "host_id", None) == request.user.id
