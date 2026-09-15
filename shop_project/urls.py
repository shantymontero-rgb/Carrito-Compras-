"""
URL configuration for shop_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from store.views import (
    catalog_view, cart_view, login_view,
    ProductListAPI, CartListCreateAPI, CartItemDetailAPI
)

schema_view = get_schema_view(
   openapi.Info(
      title="API Carrito de Compras",
      default_version='v1',
      description="Documentación interactiva de la tienda",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Vistas Web
    path('', catalog_view, name='home'),
    path('cart/', cart_view, name='cart_view'),
    path('login/', login_view, name='login_view'),

    # Tokens JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Endpoints REST
    path('api/products/', ProductListAPI.as_view(), name='api_products'),
    path('api/cart/', CartListCreateAPI.as_view(), name='api_cart'),
    path('api/cart/<int:pk>/', CartItemDetailAPI.as_view(), name='api_cart_item'),

    # Documentación Swagger
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
]