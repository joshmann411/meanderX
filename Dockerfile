FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir 'pip>=23.0' poetry-core
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false && poetry install --no-dev
COPY . /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
