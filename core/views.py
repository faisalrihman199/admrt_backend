from django.http import JsonResponse
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from django.conf import settings
from rest_framework.decorators import action
from .serializers import UserCountSerializer
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from collections import defaultdict
from newChat.models import Message
from rest_framework.exceptions import PermissionDenied
from .models import Visitor
from django.core.exceptions import ObjectDoesNotExist
from django.db import models  # Ensure models is imported
from django.db.models import Count, OuterRef, Subquery
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from django.db.models import Count,Q
from django.db.models.functions import ExtractMonth,ExtractDay,ExtractWeek, TruncDay, TruncWeek, TruncMonth, TruncYear
from datetime import timedelta
from .models import User,AffiliateLink,AffiliateLinkVisit
from .serializers import UserDetailSerializer, UserPartialUpdateSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer,AdvertiserProductCountSerializer,AffiliateLinkSerializer
from users.models import AdvertiserProduct,AdSpaceForSpaceHost
from rest_framework.pagination import PageNumberPagination
from datetime import datetime
class CustomPagination(PageNumberPagination):
    page_size = 10  # Default number of records per page
    page_size_query_param = 'page_size'  # Allow clients to set page size
    max_page_size = 100  # Maximum page size allowed

class UserViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    # def settings(self, request):
    #     user = self.request.user
    #     serializer = self.get_serializer(user)
    #     return Response(serializer.data)

    def list(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        user = self.request.user
        serializer = UserPartialUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    # def update_settings(self, request):
    #     user = self.request.user
    #     serializer = UserPartialUpdateSerializer(user, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=400)
    
    
class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password reset code has been sent to your email."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
    
    
# class UserViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = UserDetailSerializer

#     def get_queryset(self):
#         requested_user_id = self.request.GET.get('id')
#         if requested_user_id is not None:
#             user_id = requested_user_id
#         else:
#             user_id = self.request.user.id
#         # Fetch the user profile
#         queryset = get_user_model().objects.filter(id=user_id).first().profile
#         if hasattr(queryset, 'spacehost'):
#             self.serializer_class = SpaceHostSerializer
#             queryset = queryset.spacehost
#         elif hasattr(queryset, 'advertiser'):
#             self.serializer_class = AdvertiserSerializer
#             queryset = queryset.advertiser
#         else:
#             queryset = None
#         return queryset

#     def list(self, request):
#         queryset = self.get_queryset()
#         # serializer_class = self.get_serializer_class()
#         serializer = self.serializer_class(queryset, many=False)
#         return Response(serializer.data)
    
#     def create(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         if queryset is None:
#             return Response(status=status.HTTP_403_FORBIDDEN, data={"details": "Profile creation should have been done at the registration level. Seems like that was not done. Something went wrong."})
#         else:
#             serializer = self.get_serializer(queryset, data=request.data, partial=True)
#             serializer.is_valid(raise_exception=True)
#             self.perform_update(serializer)
#             return Response(serializer.data)



class UserCountView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        roles = ['advertiser', 'space_host']
        period = request.query_params.get('period')
        
        if period not in ['daily', 'weekly', 'monthly', 'all']:
            raise ValidationError("Invalid period specified.")
        
        current_time = timezone.now()

        # Dictionaries to store counts
        total_accounts = defaultdict(int)
        advertisers_accounts = defaultdict(int)
        ad_hosts_accounts = defaultdict(int)

        total_queryset = User.objects.filter(
            Q(user_role='space_host') | Q(user_role='advertiser')
        )
        total_account_nums = total_queryset.count()

        if period == 'monthly':
            start_of_year = current_time.replace(month=1, day=1)
            total_queryset = total_queryset.filter(date_joined__gte=start_of_year)
            total_monthly_data = total_queryset.annotate(month=ExtractMonth('date_joined')).values('month').annotate(count=Count('id'))

            for entry in total_monthly_data:
                month_number = entry['month']
                month_name = timezone.datetime(current_time.year, month_number, 1).strftime('%b')
                total_accounts[month_name] += entry['count']

            for role in roles:
                role_id = settings.K_ADVERTISER_ID if role == 'advertiser' else settings.K_SPACE_HOST_ID
                queryset = User.objects.filter(user_role=role_id, date_joined__gte=start_of_year)
                monthly_data = queryset.annotate(month=ExtractMonth('date_joined')).values('month').annotate(count=Count('id'))

                for entry in monthly_data:
                    month_name = timezone.datetime(current_time.year, entry['month'], 1).strftime('%b')
                    if role == 'advertiser':
                        advertisers_accounts[month_name] += entry['count']
                    else:
                        ad_hosts_accounts[month_name] += entry['count']

            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            data = {
                "totalAccountNums": total_account_nums,
                "totalAdvertiserNums": User.objects.filter(user_role=settings.K_ADVERTISER_ID).count(),
                "totalSpaceHostNums": User.objects.filter(user_role=settings.K_SPACE_HOST_ID).count(),
                "totalAccounts": [{"name": month, "value": total_accounts.get(month, 0)} for month in months],
                "advertisersAccounts": [{"name": month, "value": advertisers_accounts.get(month, 0)} for month in months],
                "adHostsAccounts": [{"name": month, "value": ad_hosts_accounts.get(month, 0)} for month in months],
            }

        elif period == 'daily':
            start_of_week = current_time - timedelta(days=current_time.weekday())
            end_of_week = start_of_week + timedelta(days=6)

            total_weekly_data = total_queryset.filter(date_joined__range=[start_of_week, end_of_week]).annotate(day=ExtractDay('date_joined')).values('day').annotate(count=Count('id'))

            for entry in total_weekly_data:
                day_number = entry['day']
                day_name = timezone.datetime(current_time.year, current_time.month, day_number).strftime('%a')
                total_accounts[day_name] += entry['count']

            for role in roles:
                role_id = settings.K_ADVERTISER_ID if role == 'advertiser' else settings.K_SPACE_HOST_ID
                queryset = User.objects.filter(user_role=role_id, date_joined__range=[start_of_week, end_of_week])
                weekly_data = queryset.annotate(day=ExtractDay('date_joined')).values('day').annotate(count=Count('id'))

                for entry in weekly_data:
                    day_name = timezone.datetime(current_time.year, current_time.month, entry['day']).strftime('%a')
                    if role == 'advertiser':
                        advertisers_accounts[day_name] += entry['count']
                    else:
                        ad_hosts_accounts[day_name] += entry['count']

            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            data = {
                "totalAccountNums": total_account_nums,
                "totalAdvertiserNums": User.objects.filter(user_role=settings.K_ADVERTISER_ID).count(),
                "totalSpaceHostNums": User.objects.filter(user_role=settings.K_SPACE_HOST_ID).count(),
                "totalAccounts": [{"name": day, "value": total_accounts.get(day, 0)} for day in days],
                "advertisersAccounts": [{"name": day, "value": advertisers_accounts.get(day, 0)} for day in days],
                "adHostsAccounts": [{"name": day, "value": ad_hosts_accounts.get(day, 0)} for day in days],
            }

        elif period == 'weekly':
            weeks_data = []
            # Start with the last 3 full weeks
            for week in range(3, 0, -1):
                start_of_week = current_time - timedelta(weeks=week, days=current_time.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                weeks_data.append((start_of_week, end_of_week))

            # Add the current partial week (up to today)
            start_of_current_week = current_time - timedelta(days=current_time.weekday())
            weeks_data.append((start_of_current_week, current_time))

            # Sort weeks in ascending order
            weeks_data = sorted(weeks_data, key=lambda x: x[0])

            for start_of_week, end_of_week in weeks_data:
                # Format date as "28 Oct - 03 Nov" with spaces between day and month
                formatted_range = f"{start_of_week.day} {start_of_week.strftime('%b')} - {end_of_week.day} {end_of_week.strftime('%b')}"
                total_weekly_data = total_queryset.filter(date_joined__range=[start_of_week, end_of_week]).count()
                total_accounts[formatted_range] = total_weekly_data

                for role in roles:
                    role_id = settings.K_ADVERTISER_ID if role == 'advertiser' else settings.K_SPACE_HOST_ID
                    role_count = total_queryset.filter(user_role=role_id, date_joined__range=[start_of_week, end_of_week]).count()
                    if role == 'advertiser':
                        advertisers_accounts[formatted_range] += role_count
                    else:
                        ad_hosts_accounts[formatted_range] += role_count

            data = {
                "totalAccountNums": total_account_nums,
                "totalAdvertiserNums": User.objects.filter(user_role=settings.K_ADVERTISER_ID).count(),
                "totalSpaceHostNums": User.objects.filter(user_role=settings.K_SPACE_HOST_ID).count(),
                "totalAccounts": [{"name": range_key, "value": total_accounts.get(range_key, 0)} for range_key in total_accounts],
                "advertisersAccounts": [{"name": range_key, "value": advertisers_accounts.get(range_key, 0)} for range_key in advertisers_accounts],
                "adHostsAccounts": [{"name": range_key, "value": ad_hosts_accounts.get(range_key, 0)} for range_key in ad_hosts_accounts],
            }

        
        elif period == 'all':
            current_year = current_time.year
            for year in range(current_year - 10, current_year + 1):
                year_start = timezone.datetime(year, 1, 1)
                year_end = timezone.datetime(year + 1, 1, 1)
                total_count = total_queryset.filter(date_joined__range=[year_start, year_end]).count()
                total_accounts[year] = total_count

                for role in roles:
                    role_id = settings.K_ADVERTISER_ID if role == 'advertiser' else settings.K_SPACE_HOST_ID
                    role_count = total_queryset.filter(user_role=role_id, date_joined__range=[year_start, year_end]).count()
                    if role == 'advertiser':
                        advertisers_accounts[year] = role_count
                    else:
                        ad_hosts_accounts[year] = role_count

            data = {
                "totalAccountNums": total_account_nums,
                "totalAdvertiserNums": User.objects.filter(user_role=settings.K_ADVERTISER_ID).count(),
                "totalSpaceHostNums": User.objects.filter(user_role=settings.K_SPACE_HOST_ID).count(),
                "totalAccounts": [{"name": year, "value": total_accounts.get(year, 0)} for year in range(current_year - 10, current_year + 1)],
                "advertisersAccounts": [{"name": year, "value": advertisers_accounts.get(year, 0)} for year in range(current_year - 10, current_year + 1)],
                "adHostsAccounts": [{"name": year, "value": ad_hosts_accounts.get(year, 0)} for year in range(current_year - 10, current_year + 1)],
            }

        return Response({
            "success": True,
            "message": "User counts retrieved successfully.",
            "data": data,
        })

class MessageCountView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        roles = ['advertiser', 'space_host']
        period = request.query_params.get('period')

        if period not in ['daily', 'weekly', 'monthly', 'all']:
            raise ValidationError("Invalid period specified.")

        current_time = timezone.now()
        total_messages = defaultdict(int)
        advertiser_messages = defaultdict(int)
        space_host_messages = defaultdict(int)

        # Total message counts for each role
        total_message_nums = Message.objects.count()
        total_advertiser_msgs = Message.objects.filter(sender__user_role=settings.K_ADVERTISER_ID).count()
        total_space_host_msgs = Message.objects.filter(sender__user_role=settings.K_SPACE_HOST_ID).count()

        if period == 'monthly':
            start_of_year = current_time.replace(month=1, day=1)
            messages_queryset = Message.objects.filter(created_at__gte=start_of_year)
            monthly_data = messages_queryset.annotate(month=ExtractMonth('created_at')).values('month').annotate(count=Count('id'))

            for entry in monthly_data:
                month_number = entry['month']
                month_name = timezone.datetime(current_time.year, month_number, 1).strftime('%b')
                total_messages[month_name] += entry['count']

        elif period == 'daily':
            start_of_week = current_time - timezone.timedelta(days=current_time.weekday())
            end_of_week = start_of_week + timezone.timedelta(days=6)
            daily_data = Message.objects.filter(created_at__range=[start_of_week, end_of_week]).annotate(day=ExtractDay('created_at')).values('day').annotate(count=Count('id'))

            for entry in daily_data:
                day_number = entry['day']
                day_name = timezone.datetime(current_time.year, current_time.month, day_number).strftime('%a')
                total_messages[day_name] += entry['count']

        if period == 'weekly':
            weeks_data = []
            # First three full weeks before the current week
            for week in range(3, 0, -1):
                start_of_week = current_time - timezone.timedelta(weeks=week, days=current_time.weekday())
                end_of_week = start_of_week + timezone.timedelta(days=6)
                weeks_data.append((start_of_week, end_of_week))

            # Add the current partial week (up to today)
            start_of_current_week = current_time - timezone.timedelta(days=current_time.weekday())
            weeks_data.append((start_of_current_week, current_time))

            # Initialize weekly data
            for start_of_week, end_of_week in weeks_data:
                # Format dates as "dd MMM"
                formatted_range = f"{start_of_week.strftime('%d %b')} - {end_of_week.strftime('%d %b')}"
                total_weekly_data = Message.objects.filter(created_at__range=[start_of_week, end_of_week]).count()
                total_messages[formatted_range] = total_weekly_data

                # Count messages by role within each weekly range
                for role in roles:
                    role_id = settings.K_ADVERTISER_ID if role == 'advertiser' else settings.K_SPACE_HOST_ID
                    role_count = Message.objects.filter(sender__user_role=role_id, created_at__range=[start_of_week, end_of_week]).count()
                    if role == 'advertiser':
                        advertiser_messages[formatted_range] += role_count
                    else:
                        space_host_messages[formatted_range] += role_count

            # Prepare the response data structure for the weekly period
            data = {
                "totalMessageNums": total_message_nums,
                "totalAdvertiserMessages": total_advertiser_msgs,
                "totalSpaceHostMessages": total_space_host_msgs,
                "totalMessages": [{"name": range_key, "value": total_messages.get(range_key, 0)} for range_key in total_messages],
                "advertiserMessages": [{"name": range_key, "value": advertiser_messages.get(range_key, 0)} for range_key in advertiser_messages],
                "spaceHostMessages": [{"name": range_key, "value": space_host_messages.get(range_key, 0)} for range_key in space_host_messages],
            }

        elif period == 'all':
            current_year = current_time.year
            for year in range(current_year - 10, current_year + 1):
                year_start = timezone.datetime(year, 1, 1)
                year_end = timezone.datetime(year + 1, 1, 1)

                total_count = Message.objects.filter(created_at__range=[year_start, year_end]).count()
                total_messages[year] = total_count

            data = {
                "totalMessageNums": total_message_nums,
                "totalAdvertiserMessages": total_advertiser_msgs,
                "totalSpaceHostMessages": total_space_host_msgs,
                "totalMessages": [{"name": year, "value": total_messages.get(year, 0)} for year in range(current_year - 10, current_year + 1)],
                "advertiserMessages": [{"name": year, "value": advertiser_messages.get(year, 0)} for year in range(current_year - 10, current_year + 1)],
                "spaceHostMessages": [{"name": year, "value": space_host_messages.get(year, 0)} for year in range(current_year - 10, current_year + 1)],
            }

        # Monthly period data structure
        elif period == 'monthly':
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            data = {
                "totalMessageNums": total_message_nums,
                "totalAdvertiserMessages": total_advertiser_msgs,
                "totalSpaceHostMessages": total_space_host_msgs,
                "totalMessages": [{"name": month, "value": total_messages.get(month, 0)} for month in months],
                "advertiserMessages": [{"name": month, "value": advertiser_messages.get(month, 0)} for month in months],
                "spaceHostMessages": [{"name": month, "value": space_host_messages.get(month, 0)} for month in months],
            }

        return Response({
            "success": True,
            "message": "Message counts retrieved successfully.",
            "data": data,
        })
def track_visitor(request):
    ip_address = request.META.get('REMOTE_ADDR')

    if ip_address:
        # Check if a visitor with this IP address already exists
        visitor_exists = Visitor.objects.filter(ip_address=ip_address).exists()
        
        if not visitor_exists:
            # Create a new visitor record if it doesn't exist
            Visitor.objects.create(ip_address=ip_address, visit_date=timezone.now())
            return JsonResponse({'message': 'Visitor recorded'}, status=201)
        else:
            return JsonResponse({'message': 'Visitor already recorded'}, status=200)
    else:
        return JsonResponse({'error': 'IP address not found'}, status=400)
    
class AdvertiserProductCountView(generics.ListAPIView):
    pagination_class = CustomPagination
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user_email = self.request.user.email  # Get user email directly
            user = User.objects.filter(email=user_email).first()  # Fetch user object safely

            # Check if the user exists
            if not user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            # Check if the user is a superuser
            if not user.is_superuser:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            # Fetch all users with the advertiser role
            advertisers = User.objects.filter(user_role=settings.K_ADVERTISER_ID)

            # Implement search functionality
            search_name = request.query_params.get('name', None)
            if search_name:
                advertisers_filtered = advertisers.filter(Q(full_name__icontains=search_name))
            else:
                advertisers_filtered = advertisers  # No filter applied if no search name

            # Prepare a list to hold the results
            result_data = []

            # Initialize total counts
            total_advertisers = advertisers.count()
            total_products = 0
            max_products = 0
            top_advertiser = None

            # Iterate over the filtered advertisers and count their products
            for advertiser in advertisers_filtered:
                product_count = AdvertiserProduct.objects.filter(user=advertiser.profile).count()
                total_products += product_count  # Accumulate the total number of products
                
                # Check if this advertiser has the most products
                if product_count > max_products:
                    max_products = product_count
                    top_advertiser = {
                        'id': advertiser.id,
                        'full_name': advertiser.full_name,
                        'product_count': product_count
                    }

                result_data.append({
                    'id': advertiser.id,
                    'full_name': advertiser.full_name,
                    'product_count': product_count
                })

            # Calculate the Advertiser with the most products from the original queryset
            for advertiser in advertisers:
                product_count = AdvertiserProduct.objects.filter(user=advertiser.profile).count()
                if product_count > max_products:
                    max_products = product_count
                    top_advertiser = {
                        'id': advertiser.id,
                        'full_name': advertiser.full_name,
                        'product_count': product_count
                    }

            # Pagination
            paginator = self.pagination_class()
            paginated_data = paginator.paginate_queryset(result_data, request)

            # Prepare the final response data
            response_data = {
                "success": True,
                "message": "Advertiser product count retrieved successfully",
                "data": {
                    "advertisers": paginated_data,
                    "total_advertisers": total_advertisers,
                    "total_products": total_products,
                    "top_advertiser": top_advertiser,
                    "current_page": paginator.page.number,
                    "total_items": len(result_data),
                    "total_pages": paginator.page.paginator.num_pages,
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the exception if needed
            print(f"Internal Server Error: {e}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SpaceHostAdCountView(generics.ListAPIView):
    pagination_class = CustomPagination
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user_email = self.request.user.email  # Get user email directly
            user = User.objects.filter(email=user_email).first()  # Fetch user object safely

            # Check if the user exists
            if not user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            # Check if the user is a superuser
            if not user.is_superuser:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            # Fetch all users with the Space Host role
            space_hosts = User.objects.filter(user_role=settings.K_SPACE_HOST_ID)

            # Implement search functionality
            search_name = request.query_params.get('name', None)
            if search_name:
                space_hosts_filtered = space_hosts.filter(Q(full_name__icontains=search_name))
            else:
                space_hosts_filtered = space_hosts  # No filter applied if no search name

            # Prepare a list to hold the results
            result_data = []
            total_ads = 0
            max_ads = {'id': None, 'full_name': None, 'ad_count': 0}

            # Iterate over the filtered Space Hosts and count their ads
            for space_host in space_hosts_filtered:
                ad_count = AdSpaceForSpaceHost.objects.filter(user=space_host.profile).count()
                total_ads += ad_count
                
                if ad_count > max_ads['ad_count']:
                    max_ads = {'id': space_host.id, 'full_name': space_host.full_name, 'ad_count': ad_count}
                
                result_data.append({
                    'id': space_host.id,
                    'full_name': space_host.full_name,
                    'ad_count': ad_count
                })

            # Calculate the Space Host with the most ads from the original queryset
            for space_host in space_hosts:
                ad_count = AdSpaceForSpaceHost.objects.filter(user=space_host.profile).count()
                if ad_count > max_ads['ad_count']:
                    max_ads = {'id': space_host.id, 'full_name': space_host.full_name, 'ad_count': ad_count}

            # Pagination
            paginator = self.pagination_class()
            paginated_data = paginator.paginate_queryset(result_data, request)

            # Prepare the final response data
            response_data = {
                "success": True,
                "message": "Space Host ad count retrieved successfully",
                "data": {
                    "total_space_hosts": space_hosts.count(),
                    "total_ads": total_ads,
                    "space_host_with_most_ads": max_ads,
                    "current_page": paginator.page.number,
                    "total_items": len(result_data),
                    "total_pages": paginator.page.paginator.num_pages,
                    "adhosts": paginated_data,
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the exception if needed
            print(f"Internal Server Error: {e}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class AddAffiliateLinkView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AffiliateLinkSerializer

    def post(self, request, *args, **kwargs):
        user_email = self.request.user.email

        # Fetch the user object from the database
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a superuser
        if not user.is_superuser:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        # Check if 'id' is in request data for update
        affiliate_link_id = request.data.get('id')
        if affiliate_link_id:
            try:
                # Fetch the existing affiliate link for update
                affiliate_link = AffiliateLink.objects.get(id=affiliate_link_id)
                serializer = self.get_serializer(affiliate_link, data=request.data, partial=True)
            except AffiliateLink.DoesNotExist:
                return Response({'error': 'Affiliate link not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Initialize the serializer for creating a new affiliate link
            serializer = self.get_serializer(data=request.data)

        # Validate and save (create or update) the affiliate link
        if serializer.is_valid():
            affiliate_link = serializer.save()
            action = "updated" if affiliate_link_id else "created"
            return Response(
                {'message': f'Affiliate link {action} successfully', 'link_id': affiliate_link.id},
                status=status.HTTP_200_OK if affiliate_link_id else status.HTTP_201_CREATED
            )

        # If validation fails, return the errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AddVisitView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]  # Allow anyone to access this view

    def get(self, request, *args, **kwargs):
        # Get the affiliate link ID from query parameters
        link_id = request.query_params.get('link')
        print("link_id is", link_id)

        # Validate ID input
        if not link_id:
            return Response({'error': 'ID parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get the affiliate link by ID
            affiliate_link = AffiliateLink.objects.get(url=link_id)
            print("affiliate link is", affiliate_link)

            # Get visitor's IP address
            ip_address = request.META.get('REMOTE_ADDR')

            # Check if this IP has already visited this link using the link ID
            visit, created = AffiliateLinkVisit.objects.get_or_create(
                link=affiliate_link,
                ip_address=ip_address,
                defaults={'visit_date': timezone.now()}
            )

            if not created:
                # If the visit record already exists, we don't count it again
                return Response({'message': 'Visit already counted'}, status=status.HTTP_200_OK)

            # If this is a new visit, we do not need to increment anything
            # Instead, we will count the total visits
            total_visits = AffiliateLinkVisit.objects.filter(link=affiliate_link).count()

            return Response({'message': 'Visit counted successfully', 'visits': total_visits}, status=status.HTTP_201_CREATED)

        except ObjectDoesNotExist:
            return Response({'error': 'Affiliate link not found'}, status=status.HTTP_404_NOT_FOUND)




class AffiliateLinkStatsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        user_email = self.request.user
        try:
            user = User.objects.get(email=user_email)
            print("user object is ",user)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a superuser
        if not user.is_superuser:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        # Total number of affiliate links
        total_links = AffiliateLink.objects.count()

        # Number of links that have been visited at least once
        visited_links_count = AffiliateLinkVisit.objects.values('link').distinct().count()

        # Number of links that have not been visited even once
        unvisited_links_count = total_links - visited_links_count

        # Retrieve links and count visits
        affiliate_links = AffiliateLink.objects.annotate(visit_count=Count('visits'))

        # Pagination
        paginator = self.pagination_class()
        paginated_links = paginator.paginate_queryset(affiliate_links, request)

        # Prepare response data
        response_data = {
            'success': True,
            'message': 'Affiliate link statistics retrieved successfully',
            'data': {
                'total_links': total_links,
                'visited_links_count': visited_links_count,
                'unvisited_links_count': unvisited_links_count,
                'current_page': paginator.page.number,  # Current page number
                'total_items': paginator.page.paginator.count,  # Total number of items
                'total_pages': paginator.page.paginator.num_pages,  # Total number of pages
                'links': [{'id': link.id, 'url': "https://admrt.com?referal="+link.url, 'visit_count': link.visit_count} for link in paginated_links],
            }
        }

        return Response(response_data,status=status.HTTP_200_OK)

class AffiliateLinkUpdateView(generics.GenericAPIView):
    def put(self, request):
        try:
            # Get the ID and new URL from the request body
            affiliate_link_id = request.data.get('id')
            new_url = request.data.get('url')

            # Validate the input
            if not affiliate_link_id or not new_url:
                return Response({"error": "ID and new URL are required"}, status=status.HTTP_400_BAD_REQUEST)

            # Get the AffiliateLink instance by ID
            affiliate_link = AffiliateLink.objects.get(id=affiliate_link_id)
            
            # Update the URL with the new value
            affiliate_link.url = new_url
            affiliate_link.save()

            return Response({"success": True, "message": "URL updated successfully"}, status=status.HTTP_200_OK)
        
        except AffiliateLink.DoesNotExist:
            return Response({"error": "AffiliateLink not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AffiliateLinkDeleteView(generics.GenericAPIView):
    def delete(self, request, id):
        try:
            # Get the AffiliateLink instance by ID
            affiliate_link = AffiliateLink.objects.get(id=id)
            
            # Delete the AffiliateLink
            affiliate_link.delete()

            return Response({"success": True, "message": "Affiliate link deleted successfully"}, status=status.HTTP_200_OK)
        
        except AffiliateLink.DoesNotExist:
            return Response({"error": "AffiliateLink not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class VisitorCountView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        period = request.query_params.get('period')

        if period not in ['daily', 'weekly', 'monthly', 'all']:
            raise ValidationError("Invalid period specified.")

        current_time = timezone.now()
        total_visitors = defaultdict(int)
        affiliate_visitors = defaultdict(int)

        # Total visitor counts
        total_visitor_nums = Visitor.objects.count()
        total_affiliate_visitors = AffiliateLinkVisit.objects.count()

        if period == 'monthly':
            # Monthly data
            monthly_data = Visitor.objects.annotate(month=ExtractMonth('visit_date')).values('month').annotate(count=Count('id'))
            for entry in monthly_data:
                month_number = entry['month']
                month_name = datetime(current_time.year, month_number, 1).strftime('%b')
                total_visitors[month_name] += entry['count']

            affiliate_monthly_data = AffiliateLinkVisit.objects.annotate(month=ExtractMonth('visit_date')).values('month').annotate(count=Count('id'))
            for entry in affiliate_monthly_data:
                month_number = entry['month']
                month_name = datetime(current_time.year, month_number, 1).strftime('%b')
                affiliate_visitors[month_name] += entry['count']

        elif period == 'daily':
            # Daily data for today
            daily_data = Visitor.objects.filter(visit_date=current_time.date()).annotate(day=ExtractDay('visit_date')).values('day').annotate(count=Count('id'))
            for entry in daily_data:
                day_number = entry['day']
                day_name = datetime(current_time.year, current_time.month, day_number).strftime('%a')
                total_visitors[day_name] += entry['count']

            affiliate_daily_data = AffiliateLinkVisit.objects.filter(visit_date__date=current_time.date()).annotate(day=ExtractDay('visit_date')).values('day').annotate(count=Count('id'))
            for entry in affiliate_daily_data:
                day_number = entry['day']
                day_name = datetime(current_time.year, current_time.month, day_number).strftime('%a')
                affiliate_visitors[day_name] += entry['count']

        elif period == 'weekly':
            # Weekly data for the past four weeks
            weeks_data = []
            for week in range(4):
                start_of_week = current_time - timedelta(weeks=week, days=current_time.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                weeks_data.append((start_of_week, end_of_week))

            for week_number, (start_of_week, end_of_week) in enumerate(weeks_data, start=1):
                total_weekly_data = Visitor.objects.filter(visit_date__range=[start_of_week, end_of_week]).count()
                total_visitors[f"Week {week_number}"] += total_weekly_data

                affiliate_weekly_data = AffiliateLinkVisit.objects.filter(visit_date__range=[start_of_week, end_of_week]).count()
                affiliate_visitors[f"Week {week_number}"] += affiliate_weekly_data

        elif period == 'all':
            current_year = current_time.year
            for year in range(current_year - 10, current_year + 1):
                year_start = datetime(year, 1, 1)
                year_end = datetime(year + 1, 1, 1)

                total_count = Visitor.objects.filter(visit_date__range=[year_start, year_end]).count()
                total_visitors[year] = total_count

                affiliate_count = AffiliateLinkVisit.objects.filter(visit_date__range=[year_start, year_end]).count()
                affiliate_visitors[year] = affiliate_count

        # Prepare response data with combined visitors for each period
        response_data = {
            "totalSiteVisitors": total_visitor_nums,
            "totalAffiliateVisitors": total_affiliate_visitors,
            "chartData": [
                {"label": 'All Visitors', "value": total_visitor_nums + total_affiliate_visitors},
                {"label": 'Normal Users', "value": total_visitor_nums},
                {"label": 'Custom Linked', "value": total_affiliate_visitors},
            ],
            "totalVisitors": total_visitor_nums + total_affiliate_visitors,
        }

        if period == 'daily':
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            response_data.update({
                "siteVisitors": [{"name": day, "value": total_visitors.get(day, 0)} for day in days],
                "affiliateVisitors": [{"name": day, "value": affiliate_visitors.get(day, 0)} for day in days],
                "combinedVisitors": [
                    {
                        "name": day,
                        "value": total_visitors.get(day, 0) + affiliate_visitors.get(day, 0)
                    } for day in days
                ],
            })
       
        elif period == 'weekly':
                # Weekly data for the past four weeks with the last week being up to today
            weeks_data = []
            
            # Calculate the last 3 full weeks first
            for week in range(1, 4):
                # Start of the week (Monday) - Subtract the number of weeks
                start_of_week = current_time - timedelta(weeks=week, days=current_time.weekday())  
                end_of_week = start_of_week + timedelta(days=6)  # End of the week (Sunday)
                weeks_data.append((start_of_week, end_of_week))

            # Calculate the current (incomplete) week
            start_of_last_week = current_time - timedelta(days=current_time.weekday())  # Start of this week (Monday)
            end_of_last_week = current_time  # End of today
            weeks_data.append((start_of_last_week, end_of_last_week))

            # Sort weeks_data based on the start_of_week date so earlier ranges appear first
            weeks_data.sort(key=lambda x: x[0])

            # Use formatted week ranges like "14 Oct - 20 Oct" for each week
            total_visitors = {}
            affiliate_visitors = {}

            for start_of_week, end_of_week in weeks_data:
                week_range = f"{start_of_week.strftime('%d %b')} - {end_of_week.strftime('%d %b')}"

                # Get total weekly data (for visitors)
                total_weekly_data = Visitor.objects.filter(visit_date__range=[start_of_week, end_of_week]).count()
                total_visitors[week_range] = total_weekly_data

                # Get affiliate weekly data (for affiliate visitors)
                affiliate_weekly_data = AffiliateLinkVisit.objects.filter(visit_date__range=[start_of_week, end_of_week]).count()
                affiliate_visitors[week_range] = affiliate_weekly_data

            # Prepare response using the formatted week range
            response_data = {
                "totalSiteVisitors": total_visitor_nums,
                "totalAffiliateVisitors": total_affiliate_visitors,
                "chartData": [
                    {"label": 'All Visitors', "value": total_visitor_nums + total_affiliate_visitors},
                    {"label": 'Normal Users', "value": total_visitor_nums},
                    {"label": 'Custom Linked', "value": total_affiliate_visitors},
                ],
                "totalVisitors": total_visitor_nums + total_affiliate_visitors,
                "siteVisitors": [
                    {"name": week_range, "value": total_visitors.get(week_range, 0)}
                    for week_range in total_visitors.keys() if "Week" not in week_range  # Remove Week 1 and Week 2
                ],
                "affiliateVisitors": [
                    {"name": week_range, "value": affiliate_visitors.get(week_range, 0)}
                    for week_range in affiliate_visitors.keys() if "Week" not in week_range  # Remove Week 1 and Week 2
                ],
                "combinedVisitors": [
                    {
                        "name": week_range,
                        "value": total_visitors.get(week_range, 0) + affiliate_visitors.get(week_range, 0)
                    } for week_range in total_visitors.keys() if "Week" not in week_range  # Remove Week 1 and Week 2
                ],
            }

        elif period == 'monthly':
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            response_data.update({
                "siteVisitors": [{"name": month, "value": total_visitors.get(month, 0)} for month in months],
                "affiliateVisitors": [{"name": month, "value": affiliate_visitors.get(month, 0)} for month in months],
                "combinedVisitors": [
                    {
                        "name": month,
                        "value": total_visitors.get(month, 0) + affiliate_visitors.get(month, 0)
                    } for month in months
                ],
            })

        elif period == 'all':
            current_year = current_time.year
            response_data.update({
                "siteVisitors": [{"name": year, "value": total_visitors.get(year, 0)} for year in range(current_year - 10, current_year + 1)],
                "affiliateVisitors": [{"name": year, "value": affiliate_visitors.get(year, 0)} for year in range(current_year - 10, current_year + 1)],
                "combinedVisitors": [
                    {
                        "name": year,
                        "value": total_visitors.get(year, 0) + affiliate_visitors.get(year, 0)
                    } for year in range(current_year - 10, current_year + 1)
                ],
            })

        return Response({
            "success": True,
            "message": "Visitor counts retrieved successfully.",
            "data": response_data,
        })
class RecreateUserView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user_id = user_id = request.query_params.get('id')  # Get user_id from the query parameters

        if not user_id:
            return Response({'error': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the user object
            user = User.objects.get(id=user_id)

            # Store user's information
            user_info = {
                'email': user.email,
                'phone': user.phone,
                'full_name': user.full_name,
                'country': user.country,
                'birthday': user.birthday,
                'user_role': user.user_role,
                'password': user.password,  # Keep the hashed password
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'reset_code': user.reset_code,
                'reset_code_expiry': user.reset_code_expiry,
                'last_seen': user.last_seen,
                'username':user.username
            }

            # Hard delete the user
            User.hard_delete(user_id)

           

            return Response({
                'message': 'User recreated successfully.',
                
            }, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DashboardStatsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = self.request.user
       

        if user.user_role != "admin":
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        # Count core users excluding admins
        total_users = User.objects.filter(
            Q(user_role='space_host') | Q(user_role='advertiser')
        ).count()

        # Count total messages
        total_messages = Message.objects.count()

        # Count total visitors (assuming Visitor and AffiliateLinkVisit are the models for visitors)
        total_visitors = Visitor.objects.count() + AffiliateLinkVisit.objects.count()

        # Count users with role 'space_host'
        space_host_count = User.objects.filter(user_role=settings.K_SPACE_HOST_ID).count()

        # Count users with role 'advertiser'
        advertiser_count = User.objects.filter(user_role=settings.K_ADVERTISER_ID).count()

        # Count total affiliate links
        total_affiliate_links = AffiliateLink.objects.count()

        # Prepare the response data
        response_data = {
            'total_users': total_users,
            'total_messages': total_messages,
            'total_visitors': total_visitors,
            'space_host_count': space_host_count,
            'advertiser_count': advertiser_count,
            'total_affiliate_links': total_affiliate_links
        }

        return Response({"success":True,"message":"data retrieved successfully","data":response_data}, status=status.HTTP_200_OK)