FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY invoice_db ./invoice_db
COPY scripts ./scripts

RUN pip install --no-cache-dir -e .

ENV INVOICEDB_PATH=/data/invoicedb.sqlite

ENTRYPOINT ["invoicedb"]
CMD ["--help"]