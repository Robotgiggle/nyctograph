from unittest.mock import MagicMock, patch, ANY
from fastapi.testclient import TestClient
from html import unescape
from datetime import time

from ..forms import DreamEntryForm
from ..models import User, Tag
from .testutils import *

@patch("app.utils.Session")
class TestHomepage:
    def test_get_homepage(self, db_class: MagicMock, client: TestClient):
        testEntryData = DreamEntryForm(title="testDream8567", description="lorem ipsum dolor sit amet", public=False)
        set_session(client, {"storedEntry": testEntryData.model_dump_json()})

        response = client.get("/")

        assert response.status_code == 200
        assert response.url == "http://testserver/"
        assert testEntryData.title in response.text
        assert testEntryData.description in response.text

    @patch("app.forms.dream_entry_form.DreamEntry")
    def test_submit_entry_blank(self, entry_class: MagicMock, db_class: MagicMock, client: TestClient):
        set_session(client, {"user_id": 3})
        db_instance = db_class.return_value
        user_instance = db_class.return_value.get.return_value

        response = client.post("/", data={})

        assert response.status_code == 200
        assert response.url == "http://testserver/"
        # Warning messages flashed
        assert "Validation error for 'title'" in unescape(response.text)
        assert "Validation error for 'description'" in unescape(response.text)
        assert "Validation error for 'public'" in unescape(response.text)
        # No attempt to create or save entry
        entry_class.assert_not_called()
        user_instance.dream_entries.append.assert_not_called()
        db_instance.commit.assert_not_called()

    @patch("app.forms.dream_entry_form.DreamEntry")
    def test_submit_entry_badtag(self, entry_class: MagicMock, db_class: MagicMock, client: TestClient):
        set_session(client, {"user_id": 3})
        db_instance = db_class.return_value
        user_instance = MagicMock()
        db_instance.get.side_effect = lambda m,v: None if m==Tag else user_instance
        entryData = {"title": "New Test Entry!", "description": "Hello world, I am the description", 
                     "content_tags": ["fake", "also fake", "not real"], "public": "True"}
        
        response = client.post("/", data=entryData)

        assert response.status_code == 200
        assert response.url == "http://testserver/"
        # Warning messages flashed
        for badtag in entryData["content_tags"]:
            assert f"'{badtag}' is not a valid tag!" in unescape(response.text)
        # No attempt to save entry
        db_instance.add.assert_not_called()
        db_instance.commit.assert_not_called()

    @patch("app.forms.dream_entry_form.DreamEntry")
    def test_submit_entry_minimal(self, entry_class: MagicMock, db_class: MagicMock, client: TestClient):
        set_session(client, {"user_id": 3})
        db_instance = db_class.return_value
        entry_instance = entry_class.return_value
        user_instance = db_instance.get.return_value
        entryData = {"title": "New Test Entry!", "description": "Hello world, I am the description", "public": "True"}

        response = client.post("/", data=entryData)

        assert response.status_code == 200
        assert response.url == "http://testserver/"
        # Login check
        db_instance.get.assert_called_with(User, 3)
        # Building new entry
        callArgs = entry_class.call_args[1]
        assert callArgs.get("title") == entryData["title"]
        assert callArgs.get("description") == entryData["description"]
        assert callArgs.get("sense_sight") == None
        assert callArgs.get("public") == bool(entryData["public"])
        assert entry_instance.created_at != None
        user_instance.dream_entries.append.assert_called_with(entry_instance)
        # Saving new entry
        db_instance.add.assert_called_with(entry_instance)
        db_instance.commit.assert_called()

    @patch("app.forms.dream_entry_form.DreamEntry")
    def test_submit_entry_full(self, entry_class: MagicMock, db_class: MagicMock, client: TestClient):
        set_session(client, {"user_id": 3})
        db_instance = db_class.return_value
        entry_instance = entry_class.return_value
        user_instance = MagicMock()
        tag_instance = MagicMock()
        db_instance.get.side_effect = lambda m,v: tag_instance if m==Tag else user_instance
        entryData = {
            "title": "New Test Entry!", "description": "Hello world, I am the description", 
            "content_tags": ["Flying", "Chase"], "sense_sound": "on", "sense_pain": "on",
            "type_tags": ["Recurring"], "context": "Hello world, I am the context", 
            "context_tags": ["Vacation", "New Job"], "bed_time": "11:30", "wake_time": "15:30",
            "country": "testCountry", "state": "testState", "city": "testCity", "public": "True"
        }

        response = client.post("/", data=entryData)

        assert response.status_code == 200
        assert response.url == "http://testserver/"
        # Login check
        db_instance.get.assert_called_with(User, 3)
        # Building new entry
        callArgs = entry_class.call_args[1]
        assert callArgs.get("title") == entryData["title"]
        assert callArgs.get("description") == entryData["description"]
        assert callArgs.get("sense_sight") == ("sense_sight" in entryData)
        assert callArgs.get("sense_sound") == ("sense_sound" in entryData)
        assert callArgs.get("sense_touch") == ("sense_touch" in entryData)
        assert callArgs.get("sense_smell") == ("sense_smell" in entryData)
        assert callArgs.get("sense_taste") == ("sense_taste" in entryData)
        assert callArgs.get("sense_pain") == ("sense_pain" in entryData)
        assert callArgs.get("sense_other") == ("sense_other" in entryData)
        assert callArgs.get("context") == entryData["context"]
        assert callArgs.get("bed_time") == time.fromisoformat(entryData["bed_time"])
        assert callArgs.get("wake_time") == time.fromisoformat(entryData["wake_time"])
        assert callArgs.get("country") == entryData["country"]
        assert callArgs.get("state") == entryData["state"]
        assert callArgs.get("city") == entryData["city"]
        assert callArgs.get("public") == bool(entryData["public"])
        assert entry_instance.created_at != None
        for tag in entryData["content_tags"] + entryData["type_tags"] + entryData["context_tags"]:
            db_instance.get.assert_any_call(Tag, tag)
            entry_instance.tags.append.assert_called_with(tag_instance)
        user_instance.dream_entries.append.assert_called_with(entry_instance)
        # Saving new entry
        db_instance.add.assert_called_with(entry_instance)
        db_instance.commit.assert_called()

    def test_submit_entry_guest(self, db_class: MagicMock, client: TestClient):
        set_session(client, {})
        db_instance = db_class.return_value
        entryData = {
            "title": "New Test Entry!",
            "description": "Hello world, I am the description",
            "public": "False",
        }

        response = client.post("/", data=entryData)

        assert response.status_code == 200
        assert response.url == "http://testserver/signup"
        assert "Dream entry temporarily stored" in unescape(response.text)
        db_instance.get.assert_not_called()
        db_instance.add.assert_not_called()
        db_instance.commit.assert_not_called()
