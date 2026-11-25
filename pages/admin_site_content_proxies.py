"""Реєстрація proxy CMS-секцій у Django admin."""

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from unfold.admin import ModelAdmin

from pages import cms_proxies
from pages.admin_home_categories import home_categories_section_view
from pages.admin_home_picker import (
    home_picker_doors_view,
    home_picker_filters_view,
    home_picker_style_view,
)
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
    (cms_proxies.HomePickerDoorsSettings, "home", "picker_doors"),
    (cms_proxies.HomePickerFiltersSettings, "home", "picker_filters"),
    (cms_proxies.HomePickerStyleSettings, "home", "picker_style"),
    (cms_proxies.HomePopularSettings, "home", "popular"),
    (cms_proxies.HomeBlogSettings, "home", "blog"),
    (cms_proxies.SiteHeaderSettings, "site", "header"),
    (cms_proxies.SiteFooterSettings, "site", "footer"),
    (cms_proxies.AboutBodySettings, "about", "body"),
    (cms_proxies.AboutFormSettings, "about", "form"),
    (cms_proxies.DeliveryBodySettings, "delivery", "body"),
    (cms_proxies.WarrantyBodySettings, "warranty", "body"),
    (cms_proxies.ReturnsBodySettings, "returns", "body"),
    (cms_proxies.InstallBodySettings, "install", "body"),
    (cms_proxies.PromosBodySettings, "promos", "body"),
    (cms_proxies.OfferBodySettings, "offer", "body"),
    (cms_proxies.PrivacyBodySettings, "privacy", "body"),
    (cms_proxies.BlogBodySettings, "blog", "body"),
    (cms_proxies.BlogAskSettings, "blog", "ask"),
    (cms_proxies.SiteInfoConsultSettings, "site", "infoconsult"),
    (cms_proxies.CatalogChromeSettings, "catalog", "chrome"),
)


class SiteContentSectionAdmin(SingletonModelAdminMixin, ModelAdmin):
    page_slug: str = ""
    section_slug: str = ""

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if self.page_slug == "home" and self.section_slug == "categories":
            return home_categories_section_view(request, model_admin=self)
        if self.page_slug == "home" and self.section_slug == "picker_doors":
            return home_picker_doors_view(request, model_admin=self)
        if self.page_slug == "home" and self.section_slug == "picker_filters":
            return home_picker_filters_view(request, model_admin=self)
        if self.page_slug == "home" and self.section_slug == "picker_style":
            return home_picker_style_view(request, model_admin=self)
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
