import hashlib
from django.db import transaction
from ingestion.models import Transaction


def compute_txn_hash(txn):
    key = f"{txn.user_id}|{txn.booking_date}|{txn.amount}|{txn.description_raw.strip()}|{txn.counterparty.strip()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
