from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from marketing import seo as seo_lib
from marketing.consent import allows_pixels

register = template.Library()


class SeoTitleNode(template.Node):
    child_nodelists = ("nodelist",)

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        page_title = self.nodelist.render(context)
        request = context.get("request")
        lang = seo_lib.current_lang()
        seo = seo_lib.get_seo(request)
        over = seo_lib.page_overrides(context, lang)
        title = seo_lib.compose_title(page_title, seo, lang, over["title"])
        context.render_context["marketing_title"] = title
        return title


@register.tag(name="seo_title")
def seo_title(parser, token):
    nodelist = parser.parse(("endseo_title",))
    parser.delete_first_token()
    return SeoTitleNode(nodelist)


def _render_if(template_name: str, ctx: dict, has_output: bool) -> str:
    # Нічого не налаштовано → порожній рядок, HTML сайту байт-у-байт як до зміни.
    if not has_output:
        return ""
    return mark_safe("\n  " + render_to_string(template_name, ctx).strip())


@register.simple_tag(takes_context=True)
def seo_head(context):
    head = seo_lib.build_head(context)
    has = bool(
        head["noindex"] or head["description"] or head["verifications"]
        or head["canonical"] or head["og"] or head["jsonld"]
    )
    return _render_if("marketing/seo_head.html", {"head": head}, has)


def _tracking_ctx(context):
    tracking = seo_lib.get_tracking(context.get("request"))
    if tracking is None:
        return {"ga4": "", "gtm": "", "ads": "", "meta": "", "tiktok": ""}
    return {
        "ga4": tracking.active("ga4_enabled", "ga4_id"),
        "gtm": tracking.active("gtm_enabled", "gtm_id"),
        "ads": tracking.active("google_ads_enabled", "google_ads_id"),
        "meta": tracking.active("meta_pixel_enabled", "meta_pixel_id"),
        "tiktok": tracking.active("tiktok_enabled", "tiktok_pixel_id"),
    }


@register.simple_tag(takes_context=True)
def tracking_head(context):
    ctx = _tracking_ctx(context)
    ctx["allow_pixels"] = allows_pixels(context.get("request"))
    return mark_safe("\n  " + render_to_string("marketing/tracking_head.html", ctx).strip())


@register.simple_tag(takes_context=True)
def tracking_body(context):
    if not allows_pixels(context.get("request")):
        return ""
    ctx = _tracking_ctx(context)
    return _render_if("marketing/tracking_body.html", ctx, bool(ctx["gtm"] or ctx["meta"]))
