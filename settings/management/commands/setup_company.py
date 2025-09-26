from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from settings.models import CompanySettings
import datetime

class Command(BaseCommand):
    help = 'Create initial company settings'

    def handle(self, *args, **options):
        if not CompanySettings.objects.exists():
            # Create default company settings
            settings = CompanySettings.objects.create(
                organization_name="Your Organization Name",
                organization_address="Your Organization Address",
                organization_phone="",
                organization_email="contact@yourorganization.com",
                organization_website="",
                fiscal_year_start=datetime.date(datetime.date.today().year, 1, 1),
                currency="USD",
                tax_rate=Decimal('0.00')
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created company settings: {settings.organization_name}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('Company settings already exist')
            )
