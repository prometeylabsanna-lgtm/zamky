"""G8: cms_audit_manifest — hardcode + seed/manifest sync."""

from django.core.management.base import BaseCommand, CommandError

from pages.cms_audit import run_audit


class Command(BaseCommand):
    help = "Full-CMS hardcode/manifest audit (fail-closed на blockers)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict-warn",
            action="store_true",
            help="Також fail на warn (повний kill hardcode).",
        )

    def handle(self, *args, **options):
        report = run_audit()
        for f in report.findings:
            style = self.style.ERROR if f.severity == "blocker" else self.style.WARNING
            loc = f"{f.file}:{f.line}" if f.line else f.file
            self.stdout.write(
                style(f"[{f.severity}] {loc} — {f.message}")
                + (f" → {f.suggestion}" if f.suggestion else "")
            )
        self.stdout.write(
            f"summary: blockers={report.blockers} warns={report.warns} "
            f"parity_ok={report.parity_ok}"
        )
        fail = report.blockers > 0 or not report.parity_ok
        if options["strict_warn"] and report.warns:
            fail = True
        if fail:
            raise CommandError("CMS audit FAIL")
        self.stdout.write(self.style.SUCCESS("CMS audit PASS"))
