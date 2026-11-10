"""Реєстрація proxy CMS-секцій у Django admin."""

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from unfold.admin import ModelAdmin

from pages import cms_proxies
from pages.admin_site_content import site_content_section_view
from pages.models_cms import SiteSettings


class SingletonModelAdminMixin:
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return redirect(
            reverse(
                f"admin:{obj._meta.app_label}_{self.model._meta.model_name}_change",
                args=[obj.pk],
            )
        )


_SECTION_MODELS = (
    (cms_proxies.HomeHeroSettings, "home", "hero"),
    (cms_proxies.HomeAudienceSettings, "home", "audience"),
    (cms_proxies.HomeCategoriesSettings, "home", "categories"),
    (cms_proxies.HomePickerSettings, "home", "picker"),
    (cms_proxies.HomePopularSettings, "home", "popular"),
    (cms_proxies.HomeBlogSettings, "home", "blog"),
    (cms_proxies.HomeDistrictSettings, "home", "district"),
    (cms_proxies.SiteHeaderSettings, "site", "header"),
    (cms_proxies.SiteFooterSettings, "site", "footer"),
    (cms_proxies.AboutBodySettings, "about", "body"),
    (cms_proxies.DeliveryBodySettings, "delivery", "body"),
    (cms_proxies.WarrantyBodySettings, "warranty", "body"),
    (cms_proxies.ReturnsBodySettings, "returns", "body"),
    (cms_proxies.InstallBodySettings, "install", "body"),
    (cms_proxies.PromosBodySettings, "promos", "body"),
    (cms_proxies.OfferBodySettings, "offer", "body"),
    (cms_proxies.PrivacyBodySettings, "privacy", "body"),
    (cms_proxies.BlogBodySettings, "blog", "body"),
    (cms_proxies.SiteInfoConsultSettings, "site", "infoconsult"),
    (cms_proxies.CatalogChromeSettings, "catalog", "chrome"),
)


class SiteContentSectionAdmin(SingletonModelAdminMixin, ModelAdmin):
    page_slug: str = ""
    section_slug: str = ""

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return site_content_section_view(
            request,
            self.page_slug,
            self.section_slug,
            model_admin=self,
        )


def register_site_content_section_admins(site=None):
    admin_site = site or admin.site
    for model, page_slug, section_slug in _SECTION_MODELS:
        if admin_site.is_registered(model):
            continue
        admin_class = type(
            f"{model.__name__}Admin",
            (SiteContentSectionAdmin,),
            {"page_slug": page_slug, "section_slug": section_slug},
        )
        admin_site.register(model, admin_class)
