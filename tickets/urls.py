from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("submit/", views.submit_ticket, name="submit_ticket"),
    path("track/", views.track_ticket, name="track_ticket"),
    path("ticket/<str:ticket_number>/", views.ticket_detail_public, name="ticket_detail_public"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("tickets/", views.ticket_list, name="ticket_list"),
    path("tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("reports/", views.reports, name="reports"),
]
