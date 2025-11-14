FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && \
    uv sync --frozen

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "fast_api:app", "--host", "0.0.0.0", "--port", "8000"]
