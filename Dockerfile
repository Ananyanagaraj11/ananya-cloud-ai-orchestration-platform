FROM python:3.11-slim
WORKDIR /app
COPY requirements-render.txt .
RUN pip install --no-cache-dir -r requirements-render.txt
COPY . .
RUN mkdir -p data
EXPOSE 8040
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8040"]
