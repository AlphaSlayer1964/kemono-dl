FROM python:3

COPY . .
RUN pip install .

ENTRYPOINT [ "kemono-dl" ]
