"""Tests for user repository."""

import pytest

from app.models.user import UserCreate
from app.repositories.user_repository import UserRepository


class TestUserRepository:
    """Tests for UserRepository."""

    def test_create_user(self, session_factory):
        """Test creating a user."""
        repo = UserRepository(session_factory())
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
        )

        user = repo.create(user_data, "hashed_password")

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_password"
        assert user.is_active is True
        assert user.is_admin is False
        assert user.id is not None

    def test_get_user_by_id(self, session_factory):
        """Test retrieving a user by ID."""
        db = session_factory()
        repo = UserRepository(db)

        # Create user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        created_user = repo.create(user_data, "hashed_password")

        # Retrieve by ID
        retrieved_user = repo.get_by_id(created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == "testuser"

    def test_get_user_by_email(self, session_factory):
        """Test retrieving a user by email."""
        db = session_factory()
        repo = UserRepository(db)

        # Create user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        repo.create(user_data, "hashed_password")

        # Retrieve by email
        retrieved_user = repo.get_by_email("test@example.com")

        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.username == "testuser"

    def test_get_user_by_username(self, session_factory):
        """Test retrieving a user by username."""
        db = session_factory()
        repo = UserRepository(db)

        # Create user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        repo.create(user_data, "hashed_password")

        # Retrieve by username
        retrieved_user = repo.get_by_username("testuser")

        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        assert retrieved_user.email == "test@example.com"

    def test_get_nonexistent_user_by_id(self, session_factory):
        """Test retrieving a non-existent user returns None."""
        repo = UserRepository(session_factory())
        user = repo.get_by_id("nonexistent-id")

        assert user is None

    def test_get_nonexistent_user_by_email(self, session_factory):
        """Test retrieving a non-existent user by email returns None."""
        repo = UserRepository(session_factory())
        user = repo.get_by_email("nonexistent@example.com")

        assert user is None

    def test_get_nonexistent_user_by_username(self, session_factory):
        """Test retrieving a non-existent user by username returns None."""
        repo = UserRepository(session_factory())
        user = repo.get_by_username("nonexistent")

        assert user is None

    def test_list_all_users(self, session_factory):
        """Test listing all users."""
        db = session_factory()
        repo = UserRepository(db)

        # Create multiple users
        for i in range(3):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                username=f"user{i}",
                password="password123",
            )
            repo.create(user_data, "hashed_password")

        # List all
        users = repo.list_all()

        assert len(users) == 3
        usernames = {user.username for user in users}
        assert usernames == {"user0", "user1", "user2"}

    def test_unique_email_constraint(self, session_factory):
        """Test that duplicate emails are not allowed."""
        db = session_factory()
        repo = UserRepository(db)

        # Create first user
        user_data1 = UserCreate(
            email="test@example.com",
            username="user1",
            password="password123",
        )
        repo.create(user_data1, "hashed_password")

        # Try to create second user with same email
        user_data2 = UserCreate(
            email="test@example.com",
            username="user2",
            password="password123",
        )

        with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
            repo.create(user_data2, "hashed_password")

    def test_unique_username_constraint(self, session_factory):
        """Test that duplicate usernames are not allowed."""
        db = session_factory()
        repo = UserRepository(db)

        # Create first user
        user_data1 = UserCreate(
            email="user1@example.com",
            username="testuser",
            password="password123",
        )
        repo.create(user_data1, "hashed_password")

        # Try to create second user with same username
        user_data2 = UserCreate(
            email="user2@example.com",
            username="testuser",
            password="password123",
        )

        with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
            repo.create(user_data2, "hashed_password")
