from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='test-main-page'),
    path('main-page/<slug:coin_name>', views.index, name='coin-main-page'),
    path('offer-detail/<int:pk>/', views.OfferView.as_view(), name='offer-detail'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('register/', views.RegisterUser.as_view(), name='register'),
    path('account/', views.account_page, name='account'),
]
