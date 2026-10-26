from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),
    path("whats-on/", views.events, name="events"),
    path("gallery/", views.gallery, name="gallery"),
    path("book/", views.book, name="book"),
    path("book/done/<uuid:token>/", views.booking_done, name="booking_done"),
    path("availability/", views.check_availability, name="availability"),
    path("contact/", views.contact, name="contact"),
    path("work-with-us/", views.work_with_us, name="work"),
]
