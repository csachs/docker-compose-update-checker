ARG BASE=python:3.7.4-alpine3.10
FROM ${BASE}

COPY docker-check-tags.py /

RUN pip install pyyaml requests

USER nobody

CMD ["python", "/docker-check-tags.py", "/docker-compose.yml"]
