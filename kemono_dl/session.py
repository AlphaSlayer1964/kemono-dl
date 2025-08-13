import requests

from .exceptions import DDOSGuardError


class CustomSession(requests.Session):
    def request(self, method, url, *args, **kwargs):
        response = super().request(method, url, *args, **kwargs)
        if response.status_code == 403:
            raise DDOSGuardError(url)
        return response
