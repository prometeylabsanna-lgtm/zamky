"""CMS templatetags для вітрини."""

from django import template

from pages.cms_content import get_block_text, is_section_visible
from pages.i18n_lib import site_lang_code

register = template.Library()


def _norm_lang(raw) -> str:
    code = str(raw or 'ua').lower()[:2]
    if code in {'uk', 'ua'}:
        return 'ua'
    if code == 'ru':
        return 'ru'
    return 'ua'


@register.simple_tag(takes_context=True)
def cms(context, page, key, fallback=''):
    lang = context.get('cms_lang') or _norm_lang(context.get('site_lang') or site_lang_code())
    blocks = context.get('site_blocks')
    return get_block_text(
        page,
        key,
        lang=lang,
        site_blocks=blocks,
        fallback=fallback,
    )


@register.simple_tag(takes_context=True)
def cms_visible(context, page, key):
    blocks = context.get('site_blocks')
    return is_section_visible(page, key, site_blocks=blocks)
