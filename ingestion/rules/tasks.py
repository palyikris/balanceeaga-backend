from celery import shared_task
from .utils import apply_rules_for_user


@shared_task
def apply_rules_task(user_id: str):
    count = apply_rules_for_user(user_id)
    print(f"Applied rules for user={user_id}, categorized {count} transactions.")
    return count
