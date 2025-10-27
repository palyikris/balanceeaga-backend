import re
from ingestion.models import Rule, RuleMatchType, Transaction, Category
from django.db.models import Q


def apply_rules_for_user(user_id: str) -> int:
    """
    Apply all enabled rules for a user to their uncategorized transactions.

    Each rule can match by:
      - CONTAINS: substring match (case-insensitive)
      - REGEX: regular expression
      - EQUALS: exact string match
      - AMOUNT_RANGE: numeric range match, e.g. "-10000,0"

    Returns:
        int: number of transactions updated
    """
    # Fetch enabled rules in order of priority
    rules = list(
        Rule.objects.filter(
            Q(user_id=user_id) | Q(user_id="default"), enabled=True
        ).order_by("priority")
    )

    # Fetch uncategorized transactions
    txns = list(Transaction.objects.filter(user_id=user_id, category__isnull=True))
    if not txns or not rules:
        return 0

    updated_count = 0

    # Preload category mapping (UUID -> Category)
    category_map = {
        str(cat.id): cat
        for cat in Category.objects.filter(Q(user_id=user_id) | Q(user_id="default"))
    }

    # Track which categories need updating
    updated_categories = set()

    for txn in txns:
        text = f"{txn.description_raw or ''} {txn.counterparty or ''}".lower()

        for rule in rules:
            # --- match by text patterns ---
            if (
                rule.match_type == RuleMatchType.CONTAINS
                and rule.match_value.lower() in text
            ):
                category = category_map.get(str(rule.action_set_category))
                if category:
                    txn.category = category
                    updated_count += 1
                    category.reference_count += 1
                    updated_categories.add(category)
                break

            elif rule.match_type == RuleMatchType.REGEX and re.search(
                rule.match_value, text, re.I
            ):
                category = category_map.get(str(rule.action_set_category))
                if category:
                    txn.category = category
                    updated_count += 1
                    category.reference_count += 1
                    updated_categories.add(category)
                break

            elif (
                rule.match_type == RuleMatchType.EQUALS
                and text.strip() == rule.match_value.lower()
            ):
                category = category_map.get(str(rule.action_set_category))
                if category:
                    txn.category = category
                    updated_count += 1
                    category.reference_count += 1
                    updated_categories.add(category)
                break

            # --- match by numeric range ---
            elif rule.match_type == RuleMatchType.AMOUNT_RANGE:
                try:
                    lo, hi = map(float, rule.match_value.split(","))
                    if lo <= float(txn.amount) <= hi:
                        category = category_map.get(str(rule.action_set_category))
                        if category:
                            txn.category = category
                            updated_count += 1
                            category.reference_count += 1
                            updated_categories.add(category)
                        break
                except Exception:
                    continue

    if updated_count:
        Transaction.objects.bulk_update(txns, ["category"])

    if updated_categories:
        Category.objects.bulk_update(updated_categories, ["reference_count"])

    return updated_count
