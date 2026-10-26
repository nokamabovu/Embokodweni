from .models import Notification, SiteInfo


def site_info(request):
    context = {"site": SiteInfo.load()}
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and user.is_staff:
        context["staff_unread"] = Notification.objects.filter(is_read=False).count()
    return context
