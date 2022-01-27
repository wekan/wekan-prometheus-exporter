FROM python:3.9-alpine3.13

COPY exporter.py /exporter.py
COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

CMD ["/exporter.py"]
