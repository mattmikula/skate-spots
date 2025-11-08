"""API tests for follow relationship endpoints."""

import pytest


@pytest.fixture
def second_user(session_factory):
    """Create a second test user."""
    from app.core.security import get_password_hash
    from app.models.user import UserCreate
    from app.repositories.user_repository import UserRepository

    db = session_factory()
    try:
        repo = UserRepository(db)
        user_data = UserCreate(
            email="seconduser@example.com",
            username="seconduser",
            password="password123",
        )
        hashed_password = get_password_hash("password123")
        user = repo.create(user_data, hashed_password)
        db.expunge(user)
        return user
    finally:
        db.close()


@pytest.fixture
def second_user_token(second_user):
    """Create an authentication token for the second user."""
    from app.core.security import create_access_token

    return create_access_token(data={"sub": str(second_user.id), "username": second_user.username})


def test_follow_user_success(client, auth_token, second_user):
    """Successfully follow another user returns HTML response."""
    response = client.post(
        f"/api/v1/users/{second_user.username}/follow",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 200
    # HTML response should contain follow button markup
    assert "button" in response.text.lower() or "unfollow" in response.text.lower()


def test_follow_user_requires_auth(client, second_user):
    """Following a user requires authentication."""
    response = client.post(f"/api/v1/users/{second_user.username}/follow")
    assert response.status_code == 401


def test_follow_user_not_found(client, auth_token):
    """Following a non-existent user returns 404."""
    response = client.post(
        "/api/v1/users/nonexistentuser/follow",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_follow_self_returns_error(client, auth_token, test_user):
    """Cannot follow yourself."""
    response = client.post(
        f"/api/v1/users/{test_user.username}/follow",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 400
    assert "cannot follow yourself" in response.json()["detail"].lower()


def test_follow_already_following_returns_error(client, auth_token, second_user):
    """Following a user twice returns error."""
    # Follow once
    response1 = client.post(
        f"/api/v1/users/{second_user.username}/follow",
        cookies={"access_token": auth_token},
    )
    assert response1.status_code == 200

    # Try to follow again
    response2 = client.post(
        f"/api/v1/users/{second_user.username}/follow",
        cookies={"access_token": auth_token},
    )

    assert response2.status_code == 400
    assert "already following" in response2.json()["detail"].lower()


def test_unfollow_user_success(client, auth_token, second_user):
    """Successfully unfollow a user."""
    # First follow
    client.post(
        f"/api/v1/users/{second_user.username}/follow",
        cookies={"access_token": auth_token},
    )

    # Then unfollow
    response = client.delete(
        f"/api/v1/users/{second_user.username}/follow",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 200
    # HTML response should contain follow button markup
    assert "button" in response.text.lower() or "follow" in response.text.lower()


def test_unfollow_user_requires_auth(client, second_user):
    """Unfollowing a user requires authentication."""
    response = client.delete(f"/api/v1/users/{second_user.username}/follow")
    assert response.status_code == 401


def test_unfollow_user_not_found(client, auth_token):
    """Unfollowing a non-existent user returns 404."""
    response = client.delete(
        "/api/v1/users/nonexistentuser/follow",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_unfollow_not_following_returns_error(client, auth_token, second_user):
    """Unfollowing a user you're not following returns error."""
    response = client.delete(
        f"/api/v1/users/{second_user.username}/follow",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 400
    assert "not following" in response.json()["detail"].lower()


def test_is_following_true(client, auth_token, second_user):
    """Check if following returns true when following."""
    # First follow
    client.post(
        f"/api/v1/users/{second_user.username}/follow",
        cookies={"access_token": auth_token},
    )

    # Check is_following
    response = client.get(
        f"/api/v1/users/me/following/{second_user.username}",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_following"] is True


def test_is_following_false(client, auth_token, second_user):
    """Check if following returns false when not following."""
    response = client.get(
        f"/api/v1/users/me/following/{second_user.username}",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_following"] is False


def test_is_following_requires_auth(client, second_user):
    """Checking if following requires authentication."""
    response = client.get(f"/api/v1/users/me/following/{second_user.username}")
    assert response.status_code == 401


def test_is_following_user_not_found(client, auth_token):
    """Checking if following a non-existent user returns 404."""
    response = client.get(
        "/api/v1/users/me/following/nonexistentuser",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_followers_empty(client, test_user):
    """Get followers for user with no followers."""
    response = client.get(f"/api/v1/users/{test_user.username}/followers")

    assert response.status_code == 200
    data = response.json()
    assert "followers" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["total"] == 0
    assert len(data["followers"]) == 0


def test_get_followers_with_followers(client, test_user, second_user_token):
    """Get followers for user with followers."""
    # Second user follows test user
    client.post(
        f"/api/v1/users/{test_user.username}/follow",
        cookies={"access_token": second_user_token},
    )

    response = client.get(f"/api/v1/users/{test_user.username}/followers")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["followers"]) > 0
    # Check follower structure
    follower = data["followers"][0]
    assert "id" in follower
    assert "username" in follower


def test_get_followers_pagination(client, test_user):
    """Get followers supports pagination."""
    response = client.get(f"/api/v1/users/{test_user.username}/followers?limit=10&offset=5")

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 5


def test_get_followers_user_not_found(client):
    """Get followers for non-existent user returns 404."""
    response = client.get("/api/v1/users/nonexistentuser/followers")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_following_empty(client, test_user):
    """Get following for user following no one."""
    response = client.get(f"/api/v1/users/{test_user.username}/following")

    assert response.status_code == 200
    data = response.json()
    assert "following" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["total"] == 0
    assert len(data["following"]) == 0


def test_get_following_with_following(client, auth_token, test_user, second_user):
    """Get following for user who follows others."""
    # Test user follows second user
    client.post(
        f"/api/v1/users/{second_user.username}/follow",
        cookies={"access_token": auth_token},
    )

    response = client.get(f"/api/v1/users/{test_user.username}/following")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["following"]) > 0
    # Check following structure
    following = data["following"][0]
    assert "id" in following
    assert "username" in following


def test_get_following_pagination(client, test_user):
    """Get following supports pagination."""
    response = client.get(f"/api/v1/users/{test_user.username}/following?limit=10&offset=5")

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 5


def test_get_following_user_not_found(client):
    """Get following for non-existent user returns 404."""
    response = client.get("/api/v1/users/nonexistentuser/following")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_follow_stats_no_activity(client, test_user):
    """Get follow stats for user with no follows."""
    response = client.get(f"/api/v1/users/{test_user.username}/follow-stats")

    assert response.status_code == 200
    data = response.json()
    assert "followers_count" in data
    assert "following_count" in data
    assert data["followers_count"] == 0
    assert data["following_count"] == 0


def test_get_follow_stats_with_activity(client, auth_token, test_user, second_user):
    """Get follow stats for user with followers and following."""
    # Test user follows second user
    client.post(
        f"/api/v1/users/{second_user.username}/follow",
        cookies={"access_token": auth_token},
    )

    response = client.get(f"/api/v1/users/{test_user.username}/follow-stats")

    assert response.status_code == 200
    data = response.json()
    assert data["followers_count"] == 0  # No one follows test_user
    assert data["following_count"] == 1  # Test_user follows 1 person


def test_get_follow_stats_user_not_found(client):
    """Get follow stats for non-existent user returns 404."""
    response = client.get("/api/v1/users/nonexistentuser/follow-stats")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_follow_unfollow_workflow(client, auth_token, second_user):
    """Complete follow/unfollow workflow."""
    # Initially not following
    response = client.get(
        f"/api/v1/users/me/following/{second_user.username}",
        cookies={"access_token": auth_token},
    )
    assert response.json()["is_following"] is False

    # Follow user
    response = client.post(
        f"/api/v1/users/{second_user.username}/follow",
        cookies={"access_token": auth_token},
    )
    assert response.status_code == 200

    # Verify following
    response = client.get(
        f"/api/v1/users/me/following/{second_user.username}",
        cookies={"access_token": auth_token},
    )
    assert response.json()["is_following"] is True

    # Unfollow user
    response = client.delete(
        f"/api/v1/users/{second_user.username}/follow",
        cookies={"access_token": auth_token},
    )
    assert response.status_code == 200

    # Verify not following
    response = client.get(
        f"/api/v1/users/me/following/{second_user.username}",
        cookies={"access_token": auth_token},
    )
    assert response.json()["is_following"] is False
