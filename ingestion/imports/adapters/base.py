import csv
import io
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from ingestion.models import Transaction


class BaseCsvAdapter:
    date_formats = ["%Y.%m.%d", "%Y-%m-%d", "%d.%m.%Y"]

    def __init__(self, raw_bytes: bytes, user_id: str, import_id: UUID):
        self.raw_bytes = raw_bytes
        self.user_id = user_id
        self.import_id = import_id

    def read_csv(self, delimiter=";", encoding="utf-8-sig"):
        text = self.raw_bytes.decode(encoding, errors="ignore")
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        return list(reader)

    def try_parse_date(self, value):
        for fmt in self.date_formats:
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except Exception:
                continue
        return None

    def bulk_insert(self, transactions: list[dict]):
        if not transactions:
            return []
        objs = [Transaction(**t) for t in transactions]
        Transaction.objects.bulk_create(objs, ignore_conflicts=True)
        return objs
