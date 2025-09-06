FROM python:3

COPY . ./src

RUN pip install --no-cache-dir -r ./src/requirements.txt
RUN pip install --no-cache-dir --compile -e ./src && pip cache purge

ENTRYPOINT [ "kemono-dl" ]
