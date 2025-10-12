"""Tests for user Pydantic models."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.user import Token, User, UserCreate, UserLogin


class TestUserCreate:
    """Tests for UserCreate model."""

    def test_valid_user_create(self):
        """Test creating a valid user."""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password == "password123"

    def test_invalid_email(self):
        """Test that invalid email raises validation error."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                username="testuser",
                password="password123",
            )

    def test_username_too_short(self):
        """Test that username shorter than 3 chars raises error."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="ab",
                password="password123",
            )

    def test_username_too_long(self):
        """Test that username longer than 50 chars raises error."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="a" * 51,
                password="password123",
            )

    def test_password_too_short(self):
        """Test that password shorter than 8 chars raises error."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="short",
            )


class TestUserLogin:
    """Tests for UserLogin model."""

    def test_valid_login(self):
        """Test creating a valid login request."""
        login = UserLogin(username="testuser", password="password123")
        assert login.username == "testuser"
        assert login.password == "password123"


class TestUser:
    """Tests for User response model."""

    def test_user_response(self):
        """Test creating a user response."""
        from datetime import datetime

        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_admin=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.is_admin is False


class TestToken:
    """Tests for Token model."""

    def test_token_response(self):
        """Test creating a token response."""
        token = Token(access_token="fake-jwt-token")
        assert token.access_token == "fake-jwt-token"
        assert token.token_type == "bearer"

    def test_token_custom_type(self):
        """Test token with custom type."""
        token = Token(access_token="fake-token", token_type="custom")
        assert token.token_type == "custom"
