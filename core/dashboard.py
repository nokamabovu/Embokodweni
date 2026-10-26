"""
Staff dashboard: overview, inbox of bookings and messages, notifications
and blocked dates. Only staff accounts can open these pages.
"""
from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache
from django.http import HttpResponse
from django.templatetags.static import static
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.timesince import timesince

from .models import BlockedDate, ContactMessage, Enquiry, Notification, SiteInfo

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff, login_url="dash_login")


# --------------------------------------------------------------- login
MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",")[0].strip() or request.META.get("REMOTE_ADDR", "")


class StaffLoginView(auth_views.LoginView):
    """Login with 'keep me logged in' and a lock after too many wrong passwords."""
    template_name = "dashboard/login.html"
    redirect_authenticated_user = True

    def lock_key(self):
        return "dash-login-fails:" + client_ip(self.request)

    def post(self, request, *args, **kwargs):
        if cache.get(self.lock_key(), 0) >= MAX_FAILED_LOGINS:
            form = self.get_form()
            form.errors.clear()
            return self.render_to_response(self.get_context_data(form=form, locked=True))
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        fails = cache.get(self.lock_key(), 0) + 1
        cache.set(self.lock_key(), fails, LOCK_MINUTES * 60)
        return self.render_to_response(self.get_context_data(form=form, locked=fails >= MAX_FAILED_LOGINS,
                                                             tries_left=max(0, MAX_FAILED_LOGINS - fails)))

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_staff:
            form.add_error(None, "This account is not a staff account.")
            return self.form_invalid(form)
        cache.delete(self.lock_key())
        response = super().form_valid(form)
        if self.request.POST.get("remember"):
            self.request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days on this device
        else:
            self.request.session.set_expiry(0)  # until the browser closes
        return response


def manifest(request):
    """Lets staff add the dashboard to their phone's home screen."""
    data = {
        "name": "Embokodweni Staff",
        "short_name": "Embo Staff",
        "start_url": reverse("dash_overview"),
        "scope": reverse("dash_overview"),
        "display": "standalone",
        "background_color": "#0B1F3A",
        "theme_color": "#0B1F3A",
        "icons": [
            {"src": static("img/staff-icon-192.png"), "sizes": "192x192", "type": "image/png"},
            {"src": static("img/staff-icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    return JsonResponse(data, content_type="application/manifest+json")


def service_worker(request):
    """Served from /dashboard/ so it can control the installed staff app."""
    from django.contrib.staticfiles import finders
    path = finders.find("js/staff-sw.js")
    with open(path) as f:
        response = HttpResponse(f.read(), content_type="application/javascript")
    response["Service-Worker-Allowed"] = reverse("dash_overview")
    return response


def dash_render(request, template, context):
    """Adds the bell and sidebar counts to every dashboard page."""
    context.update({
        "unread_count": Notification.objects.filter(is_read=False).count(),
        "bell_items": Notification.objects.all()[:6],
        "inbox_unread": Enquiry.objects.filter(is_read=False).count() + ContactMessage.objects.filter(is_read=False).count(),
    })
    return render(request, template, context)


def mark_notifications_read(url):
    Notification.objects.filter(url=url, is_read=False).update(is_read=True)


# ---------------------------------------------------------------- overview
@staff_required
def overview(request):
    today = timezone.localdate()
    bookings = Enquiry.objects.all()
    pending = bookings.filter(status="pending")
    context = {
        "stats": [
            {"label": "New / unread", "value": Enquiry.objects.filter(is_read=False).count() + ContactMessage.objects.filter(is_read=False).count(),
             "hint": "bookings and messages", "url": reverse("dash_inbox") + "?f=unread"},
            {"label": "Pending bookings", "value": pending.filter(event_date__gte=today).count(),
             "hint": "waiting for a call", "url": reverse("dash_inbox") + "?f=pending"},
            {"label": "Busy-date questions", "value": sum(1 for b in pending if b.is_question),
             "hint": "check if space is free", "url": reverse("dash_inbox") + "?f=questions"},
            {"label": "Confirmed, next 30 days", "value": bookings.filter(status="confirmed", event_date__gte=today,
                                                                          event_date__lte=today + timedelta(days=30)).count(),
             "hint": "upcoming events", "url": reverse("dash_inbox") + "?f=confirmed"},
        ],
        "attention": pending.filter(event_date__gte=today).order_by("event_date")[:6],
        "upcoming": bookings.filter(event_date__gte=today, event_date__lte=today + timedelta(days=14))
                            .exclude(status="declined").order_by("event_date", "created")[:10],
        "latest_messages": ContactMessage.objects.all()[:5],
        "notifications": Notification.objects.all()[:8],
        "today": today,
        "section": "overview",
    }
    return dash_render(request, "dashboard/overview.html", context)


# ------------------------------------------------------------------- inbox
FILTERS = [
    ("all", "All"),
    ("unread", "Unread"),
    ("pending", "Pending bookings"),
    ("questions", "Busy-date questions"),
    ("confirmed", "Confirmed"),
    ("messages", "Messages"),
    ("done", "Handled"),
]


def booking_item(b):
    return {
        "kind": "question" if b.is_question else "booking",
        "kind_label": "Question" if b.is_question else "Booking",
        "title": f"{b.name} · {b.get_event_type_display()}",
        "preview": f"{b.event_date:%a %d %b %Y} · {b.guests or '?'} guests" + (f" · {b.clean_message[:80]}" if b.clean_message else ""),
        "ref": b.reference,
        "status": b.status,
        "status_label": b.get_status_display(),
        "is_read": b.is_read,
        "created": b.created,
        "url": reverse("dash_booking", args=[b.pk]),
    }


def message_item(m):
    return {
        "kind": "message",
        "kind_label": "Message",
        "title": m.name,
        "preview": m.message[:120],
        "ref": "",
        "status": "done" if m.handled else "open",
        "status_label": "Handled" if m.handled else "Open",
        "is_read": m.is_read,
        "created": m.created,
        "url": reverse("dash_message", args=[m.pk]),
    }


@staff_required
def inbox(request):
    f = request.GET.get("f", "all")
    q = request.GET.get("q", "").strip()

    bookings = Enquiry.objects.all()
    msgs = ContactMessage.objects.all()
    if q:
        bookings = bookings.filter(Q(name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q) | Q(message__icontains=q))
        msgs = msgs.filter(Q(name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q) | Q(message__icontains=q))

    if f == "unread":
        bookings, msgs = bookings.filter(is_read=False), msgs.filter(is_read=False)
    elif f == "pending":
        bookings, msgs = bookings.filter(status="pending"), msgs.none()
    elif f == "questions":
        bookings, msgs = bookings.filter(message__startswith="[Asked about a busy date"), msgs.none()
    elif f == "confirmed":
        bookings, msgs = bookings.filter(status="confirmed"), msgs.none()
    elif f == "messages":
        bookings = bookings.none()
    elif f == "done":
        bookings, msgs = bookings.filter(handled=True), msgs.filter(handled=True)

    items = [booking_item(b) for b in bookings] + [message_item(m) for m in msgs]
    items.sort(key=lambda i: i["created"], reverse=True)
    page = Paginator(items, 25).get_page(request.GET.get("page"))
    context = {"page_obj": page, "filters": FILTERS, "current": f, "q": q, "section": "inbox"}
    return dash_render(request, "dashboard/inbox.html", context)


# ------------------------------------------------------------ booking detail
def send_confirmation(booking):
    if booking.email:
        send_mail(
            f"Booking confirmed {booking.reference}",
            f"Hi {booking.name},\n\nYour booking at Embokodweni Lifestyle on {booking.event_date} is confirmed. "
            f"See you then!\n\nReference: {booking.reference}\n\nEmbokodweni Lifestyle",
            settings.DEFAULT_FROM_EMAIL, [booking.email], fail_silently=True,
        )


@staff_required
def booking_detail(request, pk):
    booking = get_object_or_404(Enquiry, pk=pk)
    url = reverse("dash_booking", args=[pk])
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "confirm":
            site = SiteInfo.load()
            others = Enquiry.objects.filter(event_date=booking.event_date, status="confirmed").exclude(pk=pk).count()
            booking.status, booking.handled = "confirmed", True
            booking.save()
            send_confirmation(booking)
            if others >= site.max_bookings_per_day:
                messages.warning(request, f"Confirmed. Note: {booking.event_date:%d %b} already had {others} confirmed booking(s).")
            else:
                messages.success(request, f"{booking.reference} confirmed. The date now shows as booked on the website.")
        elif action == "decline":
            booking.status, booking.handled = "declined", True
            booking.save()
            messages.success(request, f"{booking.reference} declined.")
        elif action == "pending":
            booking.status, booking.handled = "pending", False
            booking.save()
            messages.success(request, f"{booking.reference} moved back to pending.")
        elif action == "note":
            booking.staff_note = request.POST.get("staff_note", "")
            booking.save()
            messages.success(request, "Note saved.")
        elif action == "unread":
            booking.is_read = False
            booking.save()
            return redirect("dash_inbox")
        return redirect(url)

    if not booking.is_read:
        booking.is_read = True
        booking.save(update_fields=["is_read"])
    mark_notifications_read(url)

    site = SiteInfo.load()
    same_day = Enquiry.objects.filter(event_date=booking.event_date).exclude(pk=pk).exclude(status="declined")
    context = {
        "b": booking,
        "dial": booking.phone.replace(" ", ""),
        "wa": whatsapp_link(booking.phone, f"Hi {booking.name}, this is Embokodweni Lifestyle about your booking {booking.reference}."),
        "same_day": same_day,
        "blocked": BlockedDate.objects.filter(date=booking.event_date).first(),
        "limit": site.max_bookings_per_day,
        "section": "inbox",
    }
    return dash_render(request, "dashboard/booking.html", context)


def whatsapp_link(phone, text):
    """Turn a South African number like 072 000 0000 into a wa.me link."""
    from urllib.parse import quote_plus
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("0"):
        digits = "27" + digits[1:]
    return f"https://wa.me/{digits}?text={quote_plus(text)}" if len(digits) >= 10 else ""


# ------------------------------------------------------------ message detail
@staff_required
def message_detail(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    url = reverse("dash_message", args=[pk])
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "note":
            msg.staff_note = request.POST.get("staff_note", "")
            msg.save()
            messages.success(request, "Note saved.")
        elif action == "handled":
            msg.handled = not msg.handled
            msg.save()
            messages.success(request, "Marked as handled." if msg.handled else "Marked as open.")
        elif action == "unread":
            msg.is_read = False
            msg.save()
            return redirect("dash_inbox")
        return redirect(url)

    if not msg.is_read:
        msg.is_read = True
        msg.save(update_fields=["is_read"])
    mark_notifications_read(url)
    context = {
        "m": msg,
        "dial": msg.phone.replace(" ", ""),
        "wa": whatsapp_link(msg.phone, f"Hi {msg.name}, this is Embokodweni Lifestyle replying to your message."),
        "section": "inbox",
    }
    return dash_render(request, "dashboard/message.html", context)


# ------------------------------------------------------------- notifications
@staff_required
def notifications(request):
    if request.method == "POST":
        Notification.objects.filter(is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect(request.POST.get("next") or "dash_notifications")
    page = Paginator(Notification.objects.all(), 30).get_page(request.GET.get("page"))
    return dash_render(request, "dashboard/notifications.html", {"page_obj": page, "section": "notifications"})


@staff_required
def notification_open(request, pk):
    n = get_object_or_404(Notification, pk=pk)
    n.is_read = True
    n.save(update_fields=["is_read"])
    return redirect(n.url or "dash_overview")


@staff_required
def notifications_api(request):
    """Polled every 30 seconds by the dashboard to update the bell."""
    items = Notification.objects.all()[:6]
    latest = Notification.objects.first()
    return JsonResponse({
        "count": Notification.objects.filter(is_read=False).count(),
        "latest_id": latest.pk if latest else 0,
        "items": [{
            "id": n.pk, "kind": n.kind, "title": n.title, "body": n.body, "is_read": n.is_read,
            "ago": timesince(n.created).split(",")[0] + " ago",
            "url": reverse("dash_notification_open", args=[n.pk]),
        } for n in items],
    })


# ------------------------------------------------------------- blocked dates
@staff_required
def blocked_dates(request):
    if request.method == "POST":
        if request.POST.get("action") == "delete":
            BlockedDate.objects.filter(pk=request.POST.get("id")).delete()
            messages.success(request, "Date unblocked. It shows as available again.")
        else:
            try:
                day = date.fromisoformat(request.POST.get("date", ""))
            except ValueError:
                messages.error(request, "Choose a valid date.")
                return redirect("dash_blocked")
            BlockedDate.objects.update_or_create(date=day, defaults={"reason": request.POST.get("reason", "")})
            messages.success(request, f"{day:%a %d %b %Y} blocked. It shows as booked on the website.")
        return redirect("dash_blocked")
    today = timezone.localdate()
    context = {
        "blocked": BlockedDate.objects.filter(date__gte=today),
        "today": today,
        "section": "blocked",
    }
    return dash_render(request, "dashboard/blocked.html", context)
