"""Tests for authentication endpoints."""


class TestRegister:
    """Tests for user registration endpoint."""

    def test_register_new_user(self, client):
        """Test registering a new user."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["is_active"] is True
        assert data["is_admin"] is False
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, test_user):
        """Test that registering with duplicate email fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "testuser@example.com",  # Duplicate
                "username": "different",
                "password": "password123",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_duplicate_username(self, client, test_user):
        """Test that registering with duplicate username fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "different@example.com",
                "username": "testuser",  # Duplicate
                "password": "password123",
            },
        )

        assert response.status_code == 400
        assert "already taken" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Test that invalid email is rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "newuser",
                "password": "password123",
            },
        )

        assert response.status_code == 422

    def test_register_short_password(self, client):
        """Test that short password is rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "short",
            },
        )

        assert response.status_code == 422


class TestLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Check that cookie was set
        assert "access_token" in response.cookies

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password123"},
        )

        assert response.status_code == 401

    def test_login_sets_cookie(self, client, test_user):
        """Test that login sets httponly cookie."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"},
        )

        assert response.status_code == 200
        cookies = response.cookies
        assert "access_token" in cookies

        # Check cookie properties
        cookie = cookies["access_token"]
        assert cookie is not None


class TestLogout:
    """Tests for logout endpoint."""

    def test_logout(self, client, test_user, auth_token):
        """Test logout clears cookie."""
        response = client.post(
            "/api/v1/auth/logout",
            cookies={"access_token": auth_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "logged out" in data["message"].lower()


class TestGetCurrentUser:
    """Tests for getting current user info."""

    def test_get_current_user_authenticated(self, client, test_user, auth_token):
        """Test getting current user info when authenticated."""
        response = client.get(
            "/api/v1/auth/me",
            cookies={"access_token": auth_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "testuser@example.com"
        assert "id" in data

    def test_get_current_user_unauthenticated(self, client):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            cookies={"access_token": "invalid-token"},
        )

        assert response.status_code == 401


class TestLoginForm:
    """Tests for form-based login."""

    def test_login_form_success(self, client, test_user):
        """Test form login redirects on success."""
        response = client.post(
            "/api/v1/auth/login/form",
            data={"username": "testuser", "password": "password123"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/"
        assert "access_token" in response.cookies

    def test_login_form_wrong_password(self, client, test_user):
        """Test form login with wrong password."""
        response = client.post(
            "/api/v1/auth/login/form",
            data={"username": "testuser", "password": "wrongpassword"},
        )

        assert response.status_code == 401


class TestRegisterForm:
    """Tests for form-based registration."""

    def test_register_form_success(self, client):
        """Test form registration redirects on success."""
        response = client.post(
            "/api/v1/auth/register/form",
            data={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/"
        assert "access_token" in response.cookies

    def test_register_form_duplicate_email(self, client, test_user):
        """Test form registration with duplicate email."""
        response = client.post(
            "/api/v1/auth/register/form",
            data={
                "email": "testuser@example.com",
                "username": "different",
                "password": "password123",
            },
        )

        assert response.status_code == 400


class TestRateLimiting:
    """Tests covering rate limit behaviour on authentication endpoints."""

    def test_login_rate_limit_exceeded(self, client, test_user):
        """Multiple failed login attempts should trigger a 429 response."""

        for _ in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "testuser", "password": "wrongpassword"},
            )
            assert response.status_code == 401

        blocked = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )

        assert blocked.status_code == 429
        assert "rate limit" in blocked.json()["detail"].lower()
        assert "Retry-After" in blocked.headers
        assert int(blocked.headers["Retry-After"]) >= 1
