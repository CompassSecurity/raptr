from collections.abc import Generator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.authentication import create_access_token_service
from app.core.password import hash_password
from app.db.session import get_session
from app.enums.enums import AclRole
from app.main import app
from app.models.user import Base, User


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """
    Create an in-memory SQLite database for testing
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """
    Create a TestClient with database session override.
    """

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


# Test user credentials
TEST_ADMIN_EMAIL = "admin@test.com"
TEST_ADMIN_PASSWORD = "AdminPass123!"
TEST_USER_EMAIL = "user@test.com"
TEST_USER_PASSWORD = "UserPass123!"


@pytest.fixture(name="test_admin_user")
def test_admin_user_fixture(session: Session) -> User:
    """
    Create a test admin user in the database
    """
    admin_user = User(
        email=TEST_ADMIN_EMAIL,
        hashed_password=hash_password(TEST_ADMIN_PASSWORD),
        role="admin",
        disabled=False,
    )
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)
    admin_user.assessment_acl_role = AclRole.RED
    return admin_user


@pytest.fixture(name="test_regular_user")
def test_regular_user_fixture(session: Session) -> User:
    """
    Create a test regular user in the database
    """
    regular_user = User(
        email=TEST_USER_EMAIL,
        hashed_password=hash_password(TEST_USER_PASSWORD),
        role="user",
        disabled=False,
    )
    session.add(regular_user)
    session.commit()
    session.refresh(regular_user)
    regular_user.assessment_acl_role = AclRole.RED
    return regular_user


@pytest.fixture(name="test_disabled_user")
def test_disabled_user_fixture(session: Session) -> User:
    """
    Create a test disabled user in the database
    """
    disabled_user = User(
        email="disabled@test.com",
        hashed_password=hash_password("DisabledPass123!"),
        role="user",
        disabled=True,
    )
    session.add(disabled_user)
    session.commit()
    session.refresh(disabled_user)
    return disabled_user


@pytest.fixture(name="auth_token_admin")
def auth_token_admin_fixture(test_admin_user: User) -> str:
    """
    Generate a valid JWT token for the test admin user
    """
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token_service(
        data={"sub": test_admin_user.email}, expires_delta=access_token_expires
    )
    return access_token


@pytest.fixture(name="auth_token_regular")
def auth_token_regular_fixture(test_regular_user: User) -> str:
    """
    Generate a valid JWT token for the test regular user
    """
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token_service(
        data={"sub": test_regular_user.email}, expires_delta=access_token_expires
    )
    return access_token


@pytest.fixture(name="auth_headers_admin")
def auth_headers_admin_fixture(auth_token_admin: str) -> dict[str, str]:
    """
    Generate authorization headers for the test admin user
    """
    return {"Authorization": f"Bearer {auth_token_admin}"}


@pytest.fixture(name="auth_headers_regular")
def auth_headers_regular_fixture(auth_token_regular: str) -> dict[str, str]:
    """
    Generate authorization headers for the test regular user
    """
    return {"Authorization": f"Bearer {auth_token_regular}"}


@pytest.fixture(autouse=True)
def default_settings_fixture():
    """
    Ensure settings are in a known default state before each test.
    Specifically, ensure MFA is disabled by default.
    """
    from app.core.config import settings

    # Store original values, for testing we want False
    original_otp_local = settings.OTP_LOCAL_ENABLED
    original_otp_external = settings.OTP_EXTERNAL_ENABLED
    settings.OTP_LOCAL_ENABLED = False
    settings.OTP_EXTERNAL_ENABLED = False

    # Ensure SECRET_KEY is set for tests
    original_secret_key = settings.SECRET_KEY
    if not settings.SECRET_KEY:
        settings.SECRET_KEY = "test_secret_key"

    yield

    # Restore original values
    settings.OTP_LOCAL_ENABLED = original_otp_local
    settings.OTP_EXTERNAL_ENABLED = original_otp_external
    settings.SECRET_KEY = original_secret_key
