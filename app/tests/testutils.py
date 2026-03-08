import json
import pytest
from base64 import b64encode
from itsdangerous import TimestampSigner
from fastapi.testclient import TestClient

from ..main import app, COOKIE_SECRET_KEY

# Provides the fastapi TestClient at runtime to allow mocks to work
@pytest.fixture(scope='module')
def client() -> TestClient:
    return TestClient(app)

# Creates and sets a session cookie with arbitrary data (https://github.com/fastapi/fastapi/issues/929#issuecomment-940982932)
def set_session(client: TestClient, sessionDict: dict):
    signer = TimestampSigner(COOKIE_SECRET_KEY)
    sessionCookie = signer.sign(
        b64encode(json.dumps(sessionDict).encode('utf-8')),
    ).decode('utf-8')
    client.cookies = {'session': sessionCookie}