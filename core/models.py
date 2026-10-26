import uuid
from urllib.parse import quote_plus

from django.db import models


class SiteInfo(models.Model):
    """Contact details shown across the site. Only one row is used."""
    address = models.CharField(max_length=200, default="Stand No. 2300, Cunningmoore A Trust, Mkhuhlu, 1255",
                               help_text="Full street address")
    area = models.CharField(max_length=120, default="Cunningmoore A, Mkhuhlu, Mpumalanga",
                            help_text="Short location shown at the top of the home page")
    phone = models.CharField(max_length=30, blank=True, default="072 880 5923")
    phone_2 = models.CharField("Second phone", max_length=30, blank=True, default="068 068 8359")
    whatsapp = models.CharField(max_length=30, blank=True, help_text="Number in international format, e.g. 27720000000")
    email = models.EmailField(blank=True)
    trading_hours = models.TextField(blank=True, default="Monday to Sunday: 10:00 to 24:00\nPublic holidays: 10:00 to 24:00",
                                     help_text="One line per day group, e.g. Fri: 17:00 - late")
    owner_name = models.CharField(max_length=120, blank=True, default="Tumelo Bishop Mbokoto")
    liquor_licence_no = models.CharField("Liquor licence number", max_length=40, blank=True, default="9-2-1-11049")
    max_bookings_per_day = models.PositiveSmallIntegerField(
        default=1, help_text="How many confirmed bookings one day can take before it shows as fully booked.")
    max_guests = models.PositiveIntegerField(
        null=True, blank=True, help_text="Largest group the venue can host. Leave empty for no limit.")
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    map_url = models.URLField(blank=True, help_text="Optional: Google Maps share link to the venue. If empty, directions use the pin below.")
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, default=-24.892,
        help_text="Map pin. In Google Maps, right-click the venue and click the numbers at the top to copy them, e.g. -24.892000",
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, default=31.266,
        help_text="e.g. 31.266000",
    )
    map_zoom = models.PositiveSmallIntegerField(default=15, help_text="15 = streets, 17 = very close")

    class Meta:
        verbose_name = "Site contact info"
        verbose_name_plural = "Site contact info"

    def __str__(self):
        return "Contact info"

    @classmethod
    def load(cls):
        info = cls.objects.first()
        if info is None:
            info = cls.objects.create()
        return info

    def map_target(self):
        """What the map points at: the pin if set, otherwise the address."""
        if self.latitude is not None and self.longitude is not None:
            return f"{self.latitude},{self.longitude}"
        return self.address

    def map_embed_url(self):
        return f"https://maps.google.com/maps?q={quote_plus(self.map_target())}&z={self.map_zoom}&output=embed"

    def directions_url(self):
        if self.map_url:
            return self.map_url
        return "https://www.google.com/maps/dir/?api=1&destination=" + quote_plus(self.map_target())

    def share_location_url(self):
        """WhatsApp message with the venue's location, for sending to friends."""
        text = f"Meet me at Embokodweni Lifestyle, {self.address}: {self.directions_url()}"
        return "https://wa.me/?text=" + quote_plus(text)

    def phones(self):
        """Phone numbers as a list of (display, dial) pairs."""
        result = []
        for number in [self.phone, self.phone_2]:
            if number:
                dial = number.replace(" ", "")
                result.append((number, dial))
        return result

    def hours_list(self):
        return [line.strip() for line in self.trading_hours.splitlines() if line.strip()]


class Event(models.Model):
    CATEGORY_CHOICES = [
        ("dj", "Live DJ"),
        ("sports", "Sports"),
        ("braai", "Food & Braai"),
        ("celebration", "Celebration"),
        ("community", "Community"),
        ("lifestyle", "Lifestyle"),
    ]
    WEEKDAY_CHOICES = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
        (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
    ]

    title = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="dj")
    description = models.TextField(blank=True)
    is_weekly = models.BooleanField(default=False, help_text="Tick for a regular weekly event, then choose the weekday.")
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, null=True, blank=True)
    date = models.DateField(null=True, blank=True, help_text="For once-off events.")
    start_time = models.TimeField(null=True, blank=True)
    entry = models.CharField(max_length=60, blank=True, help_text="e.g. Free entry, R50 at the door")
    poster = models.ImageField(upload_to="events/", blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["date", "weekday", "start_time"]

    def __str__(self):
        return self.title

    def day_short(self):
        if self.is_weekly and self.weekday is not None:
            return self.get_weekday_display()[:3].upper()
        if self.date:
            return self.date.strftime("%a").upper()
        return ""


class GalleryPhoto(models.Model):
    image = models.ImageField(upload_to="gallery/")
    caption = models.CharField(max_length=150, blank=True)
    show_on_home = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    uploaded = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-uploaded"]

    def __str__(self):
        return self.caption or self.image.name


class Enquiry(models.Model):
    EVENT_TYPE_CHOICES = [
        ("private", "Private celebration"),
        ("birthday", "Birthday"),
        ("vip", "VIP table / area"),
        ("sports", "Sports viewing group"),
        ("corporate", "Corporate or year-end function"),
        ("community", "Community event"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("declined", "Declined"),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default="private")
    event_date = models.DateField(null=True, blank=True)
    guests = models.PositiveIntegerField(null=True, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending",
                              help_text="Confirmed bookings block the date on the website.")
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    staff_note = models.TextField(blank=True, help_text="Private notes for the team")
    is_read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def __str__(self):
        return f"{self.reference} {self.name} - {self.get_event_type_display()}"

    @property
    def reference(self):
        return f"EMB-{self.pk:04d}" if self.pk else "EMB-new"

    @property
    def is_question(self):
        """True when the customer asked about a date that showed as booked."""
        return self.message.startswith("[Asked about a busy date")

    @property
    def clean_message(self):
        if self.is_question:
            return self.message.split("]", 1)[1].strip()
        return self.message


class BlockedDate(models.Model):
    """Days the venue can't take bookings (already booked privately, closed, etc.)."""
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=120, blank=True, help_text="Only staff see this, e.g. Private function")

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.date} {self.reason}".strip()


class PartnerEnquiry(models.Model):
    """Enquiries from the Work with us page: sponsors, DJs, promoters, suppliers."""
    INTEREST_CHOICES = [
        ("sponsor", "Sponsorship / brand partnership"),
        ("dj", "DJ or performer"),
        ("promoter", "Event organiser / promoter"),
        ("corporate", "Corporate or group functions"),
        ("supplier", "Supplier / vendor"),
        ("other", "Something else"),
    ]

    name = models.CharField(max_length=100)
    organisation = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    interest = models.CharField(max_length=20, choices=INTEREST_CHOICES, default="sponsor")
    link = models.URLField(blank=True, help_text="Website, social media page or DJ mix link")
    message = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Partner enquiry"
        verbose_name_plural = "Partner enquiries"

    def __str__(self):
        return f"{self.name} - {self.get_interest_display()}"


class Testimonial(models.Model):
    """Real feedback from guests and clients. Only published ones show on the site."""
    name = models.CharField(max_length=80)
    role = models.CharField(max_length=80, blank=True, help_text="e.g. Hosted a 30th birthday, Regular on Saturdays")
    quote = models.TextField()
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.name}: {self.quote[:40]}"



class ContactMessage(models.Model):
    """General questions sent from the Contact page."""
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    message = models.TextField()
    staff_note = models.TextField(blank=True, help_text="Private notes for the team")
    is_read = models.BooleanField(default=False)
    handled = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.name}: {self.message[:40]}"


class Notification(models.Model):
    """One line in the dashboard bell: new booking, question or message."""
    KIND_CHOICES = [
        ("booking", "New booking"),
        ("question", "Busy-date question"),
        ("message", "New message"),
    ]
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    title = models.CharField(max_length=150)
    body = models.CharField(max_length=255, blank=True)
    url = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title
