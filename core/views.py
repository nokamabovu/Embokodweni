from urllib.parse import quote_plus

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from datetime import date

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils import timezone

from .availability import ask_details, availability_result
from .forms import ContactMessageForm, EnquiryForm
from .notifications import booking_notification, message_notification
from .models import Enquiry, Event, GalleryPhoto, SiteInfo, Testimonial

# Services from the company profile. "colour" picks one of the four logo stones.
SERVICES = [
    {"name": "Event Hosting", "icon": "calendar", "colour": "brown",
     "short": "Space, sound and service for gatherings of every size.",
     "long": "We host events of every size, from small get-togethers to big community days, with the space, sound and team to run them."},
    {"name": "Live DJ Entertainment", "icon": "disc", "colour": "slate",
     "short": "Resident and guest DJs, with a stage for local talent.",
     "long": "Resident and guest DJs every weekend. Promoting local talent is part of our mission, so up-and-coming DJs get a stage here too."},
    {"name": "Sports Viewing Events", "icon": "screen", "colour": "tan",
     "short": "The big matches on big screens, with the crowd to match.",
     "long": "Watch the big football and rugby matches on our big screens, with food, drinks and a crowd that brings the stadium feeling."},
    {"name": "VIP Experiences", "icon": "star", "colour": "coal",
     "short": "Reserved areas and dedicated service for your group.",
     "long": "Reserve a VIP area for your group with dedicated service, so you can relax and enjoy the night."},
    {"name": "Food & Braai Services", "icon": "braai", "colour": "slate",
     "short": "Braai and food served all day.",
     "long": "Braai and good food all day. Ask us about braai packages for groups and private events."},
    {"name": "Private Celebrations", "icon": "cake", "colour": "brown",
     "short": "Birthdays, graduations, reunions and year-end functions.",
     "long": "Birthdays, graduations, reunions, baby showers and year-end functions. Tell us what you have in mind and we will plan it with you."},
    {"name": "Community Social Events", "icon": "people", "colour": "coal",
     "short": "Social days and initiatives that give back locally.",
     "long": "Social days and initiatives that bring people together and contribute to community growth."},
    {"name": "Beverage Sales", "icon": "glass", "colour": "tan",
     "short": "A well-stocked bar with cold drinks for every taste.",
     "long": "A well-stocked bar with cold drinks for every taste, served by a friendly team."},
]

MISSION = [
    "Provide quality entertainment and leisure experiences.",
    "Promote local talent and DJs.",
    "Create a safe, enjoyable and inclusive environment.",
    "Contribute to community growth through social and entertainment initiatives.",
    "Keep improving our services based on customer feedback.",
]

# Reasons to choose Embokodweni (from the company profile)
WHY = [
    {"title": "Everything under one roof", "colour": "brown",
     "text": "DJs, big screens, braai, a full bar and VIP areas in one venue. You bring the guests, we handle the rest."},
    {"title": "A crowd that shows up", "colour": "slate",
     "text": "Embokodweni is a gathering place for the community, every weekend. Your event or brand gets seen by real people."},
    {"title": "Safe and welcoming", "colour": "tan",
     "text": "A safe, enjoyable and inclusive environment is part of our mission, so families, friends and colleagues all feel at home."},
    {"title": "We keep getting better", "colour": "coal",
     "text": "We listen to feedback and keep improving, from service at the bar to the line-up on the decks."},
]

# How booking works (a real sequence, so it is numbered on the page)
STEPS = [
    {"title": "Send an enquiry", "text": "Tell us the date, the occasion and how many guests. It takes two minutes."},
    {"title": "We plan it with you", "text": "Our team calls you to confirm availability, the area, food, drinks and music."},
    {"title": "Arrive and celebrate", "text": "Your space is ready when you arrive. Enjoy the day with your people."},
]

# Ways to work with Embokodweni (Work with us page)
PARTNER_TRACKS = [
    {"key": "sponsor", "title": "Sponsors & brands", "icon": "star", "colour": "brown",
     "text": "Put your brand in front of our weekend crowd: sponsored sports screenings, themed nights, community events and product activations."},
    {"key": "dj", "title": "DJs & local talent", "icon": "disc", "colour": "slate",
     "text": "Promoting local talent is part of our mission. Send us your mix or socials and get considered for a slot on our line-up."},
    {"key": "promoter", "title": "Event organisers", "icon": "calendar", "colour": "tan",
     "text": "Bring your event to Embokodweni. Use our venue, bar, braai and DJ entertainment and focus on filling the space."},
    {"key": "corporate", "title": "Corporate & groups", "icon": "people", "colour": "coal",
     "text": "Year-end functions, team socials, stokvels, reunions and club gatherings, with food, drinks and music sorted."},
    {"key": "supplier", "title": "Suppliers & vendors", "icon": "glass", "colour": "brown",
     "text": "Drinks distributors, caterers, decor, sound and photography. Let us know what you offer."},
]

VALUES = ["Community", "Respect", "Excellence", "Entertainment", "Innovation", "Customer Satisfaction"]


# Built-in event photos (static/img/gallery). They always show, even on a fresh
# database. Photos uploaded in the admin are shown in front of these.
BUILT_IN_PHOTOS = [
    ("embokodweni-01.jpg", "Golden hour with the Embokodweni crowd"),
    ("embokodweni-02.jpg", "Hands up at sunset"),
    ("embokodweni-03.jpg", "Good people, good vibes"),
    ("embokodweni-04.jpg", "The whole crew together"),
    ("embokodweni-05.jpg", "Weekend energy"),
    ("embokodweni-06.jpg", "Celebrating together"),
    ("embokodweni-07.jpg", "Smiles all round"),
    ("embokodweni-08.jpg", "One big family"),
    ("embokodweni-09.jpg", "Sunset celebrations"),
]


def photo_list():
    """All gallery photos as a list of {"url", "caption"}: uploads first, then built-in."""
    photos = []
    for p in GalleryPhoto.objects.all():
        if p.image and p.image.storage.exists(p.image.name):
            photos.append({"url": p.image.url, "caption": p.caption})
    for name, caption in BUILT_IN_PHOTOS:
        photos.append({"url": static("img/gallery/" + name), "caption": caption})
    return photos


def pic(number):
    """URL of one built-in photo, used for page banners and backgrounds."""
    return static("img/gallery/embokodweni-%02d.jpg" % number)


def weekly_events():
    return Event.objects.filter(is_published=True, is_weekly=True).order_by("weekday", "start_time")


def upcoming_events():
    today = timezone.localdate()
    return Event.objects.filter(is_published=True, is_weekly=False, date__gte=today).order_by("date", "start_time")


def home(request):
    context = {
        "upcoming": upcoming_events()[:3],
        "hero": static("img/hero.jpg"),
        "why": WHY,
        "testimonials": Testimonial.objects.filter(is_published=True)[:3],
        "event_types": Enquiry.EVENT_TYPE_CHOICES,
        "page": "home",
    }
    return render(request, "core/home.html", context)


def about(request):
    context = {
        "mission": MISSION,
        "values": VALUES,
        "about_photo": pic(7),
        "page": "about",
    }
    return render(request, "core/about.html", context)


def services(request):
    context = {"services": SERVICES, "page": "services"}
    return render(request, "core/services.html", context)


def events(request):
    # Build Monday to Sunday, each day with its weekly events
    weekly = weekly_events()
    today = timezone.localdate().weekday()
    week = []
    for number, name in Event.WEEKDAY_CHOICES:
        week.append({
            "name": name,
            "short": name[:3],
            "is_today": number == today,
            "events": [e for e in weekly if e.weekday == number],
        })
    context = {
        "week": week,
        "has_weekly": weekly.exists(),
        "upcoming": upcoming_events(),
        "page": "events",
    }
    return render(request, "core/events.html", context)


def gallery(request):
    context = {"photos": photo_list(), "page": "gallery"}
    return render(request, "core/gallery.html", context)


def parse_date(text):
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def parse_guests(text):
    try:
        number = int(text)
        return number if number > 0 else None
    except (TypeError, ValueError):
        return None


def check_availability(request):
    """Used by the Check availability bar: /availability/?date=2026-12-12&guests=40"""
    day = parse_date(request.GET.get("date"))
    if day is None:
        return JsonResponse({"error": "Please choose a date."}, status=400)
    guests = parse_guests(request.GET.get("guests"))
    data = availability_result(day, guests)
    if data["can_ask"]:
        label = dict(Enquiry.EVENT_TYPE_CHOICES).get(request.GET.get("type"), "")
        data["ask"] = ask_details(day, guests, label.lower())
    return JsonResponse(data)


def book(request):
    result = None
    if request.method == "POST":
        form = EnquiryForm(request.POST)
        if form.is_valid():
            day = form.cleaned_data["event_date"]
            result = availability_result(day, form.cleaned_data.get("guests"))
            asking = request.POST.get("ask") == "1" and result["can_ask"]
            if result["available"] or asking:
                booking = form.save(commit=False)
                if asking:
                    booking.message = ("[Asked about a busy date: please check if another area is free] " + booking.message).strip()
                booking.save()
                booking_notification(booking)
                notify_team(booking)
                email_customer(booking)
                return redirect("booking_done", token=booking.token)
            form.add_error("event_date", result["message"])
    else:
        # Prefill from the home page availability bar
        initial = {}
        if request.GET.get("type"):
            initial["event_type"] = request.GET.get("type")
        day = parse_date(request.GET.get("date"))
        guests = parse_guests(request.GET.get("guests"))
        if day:
            initial["event_date"] = day.isoformat()
            result = availability_result(day, guests)
        if guests:
            initial["guests"] = guests
        form = EnquiryForm(initial=initial)
    ask = None
    if result and result.get("can_ask"):
        label = dict(Enquiry.EVENT_TYPE_CHOICES).get(form["event_type"].value(), "")
        ask = ask_details(date.fromisoformat(result["date"]), form["guests"].value(), label.lower())
    context = {"form": form, "result": result, "ask": ask, "asking": (request.POST.get("ask") or request.GET.get("ask")) == "1",
               "steps": STEPS, "page": "book"}
    return render(request, "core/book.html", context)


def booking_done(request, token):
    booking = get_object_or_404(Enquiry, token=token)
    asked = booking.message.startswith("[Asked about a busy date")
    return render(request, "core/booking_done.html", {"booking": booking, "asked": asked, "page": "book"})


def contact(request):
    if request.method == "POST":
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            msg = form.save()
            message_notification(msg)
            notify_message(msg)
            messages.success(request, f"Thanks, {msg.name}. We got your message and will get back to you on {msg.phone}.")
            return redirect("contact")
    else:
        form = ContactMessageForm()
    return render(request, "core/contact.html", {"form": form, "page": "contact"})


def notify_message(msg):
    """Email the team about a new contact message, if email is set up."""
    recipient = settings.ENQUIRY_NOTIFY_EMAIL
    if not recipient:
        return
    body = f"New message from the website\n\nName: {msg.name}\nPhone: {msg.phone}\nEmail: {msg.email or '-'}\n\n{msg.message}"
    send_mail(f"New message: {msg.name}", body, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=True)


def email_customer(booking):
    """Send the customer a copy of their request, if they gave an email address."""
    if not booking.email:
        return
    body = (
        f"Hi {booking.name},\n\n"
        f"Thanks for booking with Embokodweni Lifestyle. Your reference is {booking.reference}.\n\n"
        f"Event: {booking.get_event_type_display()}\n"
        f"Date: {booking.event_date}\n"
        f"Guests: {booking.guests or '-'}\n\n"
        f"Our team will call you on {booking.phone} to confirm.\n\n"
        f"Embokodweni Lifestyle"
    )
    send_mail(f"Your booking request {booking.reference}", body, settings.DEFAULT_FROM_EMAIL, [booking.email], fail_silently=True)


def work_with_us(request):
    """Partnership page. People contact the team directly by WhatsApp, phone or email."""
    site = SiteInfo.load()
    tracks = []
    for t in PARTNER_TRACKS:
        track = dict(t)
        text = f"Hi Embokodweni Lifestyle, I'm interested in working with you ({t['title']})."
        if site.whatsapp:
            track["contact_url"] = f"https://wa.me/{site.whatsapp}?text={quote_plus(text)}"
        elif site.email:
            track["contact_url"] = f"mailto:{site.email}?subject={quote_plus('Partnership: ' + t['title'])}"
        else:
            track["contact_url"] = "#contact-options"
        tracks.append(track)
    partner_text = "Hi Embokodweni Lifestyle, I'd like to talk about working with you."
    context = {
        "tracks": tracks,
        "banner": pic(6),
        "wa_url": f"https://wa.me/{site.whatsapp}?text={quote_plus(partner_text)}" if site.whatsapp else "",
        "mail_url": f"mailto:{site.email}?subject={quote_plus('Partnership enquiry')}" if site.email else "",
        "page": "work",
    }
    return render(request, "core/work.html", context)


def notify_team(enquiry):
    """Email the team about a new enquiry. It is always saved in the admin too."""
    recipient = settings.ENQUIRY_NOTIFY_EMAIL
    if not recipient:
        return
    body = (
        f"New booking request {enquiry.reference} from the website\n\n"
        f"Name: {enquiry.name}\n"
        f"Phone: {enquiry.phone}\n"
        f"Email: {enquiry.email or '-'}\n"
        f"Event type: {enquiry.get_event_type_display()}\n"
        f"Preferred date: {enquiry.event_date or '-'}\n"
        f"Guests: {enquiry.guests or '-'}\n\n"
        f"{enquiry.message}"
    )
    send_mail(f"New booking {enquiry.reference}: {enquiry.name}", body, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=True)
