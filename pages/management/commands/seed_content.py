"""Alias playbook G7: seed_content → seed_cms_content."""

from pages.management.commands.seed_cms_content import Command as SeedCmsCommand


class Command(SeedCmsCommand):
    help = "G7 alias: ідемпотентний seed CMS (seed_cms_content)."
