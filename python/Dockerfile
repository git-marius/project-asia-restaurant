FROM python:3.12-alpine

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv venv && uv sync --frozen --no-dev

COPY . .

EXPOSE ${FLASK_PORT}

CMD ["uv", "run", "flask", "--app", "wsgi", "run", "--host=0.0.0.0", "--port=5000"]
#prod: CMD ["uv", "run", "gunicorn", "-b", "0.0.0.0:5000", "wsgi:app"]
