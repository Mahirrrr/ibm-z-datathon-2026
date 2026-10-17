# Second Look API + dashboard. Built and run with rootless Podman on IBM LinuxONE (s390x).
# The pipeline stays outside the image; the container only serves secondlook.db, mounted read-only.
#
#   podman build -t second-look .
#   podman run -d --name second-look --read-only --cap-drop=ALL --security-opt no-new-privileges \
#     -p 127.0.0.1:8080:8000 -v ./secondlook.db:/app/secondlook.db:ro,Z second-look
FROM docker.io/library/python:3.12-slim

COPY requirements-api.txt /tmp/requirements-api.txt
RUN pip install --no-cache-dir -r /tmp/requirements-api.txt && rm /tmp/requirements-api.txt

WORKDIR /app
COPY api/ api/
COPY pipeline/__init__.py pipeline/config.py pipeline/codebook.py pipeline/
COPY dashboard/ dashboard/

USER 1000:1000
ENV PYTHONDONTWRITEBYTECODE=1 SECOND_LOOK_CONTAINER=podman
EXPOSE 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
