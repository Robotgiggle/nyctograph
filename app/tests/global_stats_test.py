from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from html import unescape

from ..models import GlobalStats
from .testutils import *

@patch("app.utils.Session")
@patch("app.routers.global_stats.select")
class TestGlobalStats:
    def test_stats_basic(self, select_fn: MagicMock, db_class: MagicMock, client: TestClient):
        db_obj = db_class.return_value
        select_obj = select_fn.return_value
        query_obj = select_obj.where.return_value
        stats_obj = db_obj.execute.return_value.scalar.return_value
        tag_list_obj = db_obj.execute.return_value.all.return_value
        
        response = client.get("/global-stats")

        assert response.status_code == 200
        assert response.url == "http://testserver/global-stats"
        # assert various calls to make sure the page is doing what it should
        select_fn.assert_called()
        select_obj.where.assert_called()
        db_obj.execute.assert_any_call(query_obj)
        stats_obj.total_entries.__str__.assert_called()
        stats_obj.avg_sleep_duration.__round__.assert_called()
        stats_obj.sight_rate.__mul__.assert_called()
        tag_list_obj.__bool__.assert_called()
        tag_list_obj.__iter__.assert_called()
        # page should not show no-entries error
        assert "Sensory Experiences" in response.text
        assert "There are no public entries matching this set of filters!" not in response.text

    def test_stats_no_entries(self, select_fn: MagicMock, db_class: MagicMock, client: TestClient):
        stats_obj = db_class.return_value.execute.return_value.scalar.return_value
        stats_obj.total_entries = 0
        
        response = client.get("/global-stats")

        assert response.status_code == 200
        assert response.url == "http://testserver/global-stats"
        # page *should* show no-entries error
        assert "Sensory Experiences" not in response.text
        assert "There are no public entries matching this set of filters!" in response.text

    def test_stats_no_tags(self, select_fn: MagicMock, db_class: MagicMock, client: TestClient):
        db_obj = db_class.return_value
        db_obj.execute.return_value.all.return_value = []
        
        response = client.get("/global-stats")

        assert response.status_code == 200
        assert response.url == "http://testserver/global-stats"
        # page should not show no-entries error
        assert "Sensory Experiences" in response.text
        assert "There are no public entries matching this set of filters!" not in response.text
        # page *should* show no-tags and no-associations errors
        assert "No special dream types recorded." in response.text
        assert "No dream content tags found." in response.text
        assert "No real-world context tags found." in response.text
        assert "No tag associations found." in response.text