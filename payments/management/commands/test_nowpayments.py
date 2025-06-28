from django.core.management.base import BaseCommand
from payments.nowpayments import nowpayments

class Command(BaseCommand):
    help = 'Test NOWPayments API connection'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing NOWPayments API connection...'))
        
        # Test getting available currencies
        currencies = nowpayments.get_available_currencies()
        if currencies:
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully connected to NOWPayments API'))
            self.stdout.write(f'Available currencies: {len(currencies.get("currencies", []))}')
            if currencies.get('currencies'):
                self.stdout.write(f'Sample currencies: {currencies["currencies"][:10]}')
        else:
            self.stdout.write(self.style.ERROR('✗ Failed to connect to NOWPayments API'))
            self.stdout.write('Please check your API key and network connection')
        
        # Test exchange rate
        rate = nowpayments.get_exchange_rate('USD', 'BTC')
        if rate:
            self.stdout.write(self.style.SUCCESS(f'✓ Exchange rate test successful'))
            self.stdout.write(f'1 USD = {rate.get("estimated_amount", "N/A")} BTC')
        else:
            self.stdout.write(self.style.WARNING('⚠ Exchange rate test failed'))
