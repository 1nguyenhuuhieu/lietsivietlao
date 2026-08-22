from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("danh-sach-liet-si/", views.martyr_list, name="martyr_list"),
    path("api/goi-y/", views.suggestions, name="suggestions"),
    path("quan-tri/thay-anh-trang-chu/", views.replace_home_image, name="replace_home_image"),
    path("liet-si/<int:source_id>/", views.detail, name="detail"),
    path("gioi-thieu/", views.about, name="about"),
    path("trai-nghiem-360/", views.tour, name="tour"),
    path("trai-nghiem-360/anh-tong-quan/", views.tour_overview_image, name="tour_overview_image"),
    path("trai-nghiem-360/khu-mo/<str:zone>/", views.tour_zone_map, name="tour_zone_map"),
    path("quan-tri/trai-nghiem-360/", views.tour_manager, name="tour_manager"),
    path("health/", views.health, name="health"),
    path("robots.txt", views.robots, name="robots"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
]
