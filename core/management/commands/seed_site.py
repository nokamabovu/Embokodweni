"""
Loads the starting content: the contact info row and a sample weekly
line-up. (The event photos are built into static/img/gallery.) Safe to run more than once; it only adds what is missing.

    python manage.py seed_site
"""
from datetime import time
from django.core.management.base import BaseCommand

from core.models import Event, SiteInfo

WEEKLY = [
    {"title": "Friday Night Sessions", "category": "dj", "weekday": 4, "start_time": time(17, 0),
     "description": "Resident DJs kick off the weekend after work."},
    {"title": "Match Day & Braai", "category": "sports", "weekday": 5, "start_time": time(12, 0),
     "description": "Big-screen football and rugby with the braai going all afternoon."},
    {"title": "Saturday Takeover", "category": "dj", "weekday": 5, "start_time": time(19, 0),
     "description": "Guest DJs and local talent until late. Themed nights every month."},
    {"title": "Sunday Chill", "category": "lifestyle", "weekday": 6, "start_time": time(13, 0),
     "description": "A slow afternoon with good food and soulful sounds to close the week."},
]


class Command(BaseCommand):
    help = "Load contact info and a sample weekly line-up"

    def handle(self, *args, **options):
        SiteInfo.load()

        # Weekly line-up (only when there are no weekly events yet)
        if not Event.objects.filter(is_weekly=True).exists():
            for data in WEEKLY:
                Event.objects.create(is_weekly=True, **data)
            self.stdout.write(f"Weekly events added: {len(WEEKLY)}")
        else:
            self.stdout.write("Weekly events already exist, skipped")

        self.stdout.write(self.style.SUCCESS("Seed complete"))
