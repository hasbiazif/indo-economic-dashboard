FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY data_fetchers/ ./data_fetchers/
COPY forecasting/ ./forecasting/
COPY dashboard/ ./dashboard/
COPY deploy/start.sh /start.sh

RUN chmod +x /start.sh

RUN useradd -m -u 1000 appuser
RUN chown -R appuser:appuser /app

EXPOSE 7860

USER appuser
CMD ["/start.sh"]
