from unittest.mock import patch
from fastapi.testclient import TestClient

from ..models import User
from .testutils import *

@patch("app.utils.Session")
def test_get_entry_list_success(db_class, client: TestClient):
    set_session(client, {"user_id":2})
    db_instance = db_class.return_value
    user_instance = db_instance.get.return_value

    response = client.get("/my-dreams")

    assert response.status_code == 200
    assert response.url == "http://testserver/my-dreams"
    db_instance.get.assert_called_with(User, 2)
    user_instance.dream_entries.__iter__.assert_called()

@patch("app.utils.Session")
def test_get_entry_list_logged_out(db_class, client: TestClient):
    set_session(client, {})
    db_instance = db_class.return_value

    response = client.get("/my-dreams")

    assert response.status_code == 200
    assert response.url == "http://testserver/login"
    db_instance.get.assert_not_called()