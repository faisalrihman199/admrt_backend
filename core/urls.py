from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, PasswordResetView, PasswordResetConfirmView, UserCountView,MessageCountView,track_visitor,AdvertiserProductCountView,SpaceHostAdCountView,AddAffiliateLinkView,AddVisitView,AffiliateLinkStatsView,AffiliateLinkUpdateView,AffiliateLinkDeleteView,VisitorCountView,RecreateUserView,DashboardStatsView
router = DefaultRouter()
router.register('', UserViewSet, basename='settings')

urlpatterns = [
    path('users/reset_password/', PasswordResetView.as_view(), name='password_reset'),
    path('users/reset_password_confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('admin/accounts/',UserCountView.as_view(),name="get_created_users"),
    path('admin/messages/',MessageCountView.as_view(),name="get_created_messages"),
    path('track-visitor/',track_visitor,name="track-user"),
    path('admin/advertisers/',AdvertiserProductCountView.as_view(),name="admin_advertisers"),
    path('admin/space_host/',SpaceHostAdCountView.as_view(),name="admin_spacehosts"),
    path('addAffliate/',AddAffiliateLinkView.as_view(),name="add_affliate"),
    path('addVisit/',AddVisitView.as_view(),name="add_visit"),
    path('affliate/',AffiliateLinkStatsView.as_view(),name="affliate"),
    path('affliate/update/',AffiliateLinkUpdateView.as_view(),name="update affliate"),
    path('affliate/delete/<int:id>/', AffiliateLinkDeleteView.as_view(), name='affiliate-link-delete'),
    path('visitor/',VisitorCountView.as_view(),name="visitor"),
    path('deleteUser/',RecreateUserView.as_view(),name="delete_user"),
    path('navStats/',DashboardStatsView.as_view(),name="nav_stats"),

    path('', include(router.urls)),

]
