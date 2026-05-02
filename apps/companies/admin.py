from django.contrib import admin
from .models import Company, CompanyMember

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'industry', 'company_size', 'subscription_tier', 'is_verified', 'created_at']
    list_filter = ['industry', 'company_size', 'subscription_tier', 'is_verified', 'created_at']
    search_fields = ['name', 'description', 'owner__email']
    ordering = ['-created_at']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('owner', 'name', 'slug')
        }),
        ('Company Info', {
            'fields': ('description', 'logo', 'website', 'industry', 'company_size')
        }),
        ('Settings', {
            'fields': ('subscription_tier', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CompanyMember)
class CompanyMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__email', 'company__name']
    ordering = ['-joined_at']
    readonly_fields = ['joined_at']
