import json
import pytest
from os import getenv
from dotenv import load_dotenv
from base64 import b64encode, b64decode
from itsdangerous import TimestampSigner
from fastapi.testclient import TestClient

from ..main import app

load_dotenv(".env")

# Fixture that creates the fastapi TestClient at runtime to allow mocks to work
@pytest.fixture(scope='module')
def client() -> TestClient:
    return TestClient(app)

# Creates and sets a session cookie with arbitrary data (https://github.com/fastapi/fastapi/issues/929#issuecomment-940982932)
def set_session(client: TestClient, sessionDict: dict):
    signer = TimestampSigner(getenv("COOKIE_SECRET_KEY", ""))
    sessionCookie = signer.sign(
        b64encode(json.dumps(sessionDict).encode('utf-8')),
    ).decode('utf-8')
    client.cookies = {'session': sessionCookie}

def get_session(client: TestClient) -> dict:
    signer = TimestampSigner(getenv("COOKIE_SECRET_KEY", ""))
    rawCookie = client.cookies.get('session', domain='testserver.local')   # check for the real cookie
    if not rawCookie: rawCookie = client.cookies.get('session', domain='') # check for our artificial cookie
    if not rawCookie: return {}
    return json.loads(b64decode(signer.unsign(rawCookie)))