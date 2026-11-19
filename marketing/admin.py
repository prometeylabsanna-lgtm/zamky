"""Адмінка розділу «Маркетинг»: фіди, SEO-налаштування, пікселі."""

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action

from marketing import seo as seo_lib
from marketing.feeds import get_feed_payload, resolve_base_url
from marketing.models import FeedCategoryMapping, ProductFeed, SeoSettings, TrackingSettings

REASON_LABELS = {
    "price_not_positive": "ціна ≤ 0",
    "below_purchase_price": "ціна нижча за закупівлю",
    "inactive_category": "неактивна категорія",
    "no_image": "без фото",
    "no_link": "без посилання",
}


class SingletonAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.load()
        opts = self.model._meta
        return redirect(reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[obj.pk]))


class FeedCategoryMappingInline(TabularInline):
    model = FeedCategoryMapping
    extra = 0
    autocomplete_fields = ()
    fields = ("category", "google_product_category")
    verbose_name = "Мапінг категорії → Google product category"
    verbose_name_plural = "Мапінг категорій → Google product category (необовʼязково)"


@admin.register(ProductFeed)
class ProductFeedAdmin(ModelAdmin):
    list_display = ("name", "feed_type", "is_enabled", "public_url", "last_included", "excluded_display", "last_generated_at")
    list_filter = ("feed_type", "is_enabled")
    search_fields = ("name", "slug")
    filter_horizontal = ("categories",)
    inlines = (FeedCategoryMappingInline,)
    actions = ("regenerate",)
    readonly_fields = (
        "public_url",
        "stats",
        "enabled_changed_at",
        "enabled_changed_by",
        "last_generated_at",
    )
    fieldsets = (
        ("Фід", {"fields": ("name", "feed_type", "is_enabled", "public_url", "slug", "access_token")}),
        ("Магазин", {"fields": ("shop_name", "company_name", "currency")}),
        ("Склад фіду", {"fields": ("only_in_stock", "categories", "cache_hours")}),
        (
            "Статистика та журнал",
            {"fields": ("stats", "last_generated_at", "enabled_changed_at", "enabled_changed_by")},
        ),
    )

    @admin.display(description="Публічний URL")
    def public_url(self, obj):
        if not obj or not obj.pk:
            return "—"
        path = obj.public_path + ("?token=…" if obj.access_token else "")
        state = "" if obj.is_enabled else " (вимкнено → 404)"
        return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>{}', obj.public_path, path, state)

    @admin.display(description="Виключено")
    def excluded_display(self, obj):
        return obj.last_excluded

    @admin.display(description="Статистика останньої генерації")
    def stats(self, obj):
        if not obj or not obj.last_generated_at:
            return "Ще не генерувався. Відкрийте URL фіду або дію «Перегенерувати»."
        rows = sorted((obj.last_excluded_reasons or {}).items())
        reasons = format_html_join(
            "", "<li>{}: {}</li>", ((REASON_LABELS.get(k, k), n) for k, n in rows)
        )
        return format_html(
            "<p>У фіді: <b>{}</b>, виключено: <b>{}</b></p><ul>{}</ul>",
            obj.last_included,
            obj.last_excluded,
            reasons,
        )

    def save_model(self, request, obj, form, change):
        if not change or "is_enabled" in form.changed_data:
            obj.enabled_changed_at = timezone.now()
            obj.enabled_changed_by = request.user
        super().save_model(request, obj, form, change)

    @action(description="Перегенерувати фід (скинути кеш)")
    def regenerate(self, request, queryset):
        base = resolve_base_url(request)
        for feed in queryset:
            payload = get_feed_payload(feed, base, force=True)
            self.message_user(
                request,
                f"{feed.name}: у фіді {payload.included}, виключено {payload.excluded}.",
                messages.SUCCESS,
            )


COUNTER_MEDIA_JS = ("js/admin/seo_counter.js",)


@admin.register(SeoSettings)
class SeoSettingsAdmin(SingletonAdmin):
    readonly_fields = ("noindex_warning", "og_preview")
    fieldsets = (
        (
            "Індексація",
            {
                "fields": ("noindex_warning", "global_noindex", "robots_extra"),
                "description": "robots.txt генерується автоматично: Disallow: /admin/ і Sitemap (коли sitemap є). Ваші рядки додаються після них.",
            },
        ),
        ("Домен і canonical", {"fields": ("primary_domain",)}),
        (
            "Title і description за замовчуванням",
            {
                "fields": (
                    "title_default",
                    "title_default_ru",
                    "title_suffix",
                    "description_default",
                    "description_default_ru",
                )
            },
        ),
        ("Open Graph / X (Twitter)", {"fields": ("og_preview", "og_image", "og_image_alt", "twitter_card", "twitter_site")}),
        (
            "Коди підтвердження (лише значення content)",
            {
                "fields": (
                    "google_verification",
                    "bing_verification",
                    "meta_domain_verification",
                    "pinterest_verification",
                )
            },
        ),
        (
            "Організація (JSON-LD на головній)",
            {
                "fields": ("org_type", "org_name", "org_logo", "same_as"),
                "description": "Телефон, email, адреса та соцмережі беруться з «Налаштування → Контакти». Порожнє поле не виводиться.",
            },
        ),
    )

    class Media:
        js = COUNTER_MEDIA_JS

    @admin.display(description="Увага")
    def noindex_warning(self, obj):
        style = "padding:12px 16px;border-radius:8px;font-weight:700;font-size:15px;"
        if obj and obj.global_noindex:
            return format_html(
                '<div style="{}background:#b91c1c;color:#fff">⚠ ЗАРАЗ УВЕСЬ САЙТ ЗАКРИТО ВІД ІНДЕКСАЦІЇ (noindex). Google прибере всі сторінки з пошуку.</div>',
                style,
            )
        return format_html(
            '<div style="{}background:#fef3c7;color:#92400e">Галочка нижче закриває ВЕСЬ сайт від Google. Вмикайте лише для staging/демо.</div>',
            style,
        )

    @admin.display(description="Превʼю OG")
    def og_preview(self, obj):
        if obj and obj.og_image:
            try:
                return format_html('<img src="{}" alt="" style="max-width:300px;border-radius:6px">', obj.og_image.url)
            except Exception:
                return "—"
        return "—"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        for title in (obj.title_default, obj.title_default_ru):
            if title:
                warn = seo_lib.title_length_warning(title, obj.title_suffix)
                if warn:
                    messages.warning(request, warn)
        for desc in (obj.description_default, obj.description_default_ru):
            warn = seo_lib.description_length_warning(desc)
            if warn:
                messages.warning(request, warn)
        if obj.og_image:
            try:
                w, h = obj.og_image.width, obj.og_image.height
                if (w, h) != (1200, 630):
                    messages.warning(request, f"OG-картинка {w}×{h}, рекомендовано 1200×630.")
            except Exception:
                pass
        if obj.global_noindex:
            messages.error(request, "Увімкнено глобальний noindex: весь сайт закрито від індексації.")


@admin.register(TrackingSettings)
class TrackingSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ("Google Analytics 4", {"fields": ("ga4_enabled", "ga4_id")}),
        ("Google Tag Manager", {"fields": ("gtm_enabled", "gtm_id")}),
        ("Google Ads", {"fields": ("google_ads_enabled", "google_ads_id")}),
        ("Meta (Facebook) Pixel", {"fields": ("meta_pixel_enabled", "meta_pixel_id")}),
        ("TikTok Pixel", {"fields": ("tiktok_enabled", "tiktok_pixel_id")}),
    )

    def get_fieldsets(self, request, obj=None):
        fs = list(super().get_fieldsets(request, obj))
        fs[0] = (
            fs[0][0],
            {
                **fs[0][1],
                "description": "Вводиться лише ID; код лічильника фіксований у шаблоні. Лічильник працює, коли увімкнено І вказано ID.",
            },
        )
        return fs
