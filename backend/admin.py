from django.contrib import admin

from backend.models import Trade, Sale, Purchase, ApplicationVersion


# admin.site.register(Sale)
@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'trade_value', 'sender', 'recipient')
    ordering = ('id',)


# admin.site.register(Sale)
@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale_price',  'amount', 'sale_status')
    ordering = ('id',)


# admin.site.register(Purchase)
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'purchase_price', 'amount', 'purchase_status')
    ordering = ('id',)


# admin.site.register(Purchase)
@admin.register(ApplicationVersion)
class ApplicationVersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'version')
    ordering = ('id',)


# admin.site.register(Transaction)
# @admin.register(Transaction)
# class TransactionAdmin(admin.ModelAdmin):
#     list_display = ('id', 'trade_price', 'transaction_amount', 'transaction_status')
#     ordering = ('id',)



