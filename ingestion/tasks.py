from celery import shared_task
from django.db import transaction
from .models import FileImport, FileStatus, FileAdapter, FileSource
import time
from ingestion.imports.detect import detect_profile, UnknownProfileError
from ingestion.imports.factory import get_adapter
from celery.utils.log import get_task_logger
from django.conf import settings
from pathlib import Path
from ingestion.transactions.tasks import deduplicate_transactions
from ingestion.rules.tasks import apply_rules_task


logger = get_task_logger(__name__)


@shared_task
def parse_import_task(import_id: str):
    logger.info(f"Starting parse_import_task for import_id={import_id}")
    try:
        with transaction.atomic():
            fi = FileImport.objects.select_for_update().get(id=import_id)
            fi.status = FileStatus.PROCESSING
            fi.save(update_fields=["status"])
            logger.info(f"Set status=PROCESSING for {fi.id}")

            file_path = Path(settings.MEDIA_ROOT) / fi.storage_path
            with open(file_path, "rb") as f:
                raw_bytes = f.read()
            logger.info(f"Read {len(raw_bytes)} bytes from {fi.storage_path}")

            try:
                profile = detect_profile(raw_bytes)
                logger.info(f"Detected profile: {profile}")
            except UnknownProfileError as e:
                fi.status = FileStatus.FAILED
                fi.error_message = str(e)
                fi.save(update_fields=["status", "error_message"])
                logger.error(f"Unknown profile: {e}")
                return

            fi.adapter_hint = FileAdapter.CSV
            fi.source_hint = FileSource.OTP if profile == "OTP" else FileSource.REVOLUT
            fi.save(update_fields=["adapter_hint", "source_hint"])

            adapter_class = get_adapter(fi.adapter_hint, fi.source_hint)
            adapter = adapter_class(raw_bytes, fi.user_id, fi.id)

            transactions = adapter.parse()
            logger.info(f"Parsed {len(transactions)} transactions.")

            adapter.bulk_insert(transactions)
            logger.info(f"Inserted transactions into database.")

            deduplicate_transactions.delay(fi.user_id)
            logger.info(f"Triggered deduplication task for user {fi.user_id}")

            apply_rules_task.delay(fi.user_id)
            logger.info(f"Triggered apply_rules_task for user {fi.user_id}")

            fi.status = FileStatus.PARSED
            fi.save(update_fields=["status"])
            logger.info(f"Task completed successfully for {fi.id}")

    except Exception as e:
        logger.exception(f"parse_import_task failed for {import_id}")
        FileImport.objects.filter(id=import_id).update(
            status=FileStatus.FAILED, error_message=str(e)
        )
