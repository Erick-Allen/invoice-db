FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY invoice_db ./invoice_db
COPY api ./api
COPY server ./server
COPY scripts ./scripts
COPY manage.py ./manage.py

RUN pip install --no-cache-dir -e .

ENV INVOICEDB_PATH=/data/invoicedb.sqlite

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]