from celery import shared_task
from django.db import transaction
from ingestion.models import Transaction
from .utils import compute_txn_hash


@shared_task
def deduplicate_transactions(user_id: str):
    """
    Deduplicate all transactions for a user.
    """
    with transaction.atomic():
        txns = list(Transaction.objects.filter(user_id=user_id))
        seen = set()
        duplicates = []

        for t in txns:
            h = compute_txn_hash(t)
            if h in seen:
                duplicates.append(t.id)
            else:
                seen.add(h)

        if duplicates:
            Transaction.objects.filter(id__in=duplicates).delete()
            print(
                f"Removed {len(duplicates)} duplicate transactions for user={user_id}"
            )
        else:
            print(f"No duplicates found for user={user_id}")
