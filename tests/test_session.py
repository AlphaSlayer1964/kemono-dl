from unittest.mock import MagicMock, patch

import pytest

from kemono_dl.exceptions import DDOSGuardError
from kemono_dl.session import CustomSession


@patch("requests.Session.request")
def test_custom_session_raises_ddos_guard(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_request.return_value = mock_response

    session = CustomSession()

    with pytest.raises(DDOSGuardError):
        session.get("http://example.com")


@patch("requests.Session.request")
def test_custom_session_allows_non_403(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    session = CustomSession()
    response = session.get("http://example.com")

    assert response.status_code == 200
