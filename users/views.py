from collections import defaultdict
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from core.serializers import UserSerializer
from .models import (
    Topic,
    # Language,
    Portfolio,
    SocialMedia,
    AdvertiserProduct,
    AdSpaceForSpaceHost,
)
from django.db.models import Subquery, OuterRef
from .serializers import (
    SpaceHostSerializer,
    AdvertiserSerializer,
    TopicSerializer,
    # LanguageSerializer,
    PortfolioSerializer,
    SocialMediaSerializer,
    ProductSerializer,
    AdSpaceForSpaceHostSerializer
)
from .utils import object_is_not_related
from core.serializers import UserCountSerializer
from django.db.models import Count,Q
from django.db.models.functions import ExtractMonth,ExtractDay,ExtractWeek, TruncDay, TruncWeek, TruncMonth, TruncYear
from datetime import timedelta
from core.models import User
from rest_framework.viewsets import GenericViewSet
from django.utils import timezone
from collections import defaultdict
from ai_model.topic_similarity import TopicSimilarityModel 

class AdSpaceForSpaceHostViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AdSpaceForSpaceHostSerializer

    def get_queryset(self):
        admin_check = get_user_model().objects.filter(id=self.request.user.id).first()
        if admin_check.user_role == 'admin':
            # Admin can access all ad spaces
            return AdSpaceForSpaceHost.objects.all()
        # Regular users can only access their own ad spaces
        return AdSpaceForSpaceHost.objects.filter(user=self.request.user.id).all()
    
    def create(self, request, *args, **kwargs):
        try:
            admin_check = get_user_model().objects.filter(id=self.request.user.id).first()
            if admin_check.user_role == 'admin':
                # Admins can create AdSpace for any user
                user_req = request.data.get('userId')
            else:
                # Regular users can only create AdSpace for themselves
                user_req = self.request.user.id

            user_profile = get_user_model().objects.filter(id=user_req).first()

            data = request.data
            data.pop('userId', None)

            if isinstance(data, list):
                serializer = self.get_serializer(data=data, many=True)
            else:
                serializer = self.get_serializer(data=data)
                
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user_profile.profile.spacehost)
            
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        admin_check = get_user_model().objects.filter(id=self.request.user.id).first()
        if admin_check.user_role == 'admin':
            # Admin can delete any AdSpace
            instance = AdSpaceForSpaceHost.objects.filter(pk=self.kwargs['pk']).first()
        else:
            # Regular users can only delete their own AdSpace
            instance = self.get_object()

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdvertiserProductViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        # Subquery to fetch the full_name from the User model
        full_name_subquery = User.objects.filter(id=OuterRef('user__user_id')).values('full_name')[:1]

        # Annotate each AdvertiserProduct with the full_name of the associated User
        return AdvertiserProduct.objects.all().annotate(full_name=Subquery(full_name_subquery))

    def create(self, request, *args, **kwargs):
        print(f"POST Request Data: {self.request.user.id}")

        adminCheck = get_user_model().objects.filter(id=self.request.user.id).first()

        if adminCheck.user_role == 'admin':
            user_req = request.data.get('userId')
        else:
            user_req = self.request.user.id

        userProfile = get_user_model().objects.filter(id=user_req).first()

        related_object_issue = object_is_not_related(userProfile.profile, 'advertiser')
        if related_object_issue:
            return related_object_issue

        data = request.data
        data.pop('userId', None)

        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
        else:
            serializer = self.get_serializer(data=data)
            
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, userProfile)  # Pass userProfile to perform_create

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, userProfile):
        serializer.save(user=userProfile.profile.advertiser)

    def get_object(self):
        queryset = self.get_queryset()
        adminCheck = get_user_model().objects.filter(id=self.request.user.id).first()

        if adminCheck.user_role == 'admin':
            # Admin can delete any product
            obj = queryset.get(pk=self.kwargs['pk'])
        else:
            # Regular users can only delete their own products
            obj = queryset.get(pk=self.kwargs['pk'], user=self.request.user.id)

        return obj

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete() 
class AllAccounts(ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        return UserSerializer.objects.filter().all()
    
    def create(self, request, *args, **kwargs):
        related_object_issue = object_is_not_related(request.user.profile, 'advertiser')
        if related_object_issue:
            return related_object_issue
        data = request.data
        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
        else:
            serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        return serializer.save(user=self.request.user.profile.advertiser)
    
class AllAdvertiserProductViewSet(ListModelMixin, GenericViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        full_name_subquery = User.objects.filter(id=OuterRef('user__user_id')).values('full_name')[:1]
        # Annotate each AdvertiserProduct with the full_name of the associated User
        return AdvertiserProduct.objects.filter(productType="public").annotate(full_name=Subquery(full_name_subquery))

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Custom response structure
        response_data = {
            "message": "Products retrieved successfully",
            "success": True,
            "data": serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    

class SocialMediaViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SocialMediaSerializer

    def get_queryset(self):
        admin_check = get_user_model().objects.filter(id=self.request.user.id).first()
        if admin_check.user_role == 'admin':
            # Admin can access all social media objects
            return SocialMedia.objects.all()
        # Regular users only access their own social media objects
        return SocialMedia.objects.filter(user=self.request.user.id).all()

    def create(self, request, *args, **kwargs):
        admin_check = get_user_model().objects.filter(id=self.request.user.id).first()
        if admin_check.user_role == 'admin':
            user_req = request.data.get('userId')
        else:
            user_req = self.request.user.id

        user_profile = get_user_model().objects.filter(id=user_req).first()

        data = request.data
        data.pop('userId', None)

        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
        else:
            serializer = self.get_serializer(data=data)
        
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user_profile.profile)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        admin_check = get_user_model().objects.filter(id=self.request.user.id).first()
        if admin_check.user_role == 'admin':
            # Admin can delete any social media object
            instance = SocialMedia.objects.filter(pk=self.kwargs['pk']).first()
        else:
            # Regular users can only delete their own social media objects
            instance = self.get_object()
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class PortfolioViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PortfolioSerializer

    def get_queryset(self):
        admin_check = get_user_model().objects.filter(id=self.request.user.id).first()
        if admin_check.user_role == 'admin':
            # Admin can access all portfolios
            return Portfolio.objects.all()
        # Regular users can only access their own portfolios
        return Portfolio.objects.filter(user=self.request.user.id).all()

    def create(self, request, *args, **kwargs):
        admin_check = get_user_model().objects.filter(id=self.request.user.id).first()
        if admin_check.user_role == 'admin':
            # Admin can create portfolio for any user
            user_req = request.data.get('userId')
        else:
            # Regular users can only create portfolios for themselves
            user_req = self.request.user.id

        user_profile = get_user_model().objects.filter(id=user_req).first()

        related_object_issue = object_is_not_related(user_profile.profile, 'spacehost')
        if related_object_issue:
            return related_object_issue

        data = request.data
        data.pop('userId', None)

        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
        else:
            serializer = self.get_serializer(data=data)

        serializer.is_valid(raise_exception=True)
        serializer.save(user=user_profile.profile.spacehost)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        admin_check = get_user_model().objects.filter(id=self.request.user.id).first()
        if admin_check.user_role == 'admin':
            # Admin can delete any portfolio
            instance = Portfolio.objects.filter(pk=self.kwargs['pk']).first()
        else:
            # Regular users can only delete their own portfolios
            instance = self.get_object()

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

# class LanguageViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = LanguageSerializer

#     def get_queryset(self):
#         return Language.objects.filter(user=self.request.user.id).all()
    
#     def create(self, request, *args, **kwargs):
#         related_object_issue = object_is_not_related(request.user.profile, 'spacehost')
#         if related_object_issue:
#             return related_object_issue
#         data = request.data
#         if isinstance(data, list):
#             serializer = self.get_serializer(data=data, many=True)
#         else:
#             serializer = self.get_serializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         headers = self.get_success_headers(serializer.data)
#         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
#     def perform_create(self, serializer):
#         return serializer.save(user=self.request.user.profile.spacehost)


class TopicViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TopicSerializer

    def get_queryset(self):
        admin_check = get_user_model().objects.filter(id=self.request.user.id).first()
        if admin_check.user_role == 'admin':
            # Admins can access all topics
            return Topic.objects.all()
        # Regular users can only access their own topics
        return Topic.objects.filter(user=self.request.user.id).all()

    def create(self, request, *args, **kwargs):
        admin_check = get_user_model().objects.filter(id=self.request.user.id).first()
        if admin_check.user_role == 'admin':
            # Admins can create topics for any user
            user_req = request.data.get('userId')
        else:
            # Regular users can only create topics for themselves
            user_req = self.request.user.id

        user_profile = get_user_model().objects.filter(id=user_req).first()

        related_object_issue = object_is_not_related(user_profile.profile, 'spacehost')
        if related_object_issue:
            return related_object_issue

        data = request.data
        data.pop('userId', None)

        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
        else:
            serializer = self.get_serializer(data=data)

        serializer.is_valid(raise_exception=True)
        serializer.save(user=user_profile.profile.spacehost)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        admin_check = get_user_model().objects.filter(id=self.request.user.id).first()
        if admin_check.user_role == 'admin':
            # Admin can delete any topic
            instance = Topic.objects.filter(pk=self.kwargs['pk']).first()
        else:
            # Regular users can only delete their own topics
            instance = self.get_object()

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        requested_user_id = self.request.GET.get("id")
        user_id=None
        if (self.request.method=='POST'):
            request_body = self.request.data
            user_req = self.request.user.id
            adminCheck= get_user_model().objects.filter(id=user_req).first()
            if(adminCheck.user_role=='admin'):
                user_id=request_body['userId']
        if requested_user_id is not None:
            user_id = requested_user_id
        if (user_id is None):
            user_id = self.request.user.id
        # Fetch the user profile
        user = get_user_model().objects.filter(id=user_id).first()
        
        if user is None:
            print("User not found.")
            return None  # Handle case where user does not exist

        queryset = user.profile

        if hasattr(queryset, 'spacehost'):
            self.serializer_class = SpaceHostSerializer
            queryset = queryset.spacehost
        elif hasattr(queryset, 'advertiser'):
            self.serializer_class = AdvertiserSerializer
            queryset = queryset.advertiser
        else:
            queryset = None

        return queryset

    def list(self, request):
        queryset = self.get_queryset()
        if queryset is None:
            return Response(status=404, data={"details": "Not found."})
        
        serializer = self.serializer_class(queryset, many=False)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):

        queryset = self.get_queryset()
        if queryset is None:
            return Response(status=status.HTTP_403_FORBIDDEN, data={
                "details": "Profile creation should have been done at the registration level. Seems like that was not done. Something went wrong."
            })
        else:
            request_body=self.request.data
            try:
                del request_body['userId']
            except:
                pass
            serializer = self.get_serializer(queryset, data=request_body, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)  



class UserCountView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        # Always include both roles
        roles = ['advertiser', 'space_host']
        period = request.query_params.get('period')
        # Validate period
        if period not in ['daily', 'weekly', 'monthly', 'all']:
            raise ValidationError("Invalid period specified.")

        current_time = timezone.now()

        # Default dictionaries to hold counts
        total_accounts = defaultdict(int)
        advertisers_accounts = defaultdict(int)
        ad_hosts_accounts = defaultdict(int)

        # Base Queryset for total accounts
        total_queryset = User.objects.all()
        # Get total account numbers
        total_account_nums = total_queryset.count()

        # Process total accounts
        if period == 'monthly':
            start_of_year = current_time.replace(month=1, day=1)
            total_queryset = total_queryset.filter(date_joined__gte=start_of_year)
            total_monthly_data = total_queryset.annotate(month=ExtractMonth('date_joined')).values('month').annotate(count=Count('id'))

            for entry in total_monthly_data:
                month_number = entry['month']
                month_name = timezone.datetime(current_time.year, month_number, 1).strftime('%b')
                total_accounts[month_name] += entry['count']

        elif period == 'daily':
            start_of_week = current_time - timedelta(days=current_time.weekday())  # Start of the week (Monday)
            end_of_week = start_of_week + timedelta(days=6)  # End of the week (Sunday)
            
            # Process total accounts for the current week
            total_weekly_data = total_queryset.filter(date_joined__range=[start_of_week, end_of_week]).annotate(day=ExtractDay('date_joined')).values('day').annotate(count=Count('id'))

            for entry in total_weekly_data:
                day_number = entry['day']
                day_name = timezone.datetime(current_time.year, current_time.month, day_number).strftime('%a')  # Get short day name
                total_accounts[day_name] += entry['count']

        # Process each role's account data
        for role in roles:
            role_id = None
            if role == 'advertiser':
                role_id = settings.K_ADVERTISER_ID
            elif role == 'space_host':
                role_id = settings.K_SPACE_HOST_ID
            
            queryset = User.objects.filter(user_role=role_id)

            if period == 'monthly':
                start_of_year = current_time.replace(month=1, day=1)
                queryset = queryset.filter(date_joined__gte=start_of_year)
                monthly_data = queryset.annotate(month=ExtractMonth('date_joined')).values('month').annotate(count=Count('id'))

                for entry in monthly_data:
                    month_number = entry['month']
                    month_name = timezone.datetime(current_time.year, month_number, 1).strftime('%b')
                    if role == 'advertiser':
                        advertisers_accounts[month_name] += entry['count']
                    elif role == 'space_host':
                        ad_hosts_accounts[month_name] += entry['count']
            
            elif period == 'daily':
                # Process accounts for the current week
                weekly_data = queryset.filter(date_joined__range=[start_of_week, end_of_week]).annotate(day=ExtractDay('date_joined')).values('day').annotate(count=Count('id'))

                for entry in weekly_data:
                    day_number = entry['day']
                    day_name = timezone.datetime(current_time.year, current_time.month, day_number).strftime('%a')  # Get short day name
                    if role == 'advertiser':
                        advertisers_accounts[day_name] += entry['count']
                    elif role == 'space_host':
                        ad_hosts_accounts[day_name] += entry['count']

            elif period == 'weekly':
                # Calculate the start of the last 4 weeks
                weeks_data = []
                for week in range(4):
                    start_of_week = current_time - timedelta(weeks=week + 1, days=current_time.weekday())
                    end_of_week = start_of_week + timedelta(days=6)
                    weeks_data.append((start_of_week, end_of_week))

                # Process total accounts for the last 4 weeks
                for week_number, (start_of_week, end_of_week) in enumerate(weeks_data, start=1):
                    total_weekly_data = total_queryset.filter(date_joined__range=[start_of_week, end_of_week]).count()
                    total_accounts[f"Week {week_number}"] = total_weekly_data

                # Process role-specific accounts
                for role in roles:
                    role_id = settings.K_ADVERTISER_ID if role == 'advertiser' else settings.K_SPACE_HOST_ID
                    queryset = User.objects.filter(user_role=role_id)

                    for week_number, (start_of_week, end_of_week) in enumerate(weeks_data, start=1):
                        weekly_data = queryset.filter(date_joined__range=[start_of_week, end_of_week]).count()
                        if role == 'advertiser':
                            advertisers_accounts[f"Week {week_number}"] += weekly_data
                        else:
                            ad_hosts_accounts[f"Week {week_number}"] += weekly_data

            elif period == 'all':
                # Get the current year and the last 10 years
                current_year = current_time.year
                for year in range(current_year - 10, current_year + 1):
                    year_start = timezone.datetime(year, 1, 1)
                    year_end = timezone.datetime(year + 1, 1, 1)
                    
                    total_count = total_queryset.filter(date_joined__range=[year_start, year_end]).count()
                    total_accounts[year] = total_count

                    # Process role-specific accounts
                    for role in roles:
                        role_id = settings.K_ADVERTISER_ID if role == 'advertiser' else settings.K_SPACE_HOST_ID
                        queryset = User.objects.filter(user_role=role_id)
                        role_count = queryset.filter(date_joined__range=[year_start, year_end]).count()

                        if role == 'advertiser':
                            advertisers_accounts[year] = role_count
                        elif role == 'space_host':
                            ad_hosts_accounts[year] = role_count

        # Prepare the response data structure
        data = {}
        
        if period == 'daily':
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            data = {
                "totalAccountNums": total_account_nums,
                "totalAdvertiserNums": User.objects.filter(user_role="advertiser").count(),
                "totalSpaceHostNums": User.objects.filter(user_role="space_host").count(),
                "totalAccounts": [{"name": day, "value": total_accounts.get(day, 0)} for day in days],
                "advertisersAccounts": [{"name": day, "value": advertisers_accounts.get(day, 0)} for day in days],
                "adHostsAccounts": [{"name": day, "value": ad_hosts_accounts.get(day, 0)} for day in days],
            }
        elif period == 'weekly':
            data = {
                "totalAccountNums": total_account_nums,
                "totalAdvertiserNums": User.objects.filter(user_role="advertiser").count(),
                "totalSpaceHostNums": User.objects.filter(user_role="space_host").count(),
                "totalAccounts": [{"name": f"Week {i+1}", "value": total_accounts.get(f"Week {i+1}", 0)} for i in range(4)],
                "advertisersAccounts": [{"name": f"Week {i+1}", "value": advertisers_accounts.get(f"Week {i+1}", 0)} for i in range(4)],
                "adHostsAccounts": [{"name": f"Week {i+1}", "value": ad_hosts_accounts.get(f"Week {i+1}", 0)} for i in range(4)],
            }
        elif period == 'all':
            data = {
                "totalAccountNums": total_account_nums,
                "totalAdvertiserNums": User.objects.filter(user_role="advertiser").count(),
                "totalSpaceHostNums": User.objects.filter(user_role="space_host").count(),
                "totalAccounts": [{"name": year, "value": total_accounts.get(year, 0)} for year in range(current_year - 10, current_year + 1)],
                "advertisersAccounts": [{"name": year, "value": advertisers_accounts.get(year, 0)} for year in range(current_year - 10, current_year + 1)],
                "adHostsAccounts": [{"name": year, "value": ad_hosts_accounts.get(year, 0)} for year in range(current_year - 10, current_year + 1)],
            }
        else:
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            data = {
                "totalAccountNums": total_account_nums,
                "totalAdvertiserNums": User.objects.filter(user_role="advertiser").count(),
                "totalSpaceHostNums": User.objects.filter(user_role="space_host").count(),
                "totalAccounts": [{"name": month, "value": total_accounts.get(month, 0)} for month in months],
                "advertisersAccounts": [{"name": month, "value": advertisers_accounts.get(month, 0)} for month in months],
                "adHostsAccounts": [{"name": month, "value": ad_hosts_accounts.get(month, 0)} for month in months],
            }

        # Return the response with success status and message
        return Response({
            "success": True,
            "message": "User counts retrieved successfully.",
            "data": data,
        })
