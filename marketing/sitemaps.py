"""Індексовані URL для /sitemap.xml. Без районів, кошика, фільтрів і noindex."""

from __future__ import annotations

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from catalog.models import Category, Product
from pages.info_cms import is_info_page_visible
from pages.models_extra import BlogPost
from pages.views import INFO_NAV


def _host_from_domain(domain: str) -> str:
    value = (domain or "").strip().rstrip("/")
    if value.startswith("https://"):
        return value[len("https://") :]
    if value.startswith("http://"):
        return value[len("http://") :]
    return value


class DomainSitemap(Sitemap):
    protocol = "https"
    i18n = True
    alternates = True
    x_default = True

    def get_domain(self, site=None):
        from marketing.models import SeoSettings

        host = _host_from_domain(SeoSettings.load().primary_domain)
        if host:
            return host
        if site is not None:
            return site.domain
        return super().get_domain(site)

    def get_urls(self, page=1, site=None, protocol=None):
        urls = super().get_urls(page=page, site=site, protocol=protocol)
        for url in urls:
            for alt in url.get("alternates") or []:
                if alt.get("lang_code") == "ua":
                    alt["lang_code"] = "uk"
        return urls


class HomeSitemap(DomainSitemap):
    changefreq = "weekly"
    priority = 1.0

    def items(self):
        return ["catalog:home"]

    def location(self, item):
        return reverse(item)


class CatalogSitemap(DomainSitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ["catalog:catalog"]

    def location(self, item):
        return reverse(item)


class CategorySitemap(DomainSitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Category.objects.filter(is_active=True).order_by("sort_order", "name")


class ProductSitemap(DomainSitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Product.objects.filter(is_active=True).order_by("catalog_order", "name")

    def lastmod(self, obj):
        return obj.updated_at


class InfoSitemap(DomainSitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        out = []
        for key in INFO_NAV:
            if not is_info_page_visible(key):
                continue
            if key == "blog":
                out.append(("pages:blog_list", {}))
            else:
                out.append(("pages:info_page", {"page": key}))
        return out

    def location(self, item):
        name, kwargs = item
        return reverse(name, kwargs=kwargs)


class BlogSitemap(DomainSitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return BlogPost.objects.filter(is_published=True).order_by("sort_order", "-created_at")

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {
    "home": HomeSitemap,
    "catalog": CatalogSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
    "info": InfoSitemap,
    "blog": BlogSitemap,
}
