from django.shortcuts import render
import hashlib, os
from django.conf import settings
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import FileImport, FileStatus
from .serializers import FileImportSerializer
from .tasks import parse_import_task, apply_rules_task
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .serializers import ImportUploadSerializer, TransactionSerializer
from pathlib import Path
from django.utils.text import get_valid_filename
import time
from ingestion.models import Transaction
from .models import Rule
from .serializers import RuleSerializer
from .models import Category
from .serializers import CategorySerializer
from .utils import get_user_id, get_access_token


def sha256sum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


class ImportViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = FileImport.objects.all().order_by("-created_at")
    serializer_class = FileImportSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        uid = get_user_id(self.request)
        access_token = get_access_token(self.request)

        if access_token is None or uid is None:
            return Response(
                {"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        qs = super().get_queryset()
        return qs.filter(user_id=uid) if uid else qs.none()

    @extend_schema(
        request=ImportUploadSerializer,  # multipart/form-data file mezővel
        responses=FileImportSerializer,
        parameters=[
            OpenApiParameter(
                name="X-User-Id",
                required=False,
                location=OpenApiParameter.HEADER,
                description="Supabase user id (dev módban opcionális)",
            ),
        ],
        summary="Fájl import indítása",
        description="CSV/OFX/QIF fájl feltöltése és feldolgozásra küldése.",
    )
    def create(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        user_id = get_user_id(request)
        access_token = get_access_token(request)

        if access_token is None or user_id is None:
            return Response(
                {"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not file:
            return Response({"detail": "No file"}, status=400)

        media_root = Path(settings.MEDIA_ROOT)
        import_dir = media_root / "imports"
        import_dir.mkdir(parents=True, exist_ok=True)

        safe_name = get_valid_filename(file.name)
        import_rel = f"imports/{safe_name}"
        full_path = media_root / import_rel

        # név ütközés elkerülés
        base, ext = os.path.splitext(import_rel)
        i = 1
        while full_path.exists():
            import_rel = f"{base}_{i}{ext}"
            full_path = settings.MEDIA_ROOT / import_rel
            i += 1

        with open(full_path, "wb+") as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        checksum = sha256sum(str(full_path))
        rec = FileImport.objects.create(
            user_id=user_id,
            original_name=file.name,
            storage_path=import_rel,
            mime_type=file.content_type,
            size_bytes=file.size,
            checksum_sha256=checksum,
            status=FileStatus.UPLOADED,
        )
        # queue feldolgozásra
        parse_import_task.delay(str(rec.id))
        s = self.get_serializer(rec)
        time.sleep(2)
        return Response(s.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Delete an import",
        description="Deletes a file import by ID.",
        responses={204: None, 404: {"detail": "Not found"}},
    )
    def destroy(self, request, pk=None):
        try:
            instance = self.get_queryset().get(pk=pk)
        except FileImport.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        file_path = Path(settings.MEDIA_ROOT) / instance.storage_path
        if file_path.exists():
            file_path.unlink()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["delete"], url_path="delete_all")
    def delete_all_imports(self, request):
        queryset = self.get_queryset()
        count = queryset.count()
        for instance in queryset:
            file_path = Path(settings.MEDIA_ROOT) / instance.storage_path
            if file_path.exists():
                file_path.unlink()
        queryset.delete()
        return Response({"deleted": count}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="latest")
    def latest_import(self, request):
        uid = get_user_id(request)
        access_token = get_access_token(request)

        if access_token is None or uid is None:
            return Response(
                {"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        print("latest import for", uid)
        allImport = FileImport.objects.all()
        latest = allImport.filter(user_id=uid).order_by("-created_at").first()
        if not latest:
            return Response({"detail": "No imports found"}, status=404)
        serializer = self.get_serializer(latest)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user_id = get_user_id(self.request)
        access_token = get_access_token(self.request)

        if access_token is None or user_id is None:
            return Response(
                {"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        qs = Transaction.objects.filter(user_id=user_id).order_by("-booking_date")

        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        category_id = self.request.query_params.get("category_id")

        if date_from:
            qs = qs.filter(booking_date__gte=date_from)
        if date_to:
            qs = qs.filter(booking_date__lte=date_to)
        if category_id:
            qs = qs.filter(category_id=category_id)

        return qs

    @extend_schema(
        summary="Delete a transaction.",
        description="Deletes a transaction by ID.",
        responses={204: None, 404: {"detail": "Not found"}},
    )
    def destroy(self, request, pk=None):
        try:
            instance = self.get_queryset().get(pk=pk)
        except Transaction.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="get")
    def get_transaction(self, request, pk=None):
        try:
            instance = self.get_queryset().get(pk=pk)
        except Transaction.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="reapply-rules")
    def reapply_rules(self, request):
        """
        Reapply rules to all uncategorized transactions for the current user.
        Tries several simple matching strategies (regex/pattern, exact counterparty,
        substring match against name/description). Updates transactions in-place.
        """
        user_id = get_user_id(request)
        access_token = get_access_token(request)

        if access_token is None or user_id is None:
            return Response(
                {"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        task = apply_rules_task.delay(user_id)

        return Response(
            {
                "task_id": task.id,
                "status": "Task started",
                "message": "Rules are being applied in the background",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["patch"], url_path="set-category")
    def set_category(self, request, pk=None):
        try:
            instance = self.get_queryset().get(pk=pk)
        except Transaction.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        cat_id = request.data.get("category_id") or request.data.get("category")

        if cat_id in (None, "", "null"):
            instance.category = None
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)

        print(
            "Setting category to",
            cat_id,
            "for transaction",
            str(instance.id),
            "for user",
            instance.user_id,
        )

        try:
            category = Category.objects.get(
                Q(user_id=instance.user_id) | Q(user_id="default"), pk=cat_id
            )
        except Category.DoesNotExist:
            return Response(
                {"detail": "Category not found"}, status=status.HTTP_404_NOT_FOUND
            )

        instance.category = category
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.all().order_by("-id")
    serializer_class = RuleSerializer

    def get_queryset(self):
        user_id = get_user_id(self.request)
        access_token = get_access_token(self.request)

        if access_token is None or user_id is None:
            return Response(
                {"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        return Rule.objects.filter(Q(user_id=user_id) | Q(user_id="default")).order_by(
            "-id"
        )

    def perform_create(self, serializer):
        user_id = get_user_id(self.request)
        serializer.save(user_id=user_id)

    def perform_update(self, serializer):
        user_id = get_user_id(self.request)
        serializer.save(user_id=user_id)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("-id")
    serializer_class = CategorySerializer

    def get_queryset(self):
        user_id = get_user_id(self.request)
        access_token = get_access_token(self.request)

        if access_token is None or user_id is None:
            return Response(
                {"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        return Category.objects.filter(
            Q(user_id=user_id) | Q(user_id="default")
        ).order_by("-id")

    def perform_create(self, serializer):
        user_id = get_user_id(self.request)
        serializer.save(user_id=user_id)

    def perform_update(self, serializer):
        user_id = get_user_id(self.request)
        serializer.save(user_id=user_id)


from decimal import Decimal
from django.db.models import Sum, F, Value, Case, When, DecimalField, Count
from django.db.models.functions import ExtractMonth, ExtractYear
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ingestion.models import Transaction
import re


@api_view(["GET"])
def cashflow_view(request):
    """Monthly income and expense totals."""
    user_id = get_user_id(request)
    access_token = get_access_token(request)

    if access_token is None or user_id is None:
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    qs = (
        Transaction.objects.filter(user_id=user_id, is_transfer=False)
        .exclude(booking_date=None)
        .annotate(year=ExtractYear("booking_date"), month=ExtractMonth("booking_date"))
        .values("year", "month")
        .annotate(
            income=Sum(
                Case(
                    When(amount__gt=0, then=F("amount")),
                    default=Value(0),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            ),
            expense=Sum(
                Case(
                    When(amount__lt=0, then=F("amount")),
                    default=Value(0),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            ),
        )
        .order_by("year", "month")
    )

    data = [
        {
            "year": int(r["year"]),
            "month": int(r["month"]),
            "income": float(r["income"] or 0),
            "expense": abs(float(r["expense"] or 0)),
        }
        for r in qs
    ]
    return Response(data)


@api_view(["GET"])
def categories_view(request):
    """Breakdown of expenses by category."""
    user_id = get_user_id(request)
    access_token = get_access_token(request)

    if access_token is None or user_id is None:
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    qs = (
        Transaction.objects.filter(user_id=user_id, is_transfer=False, amount__lt=0)
        .values("category__name", "category__type")
        .annotate(
            total=Sum(
                F("amount") * Value(-1),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        .order_by("-total")
    )

    data = [
        {
            "category": r["category__name"] or "Egyéb",
            "type": r["category__type"],
            "value": float(r["total"] or 0),
        }
        for r in qs
    ]
    return Response(data)


@api_view(["GET"])
def top_merchants_view(request):
    """Top counterparties by spending."""
    user_id = get_user_id(request)
    access_token = get_access_token(request)

    if access_token is None or user_id is None:
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    limit = int(request.query_params.get("limit", 5))

    qs = (
        Transaction.objects.filter(user_id=user_id, is_transfer=False, amount__lt=0)
        .values("counterparty")
        .annotate(
            total=Sum(
                F("amount") * Value(-1),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        .order_by("-total")[:limit]
    )

    data = [
        {
            "name": r["counterparty"] or "(no counterparty)",
            "amount": float(r["total"] or 0),
        }
        for r in qs
    ]
    return Response(data)


@api_view(["GET"])
def balance_summary(request):
    user_id = get_user_id(request)
    access_token = get_access_token(request)

    if access_token is None or user_id is None:
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    aggregates = (
        Transaction.objects.filter(user_id=user_id)
        .select_related("category")
        .aggregate(
            income=Sum(
                Case(
                    When(category__type="income", then=F("amount")),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            ),
            expense=Sum(
                Case(
                    When(category__type="expense", then=F("amount")),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            ),
        )
    )

    income = aggregates.get("income") or Decimal("0")
    expense = aggregates.get("expense") or Decimal("0")
    net_savings = income - expense

    # Nettó egyenleg (kumulativ megtakaritas)
    total_balance = net_savings

    return Response(
        {
            "income": income,
            "expense": expense,
            "net_savings": net_savings,
            "total_balance": total_balance,
        }
    )


from datetime import date
from dateutil.relativedelta import relativedelta
from django.db.models.functions import TruncMonth


@api_view(["GET"])
def monthly_balance(request):
    user_id = get_user_id(request)
    access_token = get_access_token(request)

    if access_token is None or user_id is None:
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    months = int(request.GET.get("months", 6))
    today = date.today()
    start_date = today - relativedelta(months=months - 1)
    start_date = start_date.replace(day=1)

    # csoportosítás hónap szerint
    qs = (
        Transaction.objects.filter(user_id=user_id, booking_date__gte=start_date)
        .select_related("category")
        .annotate(month=TruncMonth("booking_date"))
        .values("month")
        .annotate(
            income=Sum(
                Case(
                    When(category__type="income", then=F("amount")),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            ),
            expense=Sum(
                Case(
                    When(category__type="expense", then=F("amount")),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            ),
        )
        .order_by("month")
    )

    # JSON formázás
    result = []
    for row in qs:
        income = row.get("income") or Decimal("0")
        expense = row.get("expense") or Decimal("0")
        result.append(
            {
                "month": row["month"].strftime("%Y-%m"),
                "income": income,
                "expense": expense,
                "net": income - expense,
            }
        )

    return Response(result)


@api_view(["GET"])
def category_expenses(request):
    user_id = get_user_id(request)
    access_token = get_access_token(request)

    if access_token is None or user_id is None:
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    period = request.GET.get("period")
    today = date.today()

    start_date = None
    end_date = None

    if period:
        try:
            year, month = map(int, period.split("-"))
            start_date = date(year, month, 1)
        except Exception:
            return Response(
                {"detail": "Invalid period format (use YYYY-MM)"}, status=400
            )

        # hónap utolsó napja (következő hónap első napja mint felső zárt határ)
        if start_date.month == 12:
            end_date = date(start_date.year + 1, 1, 1)
        else:
            end_date = date(start_date.year, start_date.month + 1, 1)

    # tranzakciók összesítése kategóriánként
    qs = Transaction.objects.filter(
        user_id=user_id,
        category__type="expense",
    )
    # ha period meg van adva, akkor időszakra szűrünk, különben nincs dátum limit
    if start_date and end_date:
        qs = qs.filter(booking_date__gte=start_date, booking_date__lt=end_date)

    qs = (
        qs.select_related("category")
        .values(name=F("category__name"))
        .annotate(amount=Sum("amount"))
        .order_by("amount")
    )

    # top 5
    data = [
        {
            "category": row["name"],
            "amount": row["amount"],
        }
        for row in list(qs)[:5]
        if row["amount"]
    ]

    return Response(data)

from django.db.models.functions import ExtractWeekDay
from django.db.models import Q


@api_view(["GET"])
def spending_patterns(request):
    user_id = get_user_id(request)
    access_token = get_access_token(request)

    if access_token is None or user_id is None:
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    # Hét napjának sorrendje (Django: 1=Vasárnap, 7=Szombat)
    day_map = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}

    qs = (
        Transaction.objects.filter(user_id=user_id, category__type="expense")
        .exclude(booking_date__isnull=True)
        .annotate(weekday=ExtractWeekDay("booking_date"))
        .values("weekday")
        .annotate(amount=Sum("amount"))
        .order_by("weekday")
    )

    result = []
    for row in qs:
        weekday = int(row["weekday"])
        result.append(
            {
                "day": day_map.get(weekday, str(weekday)),
                "amount": row["amount"] or 0,
            }
        )

    return Response({"by_weekday": result})


@api_view(["GET"])
def category_coverage(request):
    user_id = get_user_id(request)
    access_token = get_access_token(request)

    if access_token is None or user_id is None:
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    total_transactions = Transaction.objects.filter(user_id=user_id).count()
    categorized_transactions = Transaction.objects.filter(
        user_id=user_id, category__isnull=False
    ).count()

    coverage_percentage = (
        (categorized_transactions / total_transactions) * 100
        if total_transactions > 0
        else 0
    )

    return Response(
        {
            "total_transactions": total_transactions,
            "categorized_transactions": categorized_transactions,
            "coverage_percentage": round(coverage_percentage, 2),
        }
    )


@api_view(["GET"])
def avg_expense_per_category(request):
    user_id = get_user_id(request)
    access_token = get_access_token(request)

    if access_token is None or user_id is None:
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    qs = (
        Transaction.objects.filter(user_id=user_id, category__type="expense")
        .values("category__name")
        .annotate(avg_amount=Sum("amount") / Count("id"))
        .order_by("category__name")
    )

    data = [
        {
            "category": r["category__name"] or "Egyéb",
            "average_expense": float(r["avg_amount"] or 0),
        }
        for r in qs
    ]
    return Response(data)
