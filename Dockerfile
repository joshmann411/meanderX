FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir 'pip>=23.0' poetry-core poetry
# avoid poetry creating virtualenvs inside the container
ENV POETRY_VIRTUALENVS_CREATE=false
# Install dependencies (including dev deps to avoid incompatible --no-dev flag)
RUN poetry install --no-interaction
COPY . /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
