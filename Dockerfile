FROM python:3.10-slim


WORKDIR /app/demo

# Install deps
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY demo/ /app/demo/

ENV PYTHONPATH="${PYTHONPATH}:/app"

ENTRYPOINT [ "python3", "/app/demo/app.py" ]
