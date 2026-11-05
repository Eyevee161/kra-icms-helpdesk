from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Priority, Ticket, TicketAttachment, TicketComment, TicketHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "description")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "color")
    ordering = ("level",)


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0
    readonly_fields = ("uploaded_at", "filename")


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 1
    fields = ("author", "author_name", "is_internal", "body", "created_at")
    readonly_fields = ("created_at",)


class TicketHistoryInline(admin.TabularInline):
    model = TicketHistory
    extra = 0
    readonly_fields = ("changed_by", "field", "old_value", "new_value", "timestamp")
    can_delete = False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_number",
        "subject",
        "category",
        "priority_badge",
        "status_badge",
        "taxpayer_name",
        "assigned_to",
        "created_at",
    )
    list_filter = ("status", "priority", "category", "assigned_to", "created_at")
    search_fields = ("ticket_number", "subject", "taxpayer_name", "taxpayer_email", "kra_pin", "id_number")
    readonly_fields = ("ticket_number", "created_at", "updated_at", "resolved_at")
    list_editable = ("assigned_to",)
    date_hierarchy = "created_at"
    inlines = [TicketAttachmentInline, TicketCommentInline, TicketHistoryInline]
    actions = ["mark_in_progress", "mark_resolved", "mark_closed"]

    fieldsets = (
        ("Ticket Info", {
            "fields": ("ticket_number", "subject", "description", "category", "priority", "status")
        }),
        ("Taxpayer Details", {
            "fields": ("taxpayer_name", "taxpayer_email", "taxpayer_phone", "kra_pin", "id_number")
        }),
        ("Assignment & Tracking", {
            "fields": ("assigned_to", "created_by", "created_at", "updated_at", "resolved_at")
        }),
    )

    def priority_badge(self, obj):
        colors = {
            "Low": "secondary",
            "Medium": "info",
            "High": "warning",
            "Critical": "danger",
        }
        color = colors.get(obj.priority.name, "secondary")
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:4px;">{}</span>',
            {"secondary": "#6c757d", "info": "#0dcaf0", "warning": "#ffc107", "danger": "#dc3545"}.get(color, "#6c757d"),
            obj.priority.name,
        )
    priority_badge.short_description = "Priority"

    def status_badge(self, obj):
        colors = {
            "open": "#0d6efd",
            "in_progress": "#fd7e14",
            "pending": "#6f42c1",
            "resolved": "#198754",
            "closed": "#6c757d",
        }
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:4px;">{}</span>',
            colors.get(obj.status, "#6c757d"),
            obj.get_status_display(),
        )
    status_badge.short_description = "Status"

    @admin.action(description="Mark selected as In Progress")
    def mark_in_progress(self, request, queryset):
        queryset.update(status="in_progress")

    @admin.action(description="Mark selected as Resolved")
    def mark_resolved(self, request, queryset):
        for t in queryset:
            t.status = "resolved"
            t.save()

    @admin.action(description="Mark selected as Closed")
    def mark_closed(self, request, queryset):
        queryset.update(status="closed")


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "author_name", "is_internal", "created_at")
    list_filter = ("is_internal", "created_at")


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "filename", "uploaded_at")
