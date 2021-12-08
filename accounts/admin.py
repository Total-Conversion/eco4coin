from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('id', 'date_joined', 'cash_balance', 'cash_locked', 'coin_balance', 'coin_locked', 'wallet_id', 'device')
    list_filter = ()
    fieldsets = (
        (None,
         {'fields': (
            'date_joined', 'cash_balance', 'cash_locked', 'coin_balance', 'coin_locked', 'wallet_id', 'device'
         )}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('id', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
         ),
    )
    search_fields = ('wallet_id',)
    ordering = ('id',)


admin.site.register(CustomUser, CustomUserAdmin)
