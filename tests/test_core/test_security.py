"""Tests for security utilities."""

from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test that passwords are hashed."""
        password = "mySecretPassword123"
        hashed = get_password_hash(password)

        assert hashed.startswith("bcrypt_sha256$")
        # Hash should be different from original
        assert hashed != password
        # Hash should be a string
        assert isinstance(hashed, str)
        # Hash should be non-empty
        assert len(hashed) > 0

    def test_verify_correct_password(self):
        """Test that correct password is verified."""
        password = "mySecretPassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test that incorrect password is rejected."""
        password = "mySecretPassword123"
        wrong_password = "wrongPassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test that hashing same password twice produces different hashes (salt)."""
        password = "mySecretPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Different hashes due to salt
        assert hash1 != hash2
        # But both verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_hash_password_allows_long_password(self):
        """Ensure long passwords (>72 bytes) are supported."""
        password = "A" * 100
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_with_expiration(self):
        """Test creating a token with custom expiration."""
        data = {"sub": "user123"}
        expires = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=expires)

        # Decode to check expiration
        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=UTC)

        # Should expire in approximately 15 minutes
        now = datetime.now(UTC)
        time_until_expiry = exp_datetime - now
        assert 14 * 60 < time_until_expiry.total_seconds() < 16 * 60

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)

        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert "exp" in payload

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        invalid_token = "invalid.jwt.token"
        payload = decode_access_token(invalid_token)

        assert payload is None

    def test_decode_expired_token(self):
        """Test that expired tokens are rejected."""
        data = {"sub": "user123"}
        # Create token that expires immediately
        expires = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expires)

        payload = decode_access_token(token)

        # Expired token should return None
        assert payload is None

    def test_decode_tampered_token(self):
        """Test that tampered tokens are rejected."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Tamper with the token in a way that always changes the signature bytes.
        # Altering the final base64 character can leave the decoded signature unchanged due
        # to padding, so flip the first signature character instead.
        header, payload, signature = token.split(".")
        tampered_signature = ("a" if signature[0] != "a" else "b") + signature[1:]
        tampered_token = ".".join([header, payload, tampered_signature])

        payload = decode_access_token(tampered_token)

        assert payload is None

    def test_token_contains_correct_data(self):
        """Test that decoded token contains expected data."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        username = "john_doe"

        data = {"sub": user_id, "username": username, "custom_field": "value"}
        token = create_access_token(data)
        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["custom_field"] == "value"
