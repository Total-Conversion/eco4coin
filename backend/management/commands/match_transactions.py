from django.core.management.base import BaseCommand, CommandError
from ..transaction_matching import match

class Command(BaseCommand):
    help = 'Matches sale and purchase orders'
    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        print("Dopasowywanie zakupów")
        match()
        self.stdout.write(self.style.SUCCESS('Matching transactions completed'))