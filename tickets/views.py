from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Ticket, Category, Priority, TicketAttachment, TicketComment, TicketHistory
from .forms import TicketSubmitForm, TicketTrackForm, CommentForm, AssignTicketForm


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


def home(request):
    return render(request, "tickets/home.html")


def submit_ticket(request):
    if request.method == "POST":
        form = TicketSubmitForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.created_by = request.user
            ticket.save()

            # Handle attachment
            attachment_file = request.FILES.get("attachment")
            if attachment_file:
                TicketAttachment.objects.create(
                    ticket=ticket,
                    file=attachment_file,
                    filename=attachment_file.name,
                    uploaded_by=request.user if request.user.is_authenticated else None,
                )

            # Send confirmation email (console backend in MVP)
            try:
                send_mail(
                    subject=f"KRA ICMS Help Desk - Ticket Received [{ticket.ticket_number}]",
                    message=(
                        f"Dear {ticket.taxpayer_name},\n\n"
                        f"Your complaint has been received.\n\n"
                        f"Ticket Number: {ticket.ticket_number}\n"
                        f"Subject: {ticket.subject}\n"
                        f"Category: {ticket.category.name}\n"
                        f"Priority: {ticket.priority.name}\n\n"
                        f"You can track the status of your ticket at any time using the ticket number and your email.\n\n"
                        f"Thank you for contacting KRA ICMS Help Desk.\n"
                        f"Kenya Revenue Authority"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[ticket.taxpayer_email],
                    fail_silently=True,
                )
            except Exception:
                pass  # MVP: ignore email failures

            messages.success(
                request,
                f"Ticket submitted successfully! Your ticket number is <strong>{ticket.ticket_number}</strong>. "
                f"Please save it for tracking.",
            )
            return redirect("ticket_detail_public", ticket_number=ticket.ticket_number)
    else:
        form = TicketSubmitForm()
    return render(request, "tickets/submit.html", {"form": form})


def track_ticket(request):
    ticket = None
    form = TicketTrackForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ticket_number = form.cleaned_data["ticket_number"].strip().upper()
        email = form.cleaned_data["email"].strip().lower()
        try:
            ticket = Ticket.objects.get(ticket_number__iexact=ticket_number, taxpayer_email__iexact=email)
        except Ticket.DoesNotExist:
            messages.error(request, "No ticket found with that number and email combination.")
    return render(request, "tickets/track.html", {"form": form, "ticket": ticket})


def ticket_detail_public(request, ticket_number):
    ticket = get_object_or_404(Ticket, ticket_number=ticket_number)
    public_comments = ticket.comments.filter(is_internal=False)
    return render(
        request,
        "tickets/ticket_detail_public.html",
        {"ticket": ticket, "comments": public_comments},
    )


@login_required
@user_passes_test(is_staff_user)
def dashboard(request):
    # Stats
    total = Ticket.objects.count()
    open_count = Ticket.objects.filter(status="open").count()
    in_progress = Ticket.objects.filter(status="in_progress").count()
    resolved = Ticket.objects.filter(status="resolved").count()
    closed = Ticket.objects.filter(status="closed").count()

    # Recent tickets
    recent = Ticket.objects.select_related("category", "priority", "assigned_to")[:15]

    # By category
    by_category = (
        Ticket.objects.values("category__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # By priority
    by_priority = (
        Ticket.objects.values("priority__name")
        .annotate(count=Count("id"))
        .order_by("priority__level")
    )

    # Unassigned
    unassigned = Ticket.objects.filter(assigned_to__isnull=True, status__in=["open", "in_progress"]).count()

    # Last 7 days trend
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_trend = Ticket.objects.filter(created_at__gte=seven_days_ago).count()

    context = {
        "total": total,
        "open_count": open_count,
        "in_progress": in_progress,
        "resolved": resolved,
        "closed": closed,
        "unassigned": unassigned,
        "recent_trend": recent_trend,
        "recent_tickets": recent,
        "by_category": by_category,
        "by_priority": by_priority,
    }
    return render(request, "tickets/dashboard.html", context)


@login_required
@user_passes_test(is_staff_user)
def ticket_list(request):
    qs = Ticket.objects.select_related("category", "priority", "assigned_to")
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    assigned = request.GET.get("assigned")
    if assigned == "me":
        qs = qs.filter(assigned_to=request.user)
    elif assigned == "unassigned":
        qs = qs.filter(assigned_to__isnull=True)
    search = request.GET.get("q")
    if search:
        qs = qs.filter(
            Q(ticket_number__icontains=search)
            | Q(subject__icontains=search)
            | Q(taxpayer_name__icontains=search)
            | Q(kra_pin__icontains=search)
        )
    return render(request, "tickets/ticket_list.html", {"tickets": qs[:100], "status": status})


@login_required
@user_passes_test(is_staff_user)
def ticket_detail(request, pk):
    ticket = get_object_or_404(
        Ticket.objects.select_related("category", "priority", "assigned_to"),
        pk=pk,
    )
    comments = ticket.comments.select_related("author")
    history = ticket.history.select_related("changed_by")[:20]
    assign_form = AssignTicketForm(instance=ticket)
    comment_form = CommentForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "assign":
            assign_form = AssignTicketForm(request.POST, instance=ticket)
            if assign_form.is_valid():
                old_status = ticket.status
                old_assignee = ticket.assigned_to
                ticket = assign_form.save()
                # Log history
                if old_status != ticket.status:
                    TicketHistory.objects.create(
                        ticket=ticket,
                        changed_by=request.user,
                        field="status",
                        old_value=old_status,
                        new_value=ticket.status,
                    )
                if old_assignee != ticket.assigned_to:
                    TicketHistory.objects.create(
                        ticket=ticket,
                        changed_by=request.user,
                        field="assigned_to",
                        old_value=str(old_assignee) if old_assignee else "Unassigned",
                        new_value=str(ticket.assigned_to) if ticket.assigned_to else "Unassigned",
                    )
                messages.success(request, "Ticket updated.")
                return redirect("ticket_detail", pk=pk)
        elif action == "comment":
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.ticket = ticket
                comment.author = request.user
                comment.save()
                messages.success(request, "Comment added.")
                return redirect("ticket_detail", pk=pk)

    return render(
        request,
        "tickets/ticket_detail.html",
        {
            "ticket": ticket,
            "comments": comments,
            "history": history,
            "assign_form": assign_form,
            "comment_form": comment_form,
        },
    )


@login_required
@user_passes_test(is_staff_user)
def reports(request):
    # Simple analytics
    by_status = Ticket.objects.values("status").annotate(count=Count("id"))
    by_category = (
        Ticket.objects.values("category__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    by_priority = Ticket.objects.values("priority__name").annotate(count=Count("id"))
    by_assignee = (
        Ticket.objects.filter(assigned_to__isnull=False)
        .values("assigned_to__username")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Resolution time (simple avg for resolved)
    resolved_tickets = Ticket.objects.filter(resolved_at__isnull=False)
    avg_hours = None
    if resolved_tickets.exists():
        total_seconds = sum(
            (t.resolved_at - t.created_at).total_seconds() for t in resolved_tickets
        )
        avg_hours = round(total_seconds / resolved_tickets.count() / 3600, 1)

    return render(
        request,
        "tickets/reports.html",
        {
            "by_status": by_status,
            "by_category": by_category,
            "by_priority": by_priority,
            "by_assignee": by_assignee,
            "avg_hours": avg_hours,
            "total": Ticket.objects.count(),
        },
    )
