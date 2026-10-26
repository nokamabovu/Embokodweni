"""
Availability rules for bookings.

A date is available when:
  1. it is today or later,
  2. the owner has not blocked it in the admin (Blocked dates),
  3. it has fewer confirmed bookings than "max bookings per day" (Site contact info),
  4. the group is not bigger than "max guests" (if the owner set one).
"""
from datetime import timedelta
from urllib.parse import quote_plus

from django.utils import timezone

from .models import BlockedDate, Enquiry, SiteInfo


def check_date(day, guests=None):
    """Return {"available": bool, "reason": str} for one day."""
    site = SiteInfo.load()
    today = timezone.localdate()

    if day < today:
        return {"available": False, "reason": "past"}
    if site.max_guests and guests and guests > site.max_guests:
        return {"available": False, "reason": "too_many"}
    if BlockedDate.objects.filter(date=day).exists():
        return {"available": False, "reason": "blocked"}
    confirmed = Enquiry.objects.filter(event_date=day, status="confirmed").count()
    if confirmed >= site.max_bookings_per_day:
        return {"available": False, "reason": "full"}
    return {"available": True, "reason": ""}


def next_free_dates(start, guests=None, how_many=3, look_ahead=60):
    """The next few available days after `start`."""
    found = []
    day = max(start, timezone.localdate())
    for _ in range(look_ahead):
        day = day + timedelta(days=1)
        if check_date(day, guests)["available"]:
            found.append(day)
            if len(found) == how_many:
                break
    return found


MESSAGES = {
    "past": "That date has already passed. Please choose a date from today onwards.",
    "too_many": "That group is bigger than we can host at once. Call us and we'll see what we can arrange.",
    "blocked": "Sorry, that date is already booked.",
    "full": "Sorry, that date is already booked.",
}


def ask_details(day, guests=None, event_label=""):
    """Call and WhatsApp links for asking about a busy date."""
    site = SiteInfo.load()
    phones = site.phones()
    details = {"phone": "", "dial": "", "whatsapp_url": ""}
    if phones:
        details["phone"], details["dial"] = phones[0]
    if site.whatsapp:
        text = (f"Hi Embokodweni Lifestyle, I'd like to book {event_label or 'an event'} on "
                f"{day.strftime('%d %B %Y')}" + (f" for {guests} guests" if guests else "") +
                ". The website says the date is booked. Is there space in another area?")
        details["whatsapp_url"] = f"https://wa.me/{site.whatsapp}?text={quote_plus(text)}"
    return details


def availability_result(day, guests=None):
    """Everything the website needs to show for one check."""
    result = check_date(day, guests)
    data = {
        "available": result["available"],
        "date": day.isoformat(),
        "date_label": day.strftime("%A %d %B %Y").replace(" 0", " "),
    }
    # A "booked" day may only be booked for part of the venue, so people
    # can still ask the team whether there's space.
    data["can_ask"] = result["reason"] in ("full", "blocked", "too_many")
    if result["available"]:
        data["message"] = f"Good news! {data['date_label']} is available."
        data["alternatives"] = []
    else:
        data["message"] = MESSAGES[result["reason"]]
        data["alternatives"] = [
            {"date": d.isoformat(), "label": d.strftime("%a %d %b").replace(" 0", " ")}
            for d in next_free_dates(day, guests)
        ] if result["reason"] != "too_many" else []
    return data
