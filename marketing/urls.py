from django.urls import path

from marketing.views import feed_view, robots_txt

urlpatterns = [
    path("feeds/<slug:slug>.xml", feed_view, name="marketing_feed"),
    path("robots.txt", robots_txt, name="robots_txt"),
]
