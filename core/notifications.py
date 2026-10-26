"""Creates the dashboard notifications (the bell) when something new arrives."""
from django.urls import reverse

from .models import Notification


def booking_notification(booking):
    if booking.is_question:
        kind, title = "question", f"{booking.name} asked about a busy date"
    else:
        kind, title = "booking", f"New booking {booking.reference} from {booking.name}"
    body = f"{booking.get_event_type_display()}, {booking.event_date:%d %b %Y}, {booking.guests or '?'} guests"
    Notification.objects.create(kind=kind, title=title, body=body,
                                url=reverse("dash_booking", args=[booking.pk]))


def message_notification(message):
    Notification.objects.create(kind="message", title=f"New message from {message.name}",
                                body=message.message[:120], url=reverse("dash_message", args=[message.pk]))
