import hashlib
from unittest.mock import MagicMock, mock_open, patch

import pytest

from kemono_dl.utils import format_bytes, get_sha256_hash, get_sha256_url_content, make_path_safe


def test_get_sha256_hash():
    # Prepare fake binary content
    fake_content = [b"hello", b"world"]
    m_open = mock_open()
    m_open.return_value.__iter__ = lambda self: iter(fake_content)

    with patch("builtins.open", m_open):
        with patch("kemono_dl.utils.iter", side_effect=lambda x, y: iter(fake_content)):
            result = get_sha256_hash("fake_path.txt")

    # Verify SHA256 hash matches expected
    sha256 = hashlib.sha256()
    for chunk in fake_content:
        sha256.update(chunk)
    expected = sha256.hexdigest()

    assert result == expected


@pytest.mark.parametrize(
    "size,expected",
    [
        (999, "999.00 B"),
        (2048, "2.00 KiB"),
        (1048576, "1.00 MiB"),
        (1073741824, "1.00 GiB"),
        (1099511627776, "1.00 TiB"),
    ],
)
def test_format_bytes(size, expected):
    assert format_bytes(size) == expected


@pytest.mark.parametrize(
    "value,replace,expected",
    [
        ("filename<>", "-", "filename--"),
        ("inva|id:name?.txt", "_", "inva_id_name_.txt"),
        ("normal", "#", "normal"),
    ],
)
def test_make_path_safe(value, replace, expected):
    assert make_path_safe(value, replace) == expected


def test_get_sha256_url_content():
    # Simulate HTTP response with chunked content
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.iter_content.return_value = [b"data", b"123"]
    mock_session.get.return_value = mock_response

    result = get_sha256_url_content(mock_session, "http://fake-url.com")

    sha256 = hashlib.sha256()
    for chunk in [b"data", b"123"]:
        sha256.update(chunk)
    expected = sha256.hexdigest()

    assert result == expected
    mock_session.get.assert_called_once_with("http://fake-url.com", stream=True)
