import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from kemono_dl import KemonoDL
from kemono_dl.exceptions import LoginError
from kemono_dl.models import Creator, FavoriteCreator, ParsedUrl, Post

TEST_DATA_PATH = "tests/data"


@pytest.fixture
def kemono_dl() -> KemonoDL:
    return KemonoDL()


@patch("kemono_dl.session.requests.Session.get")
def test_is_loggedin_true(mock_get, kemono_dl: KemonoDL) -> None:
    mock_get.return_value = Mock(ok=True)
    result = kemono_dl.isLoggedin(KemonoDL.COOMER_DOMAIN)
    assert result is True
    mock_get.assert_called_once_with(KemonoDL.COOMER_DOMAIN + "/api/v1/account")


@patch("kemono_dl.session.requests.Session.get")
def test_is_loggedin_false(mock_get, kemono_dl: KemonoDL) -> None:
    mock_get.return_value = Mock(ok=False)
    result = kemono_dl.isLoggedin(KemonoDL.COOMER_DOMAIN)
    assert result is False
    mock_get.assert_called_once_with(KemonoDL.COOMER_DOMAIN + "/api/v1/account")


@patch("kemono_dl.session.requests.Session.get")
def test_passed_ddos_guard_true(mock_get, kemono_dl: KemonoDL) -> None:
    mock_get.return_value = Mock(ok=True)
    result = kemono_dl.passed_DDOS_guard(KemonoDL.COOMER_DOMAIN)
    assert result is True
    mock_get.assert_called_once_with(KemonoDL.COOMER_DOMAIN)


@patch("kemono_dl.session.requests.Session.get")
def test_passed_ddos_guard_false(mock_get, kemono_dl: KemonoDL) -> None:
    mock_get.return_value = Mock(ok=False)
    result = kemono_dl.passed_DDOS_guard(KemonoDL.COOMER_DOMAIN)
    assert result is False
    mock_get.assert_called_once_with(KemonoDL.COOMER_DOMAIN)


@patch("kemono_dl.session.requests.Session.get")
def test_get_creator_posts(mock_get, kemono_dl: KemonoDL) -> None:
    with open(f"{TEST_DATA_PATH}/creator_posts.json", encoding="utf-8") as f:
        mock_data = json.load(f)

    mock_get.return_value = Mock(json=lambda: mock_data)
    post_ids = kemono_dl.get_creator_post_ids(KemonoDL.COOMER_DOMAIN, "SERVICE_123", "USER_123", 0)

    assert len(post_ids) == len(mock_data)
    assert post_ids == [post.get("id") for post in mock_data]
    mock_get.assert_called_once_with(KemonoDL.COOMER_DOMAIN + "/api/v1/SERVICE_123/user/USER_123", params={"o": 0})


@patch("kemono_dl.session.requests.Session.get")
def test_get_post_returns_post(mock_get, kemono_dl: KemonoDL) -> None:
    with open(f"{TEST_DATA_PATH}/post.json", encoding="utf-8") as f:
        mock_data = json.load(f)

    mock_get.return_value = Mock(json=lambda: mock_data)
    post = kemono_dl.get_post(KemonoDL.COOMER_DOMAIN, "SERVICE_123", "USER_123", "1103388334")

    assert post == Post(mock_data)
    mock_get.assert_called_once_with(KemonoDL.COOMER_DOMAIN + "/api/v1/SERVICE_123/user/USER_123/post/1103388334")


@patch("kemono_dl.session.requests.Session.get")
def test_get_post_returns_none_on_request_error(mock_get, kemono_dl: KemonoDL, capsys) -> None:
    mock_get.side_effect = RuntimeError("network down")

    result = kemono_dl.get_post(KemonoDL.COOMER_DOMAIN, "SERVICE_123", "USER_123", "1103388334")

    assert result is None

    captured = capsys.readouterr().out
    assert "[Error] unable to get post" in captured
    assert "network down" in captured

    mock_get.assert_called_once_with(KemonoDL.COOMER_DOMAIN + "/api/v1/SERVICE_123/user/USER_123/post/1103388334")


@patch("kemono_dl.session.requests.Session.get")
def test_get_post_returns_none_on_json_error(mock_get, kemono_dl: KemonoDL, capsys) -> None:
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("bad json")
    mock_get.return_value = mock_response

    result = kemono_dl.get_post(KemonoDL.COOMER_DOMAIN, "SERVICE_123", "USER_123", "1103388334")

    assert result is None

    captured = capsys.readouterr().out
    assert "[Error] unable to get post" in captured
    assert "bad json" in captured

    mock_get.assert_called_once_with(KemonoDL.COOMER_DOMAIN + "/api/v1/SERVICE_123/user/USER_123/post/1103388334")


@patch("kemono_dl.session.requests.Session.get")
def test_get_creator(mock_get, kemono_dl: KemonoDL) -> None:
    with open(f"{TEST_DATA_PATH}/creator_profile.json", encoding="utf-8") as f:
        mock_data = json.load(f)

    mock_get.return_value = Mock(json=lambda: mock_data)
    creator: Creator = kemono_dl.get_creator(KemonoDL.COOMER_DOMAIN, "SERVICE_123", "USER_123")

    assert creator == Creator(**mock_data)
    mock_get.assert_called_once_with(KemonoDL.COOMER_DOMAIN + "/api/v1/SERVICE_123/user/USER_123/profile")


def test_parse_url_match(kemono_dl: KemonoDL):
    expected = ParsedUrl(
        site="coomer",
        service="SERVICE_123",
        creator_id="USER_123",
    )
    result = kemono_dl.parse_url("https://coomer.st/SERVICE_123/user/USER_123")
    assert result == expected


def test_parse_url_no_match(kemono_dl: KemonoDL):
    expected = None
    result = kemono_dl.parse_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert result == expected


@patch("kemono_dl.session.requests.Session.post")
def test_login_true(mock_post, kemono_dl: KemonoDL) -> None:
    mock_post.return_value = Mock(ok=True)
    result = kemono_dl.login(KemonoDL.COOMER_DOMAIN, "username", "password")
    assert result is True
    mock_post.assert_called_once_with(
        KemonoDL.COOMER_DOMAIN + "/api/v1/authentication/login",
        data='{"username": "username", "password": "password"}',
    )


@patch("kemono_dl.session.requests.Session.post")
def test_login_false(mock_post, kemono_dl: KemonoDL) -> None:
    mock_post.return_value = Mock(ok=False)
    result = kemono_dl.login(KemonoDL.COOMER_DOMAIN, "username", "password")
    assert result is False
    mock_post.assert_called_once_with(
        KemonoDL.COOMER_DOMAIN + "/api/v1/authentication/login",
        data='{"username": "username", "password": "password"}',
    )


def test_get_all_creator_posts(kemono_dl: KemonoDL) -> None:
    with open(f"{TEST_DATA_PATH}/creator_posts.json", encoding="utf-8") as f:
        mock_data_page_1 = json.load(f)
    mock_data_page_2 = mock_data_page_1[:20]
    mock_data = [mock_data_page_1, mock_data_page_2]
    kemono_dl.get_creator_post_ids = Mock()
    kemono_dl.get_creator_post_ids.side_effect = mock_data
    result = kemono_dl.get_all_creator_post_ids(
        KemonoDL.COOMER_DOMAIN,
        "SERVICE_123",
        "USER_123",
    )
    assert result == mock_data_page_1 + mock_data_page_2
    assert kemono_dl.get_creator_post_ids.call_count == 2


def test_get_all_creator_posts_limit(kemono_dl: KemonoDL) -> None:
    with open(f"{TEST_DATA_PATH}/creator_posts.json", encoding="utf-8") as f:
        mock_data_page_1 = json.load(f)
    mock_data_page_2 = mock_data_page_1[:20]
    mock_data = [mock_data_page_1, mock_data_page_2]
    kemono_dl.get_creator_post_ids = Mock()
    kemono_dl.get_creator_post_ids.side_effect = mock_data
    result = kemono_dl.get_all_creator_post_ids(
        KemonoDL.COOMER_DOMAIN,
        "SERVICE_123",
        "USER_123",
        10,
    )
    assert result == mock_data_page_1[:10]
    assert kemono_dl.get_creator_post_ids.call_count == 1


@patch("kemono_dl.session.requests.Session.get")
def test_get_favorit_creators_loggedin(mock_get, kemono_dl: KemonoDL) -> None:
    kemono_dl.isLoggedin = Mock()
    kemono_dl.isLoggedin.return_value = True

    with open(f"{TEST_DATA_PATH}/favorite_creators.json", encoding="utf-8") as f:
        mock_data = json.load(f)

    mock_get.return_value = Mock(json=lambda: mock_data)
    result = kemono_dl.get_favorit_creators(KemonoDL.COOMER_DOMAIN)

    assert result == [FavoriteCreator(**fav) for fav in mock_data]
    mock_get.assert_called_once_with(
        KemonoDL.COOMER_DOMAIN + "/api/v1/account/favorites",
        params={"type": "artist"},
    )


def test_get_favorit_creators_not_loggedin(kemono_dl: KemonoDL) -> None:
    kemono_dl.isLoggedin = Mock()
    kemono_dl.isLoggedin.return_value = False
    kemono_dl.get_favorit_creators(KemonoDL.COOMER_DOMAIN)


# @patch("kemono_dl.session.requests.Session.get")
# def test_get_favorit_posts_loggedin(mock_get, kemono_dl: KemonoDL) -> None:
#     kemono_dl.isLoggedin = Mock()
#     kemono_dl.isLoggedin.return_value = True

#     with open(f"{TEST_DATA_PATH}/favorite_posts.json", encoding="utf-8") as f:
#         mock_data = json.load(f)

#     mock_get.return_value = Mock(json=lambda: mock_data)
#     result = kemono_dl.get_favorit_post_ids(KemonoDL.COOMER_DOMAIN)

#     assert result == [Post(**fav) for fav in mock_data]
#     mock_get.assert_called_once_with(
#         KemonoDL.COOMER_DOMAIN + "/api/v1/account/favorites",
#         params={"type": "post"},
#     )


def test_get_favorit_posts_not_loggedin(kemono_dl: KemonoDL) -> None:
    kemono_dl.isLoggedin = Mock()
    kemono_dl.isLoggedin.return_value = False
    kemono_dl.get_favorit_post_ids(KemonoDL.COOMER_DOMAIN)


@patch("http.cookiejar.MozillaCookieJar")
def test_load_cookies(mock_cookiejar_cls, kemono_dl: KemonoDL):
    mock_cookie = MagicMock()
    mock_cookiejar = MagicMock()
    mock_cookiejar.__iter__.return_value = [mock_cookie]
    mock_cookiejar.load = MagicMock()

    mock_cookiejar_cls.return_value = mock_cookiejar

    my_loader = kemono_dl
    my_loader.session = MagicMock()
    my_loader.session.cookies.set_cookie = MagicMock()

    my_loader.load_cookies("dummy_cookie_file.txt")

    mock_cookiejar.load.assert_called_once_with("dummy_cookie_file.txt")
    my_loader.session.cookies.set_cookie.assert_called_once_with(mock_cookie)
