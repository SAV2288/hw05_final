from django.urls import path
from . import views

urlpatterns = [
    # path() для страницы регистрации нового пользователя
    path("signup/", views.SignUp.as_view(), name="signup")
]