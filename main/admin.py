from django.contrib import admin
from .models import ToolCategory, Tool, Customer, Rental, RentalItem

@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'daily_price', 'quantity_available', 'quantity_total', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name']
    list_editable = ['daily_price', 'quantity_total', 'is_active']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'created_at']
    search_fields = ['name', 'phone']

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ['customer', 'start_date', 'end_date', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'start_date']
    search_fields = ['customer__name', 'customer__phone']
    readonly_fields = ['created_at']

@admin.register(RentalItem)
class RentalItemAdmin(admin.ModelAdmin):
    list_display = ['rental', 'tool', 'quantity', 'daily_rate']
    list_filter = ['tool__category']