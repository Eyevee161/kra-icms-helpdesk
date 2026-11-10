from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Priority(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Low, Medium, High, Critical
    level = models.PositiveSmallIntegerField(default=1)  # 1=Low ... 4=Critical
    color = models.CharField(max_length=20, default="secondary")  # Bootstrap color

    class Meta:
        verbose_name_plural = "Priorities"
        ordering = ["level"]

    def __str__(self):
        return self.name


class Ticket(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("pending", "Pending Customer"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="tickets")
    priority = models.ForeignKey(Priority, on_delete=models.PROTECT, related_name="tickets")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    # Taxpayer info (for public submissions without full auth)
    taxpayer_name = models.CharField(max_length=150)
    taxpayer_email = models.EmailField()
    taxpayer_phone = models.CharField(max_length=20, blank=True)
    kra_pin = models.CharField(max_length=20, blank=True, help_text="KRA PIN if available")
    id_number = models.CharField(max_length=20, blank=True, help_text="National ID / Passport")

    # Assignment
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tickets"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_tickets"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Mapping of category name to short code
            category_codes = {
                "Customs Declaration Issues": "CD",
                "Payment & Receipts": "PAY",
                "System Access / Login": "ACC",
                "Cargo Release / Clearance": "CR",
                "Tariff / Classification": "TAR",
                "Bond & Guarantees": "BG",
                "Warehousing": "WH",
                "Other / General Enquiry": "GEN",
            }

            code = "GEN"
            if self.category:
                code = category_codes.get(self.category.name, "GEN")

            date_part = timezone.now().strftime("%Y%m%d")
            prefix = f"KRA-{code}-{date_part}"

            last_ticket = Ticket.objects.filter(
                ticket_number__startswith=prefix
            ).order_by("-id").first()

            if last_ticket:
                try:
                    seq = int(last_ticket.ticket_number.split("-")[-1]) + 1
                except (IndexError, ValueError):
                    seq = 1
            else:
                seq = 1

            self.ticket_number = f"{prefix}-{seq:04d}"

        if self.status == "resolved" and not self.resolved_at:
            self.resolved_at = timezone.now()

        super().save(*args, **kwargs)

class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="ticket_attachments/%Y/%m/")
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.filename


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_name = models.CharField(max_length=150, blank=True)  # for public replies
    is_internal = models.BooleanField(default=False, help_text="Internal notes not visible to taxpayer")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment on {self.ticket.ticket_number}"


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="history")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    field = models.CharField(max_length=50)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name_plural = "Ticket histories"
