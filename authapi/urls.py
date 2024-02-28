from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='registration'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('profile/', views.UserProfileview.as_view(), name='profile'),
    path('changepassword/', views.ChangeUserPasswordView.as_view(), name='change-password'),
    path('reset-password-mail/', views.SendPasswordResetEmailView.as_view(), name='reset-password-mail'),
    path('reset-password/<uid>/<token>/', views.UserResetPasswordView.as_view(), name='reset-password'),
    path('hotels/', views.HotelView.as_view(), name='hotels'),
    path('hotels/<int:pk>/', views.SingleHotelView.as_view(), name='single-hotel'),
    path('hotels/<int:pk>/rooms', views.CustomView.as_view(), name='hotel-room-available'),
    path('hotels/<int:pk>/<int:pk2>/book', views.CustomView.as_view(), name='hotel-room-available'),
    path('hotels/<int:pk>/<int:pk2>/cancel', views.CustomView.as_view(), name='booking-cancel'),
    path('hotels/<int:pk>/rooms/bookings', views.RoomsBookingView.as_view()),
    # path('hotels/rooms/book1', views.CustomView.as_view()),
]
