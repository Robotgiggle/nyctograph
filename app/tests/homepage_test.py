from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from pytest import xfail

from ..models import User
from .testutils import *

@patch("app.utils.Session")
class TestHomepage:
    def test_get_homepage(self, db_class: MagicMock, client: TestClient):
        testEntry = ("testDream8567", "the quick brown fox jumped over the lazy dog")
        set_session(client, {"storedEntry": testEntry})

        response = client.get("/")

        assert response.status_code == 200
        assert response.url == "http://testserver/"
        assert testEntry[0] in response.text
        assert testEntry[1] in response.text

    @patch("app.routers.homepage.DreamEntry")
    def test_submit_entry_logged_in(self, entry_class: MagicMock, db_class: MagicMock, client: TestClient):
        set_session(client, {"user_id": 3})
        db_instance = db_class.return_value
        user_instance = db_instance.get.return_value
        entryData = {"title": "New Test Entry!", "description": "Hello world, I am the description"}

        response = client.post("/", data=entryData)

        assert response.status_code == 200
        assert response.url == "http://testserver/"
        # login check
        db_instance.get.assert_called_with(User, 3)
        # adding new entry
        entry_class.assert_called_with(title=entryData["title"], description=entryData["description"], public=False)
        user_instance.dream_entries.append.assert_called_with(entry_class.return_value)
        # saving new entry
        db_instance.add.assert_called_with(user_instance)
        db_instance.commit.assert_called()

    def test_submit_entry_guest(self, db_class: MagicMock, client: TestClient):
        # ==========================================
        xfail("sign-up page not implemented yet")
        # ==========================================
        
        set_session(client, {"user_id": 3})
        db_instance = db_class.return_value
        entryData = {"title": "New Test Entry!", "description": "Hello world, I am the description"}

        response = client.post("/", data=entryData)

        assert response.status_code == 200
        assert response.url == "http://testserver/signup"
        assert "Entry data temporarily saved" in response.text
        # no login performed
        db_instance.get.assert_not_called()
        # entry not saved to DB
        db_instance.add.assert_not_called()
        db_instance.commit.assert_not_called()
