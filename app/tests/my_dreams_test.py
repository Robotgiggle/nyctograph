from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from ..models import User
from .testutils import *

@patch("app.utils.Session")
class TestMyDreams:
    def test_get_entry_list_logged_in(self, db_class: MagicMock, client: TestClient):
        set_session(client, {"user_id":2})
        db_instance = db_class.return_value
        user_instance = db_instance.get.return_value

        response = client.get("/my-dreams")

        assert response.status_code == 200
        assert response.url == "http://testserver/my-dreams"
        db_instance.get.assert_called_with(User, 2)
        user_instance.dream_entries.__iter__.assert_called()

    def test_get_entry_list_logged_out(self, db_class: MagicMock, client: TestClient):
        set_session(client, {})
        db_instance = db_class.return_value

        response = client.get("/my-dreams")

        assert response.status_code == 200
        assert response.url == "http://testserver/login"
        db_instance.get.assert_not_called()

    # def test_get_entry_details_success(self, db_class: MagicMock, client: TestClient):
    #     TODO

    # def test_get_entry_details_logged_out(self, db_class: MagicMock, client: TestClient):
    #     TODO

    # def test_configure_entry_success(self, db_class: MagicMock, client: TestClient):
    #     TODO

    # def test_configure_entry_logged_out(self, db_class: MagicMock, client: TestClient):
    #     TODO