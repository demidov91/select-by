from django.core.management.base import BaseCommand


from exchange.utils import RatesLoader


class Command(BaseCommand):
    help = 'Loads last rates form http://select.by'

    def handle(self, *args, **options):
        if RatesLoader().load():
            self.stdout.write("Rates have been updated")
        else:
            self.stdout.write("Rates haven't changed")

