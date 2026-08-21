from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("liet-si/<int:source_id>/", views.detail, name="detail"),
    path("trai-nghiem-360/", views.tour, name="tour"),
    path("health/", views.health, name="health"),
]

