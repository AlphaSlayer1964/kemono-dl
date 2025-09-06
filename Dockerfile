FROM python:3

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir .

CMD ["kemono-dl"]
