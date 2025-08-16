import requests


class CustomSession(requests.Session):
    def request(self, method, url, *args, **kwargs):
        response = super().request(method, url, *args, **kwargs)
        content_type = response.headers.get("Content-Type", "")
        # why is the api content type text/css and not application/json!
        if content_type == "text/css":
            response.encoding = "UTF-8"
        return response
