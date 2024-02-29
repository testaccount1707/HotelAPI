from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to modify objects.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD, or OPTIONS requests.
        # if request.method in permissions.SAFE_METHODS:
        #     return True

        # Check if the user has the 'is_admin' attribute set to True.
        if not request.user.is_admin:
            raise PermissionDenied("You do not have permission to perform this action.")
        return request.user.is_admin
