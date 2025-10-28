"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ingestion.views import (
    ImportViewSet,
    TransactionViewSet,
    RuleViewSet,
    CategoryViewSet,
    cashflow_view,
    categories_view,
    top_merchants_view,
    balance_summary,
    monthly_balance,
    category_expenses,
    spending_patterns,
    category_coverage,
    avg_expense_per_category,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


router = DefaultRouter(trailing_slash=False)
router.register(r"imports", ImportViewSet, basename="imports")
router.register(r"transactions", TransactionViewSet, basename="transactions")
router.register(r"rules", RuleViewSet, basename="rules")
router.register(r"categories", CategoryViewSet, basename="categories")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    # Analytics endpoints (function-based views)
    path("api/dashboard/cashflow", cashflow_view, name="cashflow"),
    path(
        "api/dashboard/categories-summary", categories_view, name="categories-summary"
    ),
    path("api/dashboard/top-merchants", top_merchants_view, name="top-merchants"),
    path("api/dashboard/balance-summary", balance_summary, name="balance-summary"),
    path("api/dashboard/monthly-balance", monthly_balance, name="monthly-balance"),
    path(
        "api/dashboard/category-expenses", category_expenses, name="category-expenses"
    ),
    path(
        "api/dashboard/spending-patterns", spending_patterns, name="spending-patterns"
    ),
    path(
        "api/dashboard/category-coverage", category_coverage, name="category-coverage"
    ),
    path(
        "api/dashboard/avg-expense-per-category",
        avg_expense_per_category,
        name="avg-expense-per-category",
    ),
    # OpenAPI schema (JSON/YAML)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Redoc (opcionális)
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
