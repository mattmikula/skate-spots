"""Permissions for ratings."""

from rest_framework import permissions


class IsRatingOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow rating creators or admins to edit/delete ratings.
    """

    def has_object_permission(self, request, view, obj):  # noqa: ARG002
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the rating owner or admin
        return obj.user == request.user or request.user.is_staff
