from django.contrib import admin
from .models import StockHistory


@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    list_display = ("symbol", "date", "close", "volume")
    list_filter = ("symbol",)
