"""Permissions for skate spots."""

from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission to only allow owners or admins to edit/delete objects."""

    def has_object_permission(self, request, view, obj):
        """Check if user is owner or admin."""
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner or admin
        return obj.owner == request.user or request.user.is_admin
