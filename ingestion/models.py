from django.db import models
import uuid


class FileStatus(models.TextChoices):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    PARSED = "parsed"
    FAILED = "failed"


class FileAdapter(models.TextChoices):
    CSV = "csv"
    OFX = "ofx"
    QIF = "qif"
    UNKNOWN = "unknown"


class FileSource(models.TextChoices):
    OTP = "otp"
    REVOLUT = "revolut"
    IBKR = "ibkr"
    OTHER = "other"


class FileImport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=64)  # Supabase user UUID string
    original_name = models.TextField()
    storage_path = models.TextField(unique=True)  # MEDIA_ROOT-on belüli relatív út
    mime_type = models.TextField(null=True, blank=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    checksum_sha256 = models.CharField(max_length=64, null=True, blank=True)

    adapter_hint = models.CharField(
        max_length=16, choices=FileAdapter.choices, default=FileAdapter.UNKNOWN
    )
    source_hint = models.CharField(
        max_length=16, choices=FileSource.choices, default=FileSource.OTHER
    )
    status = models.CharField(
        max_length=16, choices=FileStatus.choices, default=FileStatus.UPLOADED
    )
    error_message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=64)
    import_file = models.ForeignKey(
        "ingestion.FileImport", on_delete=models.CASCADE, related_name="transactions"
    )
    booking_date = models.DateField(null=True, blank=True)
    value_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=8, default="HUF")
    description_raw = models.TextField(blank=True)
    description_norm = models.TextField(blank=True)
    counterparty = models.TextField(blank=True)
    reference = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        "ingestion.Category", null=True, blank=True, on_delete=models.SET_NULL
    )
    is_transfer = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transactions"
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["booking_date"]),
        ]


class RuleMatchType(models.TextChoices):
    CONTAINS = "contains"
    REGEX = "regex"
    EQUALS = "equals"
    AMOUNT_RANGE = "amount_range"


class Rule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    priority = models.PositiveIntegerField(default=100)
    enabled = models.BooleanField(default=True)

    match_type = models.CharField(max_length=32, choices=RuleMatchType.choices)
    match_value = models.TextField()  # text or JSON (for range, etc.)

    action_set_category = models.CharField(max_length=64, null=True, blank=True)
    action_mark_transfer = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rules"
        ordering = ["priority"]


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=64)
    name = models.CharField(max_length=64)
    reference_count = models.IntegerField(default=0)
    type = models.CharField(
        max_length=16,
        choices=[
            ("income", "Income"),
            ("expense", "Expense"),
            ("transfer", "Transfer"),
        ],
    )

    def __str__(self):
        return self.name
