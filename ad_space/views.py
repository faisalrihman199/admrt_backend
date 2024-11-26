from django.conf import settings
from django.db.models import Case, IntegerField, Q, Value, When, Count
from rest_framework import permissions
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from users.models import SpaceHost
from users.serializers import SpaceHostSerializer


class AdSpaceViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SpaceHostSerializer
    # queryset = SpaceHost.objects.all()
    
    def get_queryset(self):
        user_role = self.request.user.user_role
        if user_role != settings.K_ADVERTISER_ID:
            return None
        # Search terms
        search_term = self.request.GET.get('q')
        socials = []
        ad_types = []
        for key, value in settings.K_AD_TYPE_FILTERS.items():
            key = key.lower()
            sm = self.request.GET.get(key)
            if sm is not None and sm.lower() == 'true':
                ad_types.append(value)
        
        for key, value in settings.K_SOCIAL_MEDIA_FILTERS.items():
            key = key.lower()
            sm = self.request.GET.get(key)
            if sm is not None and sm.lower() == 'true':
                socials.append(value)

        country = self.request.GET.get('country')

        # If nothing is passed return latest 20 host profiles
        if search_term is None and len(socials) == 0 and len(ad_types) == 0 and country is None:
            return SpaceHost.objects.order_by('-user__id')[:20]
        
        # Build the query
        queryset = SpaceHost.objects.all()
        if search_term is not None:
            search_terms = search_term.split(' ')
            if len(search_terms) > 0:
                query = Q()
                # Set priority conditions
                priority_conditions = []
                for term in search_terms:
                    query |= Q(user__full_name__icontains=term)
                    # Conditions for SpaceHost
                    query |= Q(location__icontains=term) | \
                            Q(description__icontains=term)
                    # Conditions for Topic
                    query |= Q(topics__title__icontains=term)
                    # Conditions for Social Media
                    query |= Q(socials__url__icontains=term)
                
                    # Define the priorities
                    priority_conditions += [
                        When(Q(topics__title__icontains=term), then=Value(1)),
                        When(Q(user__full_name__icontains=term), then=Value(2)),
                        When(Q(socials__url__icontains=term), then=Value(3)),
                    ]

                # Combine the priority conditions for all search terms
                priority_order = Case(
                    *priority_conditions,
                    default=Value(4),
                    output_field=IntegerField()
                )

                # Now query
                queryset = SpaceHost.objects.all().filter(query).alias(priority=priority_order).order_by('priority').distinct()
        
        if len(socials) > 0:
            queryset = queryset.filter(socials__social_media__in=list(set(socials)))
        if len(ad_types) > 0:
            queryset = queryset.filter(ad_spaces__space_type__in=list(set(ad_types)))
        if country is not None:
            queryset = queryset.filter(user__country__iexact=country)
        return queryset[:20]

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)
