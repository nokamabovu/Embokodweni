from django.conf import settings
from django.contrib import admin
from django.core.mail import send_mail
from django.utils.html import format_html

from .models import BlockedDate, ContactMessage, Enquiry, Event, GalleryPhoto, Notification, PartnerEnquiry, SiteInfo, Testimonial


@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ["__str__", "phone", "email"]
    fieldsets = [
        ("Business", {"fields": ["owner_name", "liquor_licence_no"]}),
        ("Contact", {"fields": ["address", "area", "phone", "phone_2", "whatsapp", "email", "trading_hours"]}),
        ("Map", {"fields": ["latitude", "longitude", "map_zoom", "map_url"],
                 "description": "Where the map pin and the Get directions button point."}),
        ("Bookings", {"fields": ["max_bookings_per_day", "max_guests"],
                      "description": "Used by Check availability and the booking page."}),
        ("Social media", {"fields": ["facebook_url", "instagram_url", "tiktok_url"]}),
    ]

    def has_add_permission(self, request):
        # Only one contact info row
        return not SiteInfo.objects.exists()


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "is_weekly", "weekday", "date", "start_time", "is_published"]
    list_filter = ["category", "is_weekly", "is_published"]
    list_editable = ["is_published"]
    search_fields = ["title", "description"]


@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    list_display = ["thumb", "caption", "show_on_home", "order"]
    list_editable = ["show_on_home", "order"]

    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px">', obj.image.url)
        return ""


@admin.register(Enquiry)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["reference", "name", "phone", "event_type", "event_date", "guests", "status", "created"]
    list_filter = ["status", "event_type"]
    list_editable = ["status"]
    search_fields = ["name", "phone", "email", "message"]
    date_hierarchy = "event_date"
    readonly_fields = ["reference", "created"]
    actions = ["confirm_bookings", "decline_bookings"]

    @admin.action(description="Confirm selected bookings (blocks the date on the website)")
    def confirm_bookings(self, request, queryset):
        for booking in queryset:
            booking.status = "confirmed"
            booking.handled = True
            booking.save()
            if booking.email:
                send_mail(
                    f"Booking confirmed {booking.reference}",
                    f"Hi {booking.name},\n\nYour booking at Embokodweni Lifestyle on {booking.event_date} is confirmed. "
                    f"See you then!\n\nReference: {booking.reference}\n\nEmbokodweni Lifestyle",
                    settings.DEFAULT_FROM_EMAIL, [booking.email], fail_silently=True,
                )
        self.message_user(request, f"{queryset.count()} booking(s) confirmed.")

    @admin.action(description="Decline selected bookings")
    def decline_bookings(self, request, queryset):
        count = queryset.update(status="declined", handled=True)
        self.message_user(request, f"{count} booking(s) declined.")


@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display = ["date", "reason"]


@admin.register(PartnerEnquiry)
class PartnerEnquiryAdmin(admin.ModelAdmin):
    list_display = ["name", "organisation", "interest", "phone", "created", "handled"]
    list_filter = ["interest", "handled"]
    list_editable = ["handled"]
    search_fields = ["name", "organisation", "phone", "email", "message"]
    readonly_fields = ["created"]


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ["name", "role", "is_published", "order"]
    list_editable = ["is_published", "order"]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "created", "is_read", "handled"]
    list_filter = ["handled", "is_read"]
    search_fields = ["name", "phone", "email", "message"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "created", "is_read"]
    list_filter = ["kind", "is_read"]
