from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'sno', 'ano', 'amount', 'date', 'phone')
    search_fields = ('customer_name', 'sno', 'ano', 'phone')
    list_filter = ('date', 'metal_type')
