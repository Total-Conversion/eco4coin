from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from backend import views as b_views

router = routers.DefaultRouter()
router.register(r'users', b_views.UserViewSet)
router.register(r'trades', b_views.TradeViewSet)
router.register(r'sell', b_views.SaleViewSet)
router.register(r'buy', b_views.PurchaseViewSet)

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('', include('pages.urls')),
    path('api/', include(router.urls)),
    path('api/app_version', b_views.application_version_view, name='application_version'),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('', include('pages.urls'))

]

urlpatterns += [
    path('django-rq/', include('django_rq.urls'))
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
] + urlpatterns
