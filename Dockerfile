FROM python:3

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./kemono-dl/ .

ENTRYPOINT [ "python", ".__main__.py" ]
