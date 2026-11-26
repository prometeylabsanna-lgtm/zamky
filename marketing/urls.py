from django.contrib.sitemaps.views import sitemap
from django.urls import path

from marketing.sitemaps import SITEMAPS
from marketing.views import feed_view, llms_txt, robots_txt

urlpatterns = [
    path("feeds/<slug:slug>.xml", feed_view, name="marketing_feed"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("llms.txt", llms_txt, name="llms_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
]
