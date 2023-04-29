FROM python:3.10-slim

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.4.2 \
  PYTHONPATH="${PYTHONPATH}:/app"

# Install poetry
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app/demo

# Install deps
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Copy source code
COPY demo/ /app/demo/

ENTRYPOINT [ "python3", "/app/demo/app.py" ]
