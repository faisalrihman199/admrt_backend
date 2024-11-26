from .models import Visitor
from django.utils import timezone

class UniqueVisitorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the user's IP address
        ip_address = request.META.get('REMOTE_ADDR')
        today = timezone.now().date()

        # Check if the visitor with this IP has already visited today
        if not Visitor.objects.filter(ip_address=ip_address, visit_date=today).exists():
            # If not, record the new visit
            Visitor.objects.create(ip_address=ip_address, visit_date=today)

        response = self.get_response(request)
        return response
