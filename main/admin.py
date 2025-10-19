from django.contrib import admin
from .models import ToolCategory, Tool, Customer, Rental, RentalItem

@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

# admin.py
@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'daily_price', 'quantity_total', 'quantity_available', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name']
    list_editable = ['daily_price', 'quantity_total', 'is_active']
    
    def save_model(self, request, obj, form, change):
        # Admin panelda saqlaganda available ni yangilash
        if change:  # Mavjud obyekt
            old_obj = Tool.objects.get(pk=obj.pk)
            if old_obj.quantity_total != obj.quantity_total:
                # Jami son o'zgarsa, mavjud sonni moslashtirish
                difference = obj.quantity_total - old_obj.quantity_total
                obj.quantity_available += difference
        else:  # Yangi obyekt
            obj.quantity_available = obj.quantity_total
        
        super().save_model(request, obj, form, change)

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