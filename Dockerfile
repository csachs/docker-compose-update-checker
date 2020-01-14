ARG BASE=python:3.8.1-alpine3.11
FROM ${BASE}

COPY docker-check-tags.py /

RUN pip install pyyaml requests

USER nobody

CMD ["python", "/docker-check-tags.py", "/docker-compose.yml"]
