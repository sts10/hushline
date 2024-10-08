import os

from flask.testing import FlaskClient

# Import models and other modules
from hushline import db
from hushline.model import InviteCode, User


def test_user_registration_with_invite_code_disabled(client: FlaskClient) -> None:
    os.environ["REGISTRATION_CODES_REQUIRED"] = "False"

    # User registration data
    user_data = {"username": "test_user", "password": "SecurePassword123!"}

    # Post request to register a new user
    response = client.post("/register", data=user_data, follow_redirects=True)

    # Validate response
    assert response.status_code == 200
    assert "Registration successful!" in response.text

    # Verify user is added to the database
    user = db.session.scalars(
        db.select(User).filter_by(primary_username="test_user").limit(1)
    ).first()
    assert user is not None
    assert user.primary_username == "test_user"


def test_user_registration_with_invite_code_enabled(client: FlaskClient) -> None:
    # Enable invite codes
    os.environ["REGISTRATION_CODES_REQUIRED"] = "True"

    # Generate a valid invite code using the script
    code = InviteCode()
    db.session.add(code)
    db.session.commit()

    # User registration data with valid invite code
    user_data = {
        "username": "newuser",
        "password": "SecurePassword123!",
        "invite_code": code.code,
    }

    # Post request to register a new user
    response = client.post("/register", data=user_data, follow_redirects=True)

    # Validate response
    assert response.status_code == 200
    assert "Registration successful!" in response.text

    # Verify user is added to the database
    user = db.session.scalars(
        db.select(User).filter_by(primary_username="newuser").limit(1)
    ).first()
    assert user is not None
    assert user.primary_username == "newuser"


def test_register_page_loads(client: FlaskClient) -> None:
    response = client.get("/register")
    assert response.status_code == 200
    assert "<h2>Register</h2>" in response.text


def test_login_link(client: FlaskClient) -> None:
    # Get the registration page
    response = client.get("/register")
    assert response.status_code == 200

    # Check if the login link is in the response
    assert 'href="/login"' in response.text, "Login link should be present on the registration page"

    # Simulate clicking the login link
    login_response = client.get("/login")
    assert login_response.status_code == 200
    assert "<h2>Login</h2>" in login_response.text, "Should be on the login page now"


def test_registration_link(client: FlaskClient) -> None:
    # Get the login page
    response = client.get("/login")
    assert response.status_code == 200, "Login page should be accessible"

    # Check if the registration link is in the response
    assert (
        'href="/register"' in response.text
    ), "Registration link should be present on the login page"

    # Simulate clicking the registration link
    register_response = client.get("/register")
    assert register_response.status_code == 200, "Should be on the registration page now"
    assert "<h2>Register</h2>" in register_response.text, "Should be on the registration page"


def test_user_login_after_registration(client: FlaskClient) -> None:
    # Prepare the environment to not require invite codes
    os.environ["REGISTRATION_CODES_REQUIRED"] = "False"

    # User registration data
    registration_data = {"username": "newuser", "password": "SecurePassword123!"}

    # Post request to register a new user
    client.post("/register", data=registration_data, follow_redirects=True)

    # Login data should match the registration data
    login_data = {"username": "newuser", "password": "SecurePassword123!"}

    # Attempt to log in with the registered user
    login_response = client.post("/login", data=login_data, follow_redirects=True)

    # Validate login response
    assert login_response.status_code == 200
    assert "Inbox" in login_response.text, "Should be redirected to the Inbox page"
    assert (
        'href="/inbox?username=newuser"' in login_response.text
    ), "Inbox link should be present for the user"


def test_user_login_with_incorrect_password(client: FlaskClient) -> None:
    # Prepare the environment to not require invite codes
    os.environ["REGISTRATION_CODES_REQUIRED"] = "False"

    # User registration data
    registration_data = {"username": "newuser", "password": "SecurePassword123!"}

    # Post request to register a new user
    client.post("/register", data=registration_data, follow_redirects=True)

    # Login data with an incorrect password
    login_data = {"username": "newuser", "password": "Wrong_Password!"}

    # Attempt to log in with the registered user and incorrect password
    login_response = client.post("/login", data=login_data, follow_redirects=True)

    # Validate login response
    assert login_response.status_code == 200
    assert "Inbox" not in login_response.text, "Should not be redirected to the Inbox page"
    assert (
        'href="/inbox?username=newuser"' not in login_response.text
    ), "Inbox link should not be present for the user"
    assert (
        "Invalid username or password" in login_response.text
    ), "Error message should be displayed"
