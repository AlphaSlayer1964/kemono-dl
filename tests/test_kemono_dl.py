import json
from http.cookiejar import LoadError
from unittest.mock import MagicMock, Mock, patch

import pytest
from requests import HTTPError

from kemono_dl import KemonoDL
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
    mock_get.assert_called_once_with(
        KemonoDL.COOMER_DOMAIN + "/api/v1/account",
        headers={"accept": "text/css"},
    )


@patch("kemono_dl.session.requests.Session.get")
def test_is_loggedin_false(mock_get, kemono_dl: KemonoDL) -> None:
    mock_get.return_value = Mock(ok=False)
    result = kemono_dl.isLoggedin(KemonoDL.COOMER_DOMAIN)
    assert result is False
    mock_get.assert_called_once_with(
        KemonoDL.COOMER_DOMAIN + "/api/v1/account",
        headers={"accept": "text/css"},
    )


@patch("kemono_dl.session.requests.Session.get")
def test_get_creator_posts(mock_get, kemono_dl: KemonoDL) -> None:
    with open(f"{TEST_DATA_PATH}/creator_posts.json", encoding="utf-8") as f:
        mock_data = json.load(f)

    mock_get.return_value = Mock(json=lambda: mock_data)
    post_ids = kemono_dl.get_creator_post_ids(KemonoDL.COOMER_DOMAIN, "SERVICE_123", "USER_123", 0)

    assert len(post_ids) == len(mock_data)
    assert post_ids == [post.get("id") for post in mock_data]
    mock_get.assert_called_once_with(
        KemonoDL.COOMER_DOMAIN + "/api/v1/SERVICE_123/user/USER_123/posts",
        params={"o": 0},
        headers={"accept": "text/css"},
    )


@patch("kemono_dl.session.requests.Session.get")
def test_get_post(mock_get, kemono_dl: KemonoDL) -> None:
    with open(f"{TEST_DATA_PATH}/post.json", encoding="utf-8") as f:
        mock_data = json.load(f)

    mock_get.return_value = Mock(json=lambda: mock_data)
    post = kemono_dl.get_post(KemonoDL.COOMER_DOMAIN, "SERVICE_123", "USER_123", "1103388334")

    assert post == Post(mock_data)
    mock_get.assert_called_once_with(
        KemonoDL.COOMER_DOMAIN + "/api/v1/SERVICE_123/user/USER_123/post/1103388334",
        headers={"accept": "text/css"},
    )


@patch("kemono_dl.session.requests.Session.get")
def test_get_post_exception(mock_get, kemono_dl: KemonoDL, capsys) -> None:
    mock_get.side_effect = ValueError("Json Error")

    result = kemono_dl.get_post(KemonoDL.COOMER_DOMAIN, "SERVICE_123", "USER_123", "1103388334")

    assert result is None

    captured = capsys.readouterr().out
    assert "[Error] Failed to fetch post from" in captured
    assert "Json Error" in captured

    mock_get.assert_called_once_with(
        KemonoDL.COOMER_DOMAIN + "/api/v1/SERVICE_123/user/USER_123/post/1103388334",
        headers={"accept": "text/css"},
    )


@patch("kemono_dl.session.requests.Session.get")
def test_get_creator(mock_get, kemono_dl: KemonoDL) -> None:
    with open(f"{TEST_DATA_PATH}/creator_profile.json", encoding="utf-8") as f:
        mock_data = json.load(f)

    mock_get.return_value = Mock(json=lambda: mock_data)
    creator = kemono_dl.get_creator_profile(KemonoDL.COOMER_DOMAIN, "SERVICE_123", "USER_123")

    assert creator == Creator(**mock_data)
    mock_get.assert_called_once_with(KemonoDL.COOMER_DOMAIN + "/api/v1/SERVICE_123/user/USER_123/profile", headers={"accept": "text/css"})


def test_parse_url_match_creator(kemono_dl: KemonoDL):
    expected = {"site": "coomer", "service": "SERVICE_123", "creator_id": "USER_123", "post_id": None}
    result = kemono_dl.parse_url("https://coomer.st/SERVICE_123/user/USER_123")
    assert result == expected


def test_parse_url_match_post(kemono_dl: KemonoDL):
    expected = {"site": "coomer", "service": "SERVICE_123", "creator_id": "USER_123", "post_id": "POST_123"}
    result = kemono_dl.parse_url("https://coomer.st/SERVICE_123/user/USER_123/post/POST_123")
    assert result == expected


def test_parse_url_no_match(kemono_dl: KemonoDL):
    expected = None
    result = kemono_dl.parse_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert result == expected


@patch("kemono_dl.session.requests.Session.post")
def test_login(mock_post, kemono_dl: KemonoDL) -> None:
    response = Mock()
    response.raise_for_status = Mock()
    mock_post.return_value = response

    result = kemono_dl.login(KemonoDL.COOMER_DOMAIN, "username", "password")

    assert result is True
    mock_post.assert_called_once_with(
        KemonoDL.COOMER_DOMAIN + "/api/v1/authentication/login",
        json={"username": "username", "password": "password"},
    )


@patch("kemono_dl.session.requests.Session.post")
def test_login_exception(mock_post, kemono_dl: KemonoDL) -> None:
    response = Mock()
    response.raise_for_status.side_effect = HTTPError("401 Client Error")
    mock_post.return_value = response

    result = kemono_dl.login(KemonoDL.COOMER_DOMAIN, "username", "password")

    assert result is False
    mock_post.assert_called_once_with(
        KemonoDL.COOMER_DOMAIN + "/api/v1/authentication/login",
        json={"username": "username", "password": "password"},
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
def test_get_favorit_creators(mock_get, kemono_dl: KemonoDL) -> None:
    with open(f"{TEST_DATA_PATH}/favorite_creators.json", encoding="utf-8") as f:
        mock_data = json.load(f)

    mock_get.return_value = Mock(json=lambda: mock_data)
    result = kemono_dl.get_favorit_creators(KemonoDL.COOMER_DOMAIN)

    assert result == [FavoriteCreator(**fav) for fav in mock_data]
    mock_get.assert_called_once_with(
        KemonoDL.COOMER_DOMAIN + "/api/v1/account/favorites",
        params={"type": "artist"},
        headers={"accept": "text/css"},
    )


@patch("http.cookiejar.MozillaCookieJar")
def test_load_cookies(mock_cookiejar_cls, kemono_dl: KemonoDL):
    mock_cookie = MagicMock()
    mock_jar = MagicMock()
    mock_jar.__iter__.return_value = [mock_cookie]
    mock_jar.load = MagicMock()
    mock_cookiejar_cls.return_value = mock_jar

    kemono_dl.session = MagicMock()
    kemono_dl.session.cookies.set_cookie = MagicMock()

    result = kemono_dl.load_cookies("cookies.txt")

    assert result is True
    mock_jar.load.assert_called_once_with("cookies.txt")
    kemono_dl.session.cookies.set_cookie.assert_called_once_with(mock_cookie)


@patch("http.cookiejar.MozillaCookieJar")
def test_load_cookies_exception(mock_cookiejar_cls, kemono_dl: KemonoDL, capsys):
    mock_jar = MagicMock()
    mock_jar.load.side_effect = LoadError()
    mock_cookiejar_cls.return_value = mock_jar

    result = kemono_dl.load_cookies("cookies.txt")

    assert result is False
    mock_jar.load.assert_called_once_with("cookies.txt")
    captured = capsys.readouterr().out
    assert "[Error] Failed to load cookies from cookies.txt" in captured
