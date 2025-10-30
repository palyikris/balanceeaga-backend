# backend/reports/views.py
import os
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from ingestion.models import Transaction, Report
from ingestion.utils import get_access_token, get_user_id
from weasyprint import HTML
from django.template.loader import render_to_string
from django.template import Template, Context


@api_view(["GET"])
def monthly_report(request):
    """
    Generate a PDF report for a given year and month.
    The PDF is saved to MEDIA_ROOT/reports/<user_id>/report_YYYY_MM.pdf
    and a Report entry is stored in the database.
    """
    user_id = get_user_id(request)
    access_token = get_access_token(request)

    if not user_id or not access_token:
        return Response({"detail": "Authentication credentials were not provided."}, status=401)

    try:
        year = int(request.query_params.get("year"))
        month = int(request.query_params.get("month"))
    except (TypeError, ValueError):
        return Response(
            {"detail": "Invalid or missing 'year'/'month' parameters."}, status=400
        )

    txns = Transaction.objects.filter(
        user_id=user_id,
        booking_date__year=year,
        booking_date__month=month,
    ).select_related("category")

    if not txns.exists():
        return Response({"detail": "No transactions found for this month."}, status=404)

    # --- Aggregates ---
    total_income = txns.filter(amount__gt=0).aggregate(Sum("amount"))[
        "amount__sum"
    ] or Decimal(0)
    total_expense = txns.filter(amount__lt=0).aggregate(Sum("amount"))[
        "amount__sum"
    ] or Decimal(0)
    net_balance = total_income + total_expense  # expense is negative

    # --- Category summary ---
    category_totals = (
        txns.filter(category__isnull=False)
        .values("category__name", "category__type")
        .annotate(total=Sum("amount"))
        .order_by("total")
    )

    context = {
        "year": year,
        "month": month,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": net_balance,
        "categories": category_totals,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    template_path = os.path.join(os.path.dirname(__file__), "monthly_report.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_string = f.read()
    except FileNotFoundError:
        return Response({"detail": "Template not found."}, status=500)

    html_string = Template(template_string).render(Context(context))
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    # save file
    reports_dir = os.path.join(settings.MEDIA_ROOT, "reports", str(user_id))
    os.makedirs(reports_dir, exist_ok=True)
    filename = f"report_{year}_{month:02d}.pdf"
    file_path = os.path.join(reports_dir, filename)
    with open(file_path, "wb") as f:
        if isinstance(pdf, bytes):
            f.write(pdf)

    relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
    report_obj, _ = Report.objects.update_or_create(
        user_id=user_id,
        year=year,
        month=month,
        defaults={
            "storage_path": relative_path,
            "original_name": filename,
            "size_bytes": len(pdf ) if isinstance(pdf, bytes) else 0,
        },
    )

    return Response(
        {
            "detail": "Report generated successfully.",
            "file_url": f"http://127.0.0.1:8000{settings.MEDIA_URL}{report_obj.storage_path}",
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def report_history(request):
    """
    List all generated reports for the authenticated user.
    """
    user_id = get_user_id(request)
    access_token = get_access_token(request)
    
    if not user_id or not access_token:
        return Response({"detail": "Authentication credentials were not provided."}, status=401)
    
    reports = Report.objects.filter(user_id=user_id).order_by("-created_at")

    data = [
        {
            "id": str(r.id),
            "year": r.year,
            "month": r.month,
            "file_url": f"http://127.0.0.1:8000{settings.MEDIA_URL}{r.storage_path}",
            "created_at": r.created_at.isoformat(),
            "size_kb": round(r.size_bytes / 1024, 1),
            "month_label": datetime(r.year, r.month, 1).strftime("%B %Y"),
        }
        for r in reports
    ]

    return Response(data, status=status.HTTP_200_OK)
