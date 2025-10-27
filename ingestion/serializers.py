from rest_framework import serializers
from .models import FileImport
from ingestion.models import Category, Transaction, Rule

class FileImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileImport
        fields = "__all__"
        read_only_fields = (
            "id",
            "status",
            "error_message",
            "checksum_sha256",
            "size_bytes",
            "storage_path",
            "created_at",
            "updated_at",
        )


class ImportUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "type", "reference_count"]
        read_only_fields = ("id", "reference_count")


class TransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "booking_date",
            "amount",
            "currency",
            "description_raw",
            "counterparty",
            "category",
        ]


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = [
            "id",
            "user_id",
            "name",
            "priority",
            "enabled",
            "match_type",
            "match_value",
            "action_set_category",
            "action_mark_transfer",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at", "user_id")
