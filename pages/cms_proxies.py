"""Proxy-моделі CMS-секцій (слоти sidebar)."""

from pages.models_cms import SiteSettings


class HomeHeroSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Банер"
        verbose_name_plural = "Головна — Банер"


class HomeAudienceSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Для кого"
        verbose_name_plural = "Головна — Для кого"


class HomeCategoriesSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Категорії"
        verbose_name_plural = "Головна — Категорії"


class HomePickerSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Підбір"
        verbose_name_plural = "Головна — Підбір"


class HomePopularSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Популярні"
        verbose_name_plural = "Головна — Популярні"


class HomeBlogSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Блог"
        verbose_name_plural = "Головна — Блог"


class HomeDistrictSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Район SEO"
        verbose_name_plural = "Головна — Район SEO"


class SiteHeaderSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Шапка"
        verbose_name_plural = "Шапка"


class SiteFooterSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Підвал"
        verbose_name_plural = "Підвал"


class AboutBodySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Про нас"
        verbose_name_plural = "Про нас"


class DeliveryBodySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Доставка і оплата"
        verbose_name_plural = "Доставка і оплата"


class WarrantyBodySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Гарантія"
        verbose_name_plural = "Гарантія"


class ReturnsBodySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Обмін та повернення"
        verbose_name_plural = "Обмін та повернення"


class InstallBodySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Установка"
        verbose_name_plural = "Установка"


class PromosBodySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Акції"
        verbose_name_plural = "Акції"


class OfferBodySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Публічна оферта"
        verbose_name_plural = "Публічна оферта"


class PrivacyBodySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Політика конфіденційності"
        verbose_name_plural = "Політика конфіденційності"


class BlogBodySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Корисне для вибору"
        verbose_name_plural = "Корисне для вибору"


class SiteInfoConsultSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Консультація (інфо)"
        verbose_name_plural = "Консультація (інфо)"


class CatalogChromeSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Каталог — оболонка"
        verbose_name_plural = "Каталог — оболонка"
