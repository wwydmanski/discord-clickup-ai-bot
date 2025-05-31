import builtins
from unittest.mock import Mock, patch

from bot import ClickUpClient


def test_get_folder_lists_success():
    client = ClickUpClient("token", "list", folder_id="folder")
    expected = [{"id": "1"}, {"id": "2"}]
    with patch("bot.requests.get") as mock_get:
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"lists": expected}
        mock_get.return_value = mock_resp

        lists = client.get_folder_lists()
        assert lists == expected
        mock_get.assert_called_once_with(
            "https://api.clickup.com/api/v2/folder/folder/list",
            headers=client.headers,
        )


def test_get_folder_lists_no_folder():
    client = ClickUpClient("token", "list")
    assert client.get_folder_lists() == []


def test_get_newest_list_from_folder():
    client = ClickUpClient("token", "list", folder_id="folder")
    lists = [{"id": "1"}, {"id": "2"}]
    with patch.object(client, "get_folder_lists", return_value=lists):
        newest = client.get_newest_list_from_folder()
        assert newest == lists[-1]


def test_create_task_success():
    client = ClickUpClient("token", "123")
    with patch("bot.requests.post") as mock_post:
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"id": "task"}
        mock_post.return_value = mock_resp

        result = client.create_task("Title", "Desc")
        assert result == {"id": "task"}
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == "https://api.clickup.com/api/v2/list/123/task"


def test_update_task_status():
    client = ClickUpClient("token", "list")
    with patch("bot.requests.put") as mock_put:
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"status": "complete"}
        mock_put.return_value = mock_resp

        result = client.update_task_status("id1", "complete")
        assert result == {"status": "complete"}
        mock_put.assert_called_once()
        assert mock_put.call_args[0][0] == "https://api.clickup.com/api/v2/task/id1"
