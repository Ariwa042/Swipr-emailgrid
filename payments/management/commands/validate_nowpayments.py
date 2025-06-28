from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json

class Command(BaseCommand):
    help = 'Test and validate NOWPayments API credentials'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='Test a specific API key',
        )
        parser.add_argument(
            '--production',
            action='store_true',
            help='Test against production endpoint instead of sandbox',
        )

    def handle(self, *args, **options):
        # Use provided API key or get from settings
        api_key = options.get('api_key') or getattr(settings, 'NOWPAYMENTS_API_KEY', 'your-api-key-here')
        use_production = options.get('production', False)
        
        # Determine endpoint
        if use_production:
            base_url = 'https://api.nowpayments.io/v1'
            env_name = "PRODUCTION"
        else:
            base_url = 'https://api-sandbox.nowpayments.io/v1'
            env_name = "SANDBOX"
        
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        self.stdout.write(f"\n🔍 Testing NOWPayments API ({env_name})")
        self.stdout.write(f"API Key: {api_key[:8]}{'*' * (len(api_key) - 8) if len(api_key) > 8 else '***'}")
        self.stdout.write(f"Endpoint: {base_url}")
        self.stdout.write("-" * 50)
        
        # Test 1: Get API status
        self.stdout.write("1. Testing API status...")
        try:
            response = requests.get(f'{base_url}/status', headers=headers, timeout=10)
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("   ✓ API status: OK"))
            else:
                self.stdout.write(self.style.ERROR(f"   ✗ API status failed: {response.status_code}"))
                self.stdout.write(f"   Response: {response.text}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ API status error: {e}"))
        
        # Test 2: Get currencies
        self.stdout.write("\n2. Testing currencies endpoint...")
        try:
            response = requests.get(f'{base_url}/currencies', headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                currencies = data.get('currencies', [])
                self.stdout.write(self.style.SUCCESS(f"   ✓ Currencies: {len(currencies)} available"))
                if currencies:
                    self.stdout.write(f"   Sample: {currencies[:5]}")
            else:
                self.stdout.write(self.style.ERROR(f"   ✗ Currencies failed: {response.status_code}"))
                self.stdout.write(f"   Response: {response.text}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Currencies error: {e}"))
        
        # Test 3: Get minimum payment amount
        self.stdout.write("\n3. Testing minimum payment amount...")
        try:
            response = requests.get(f'{base_url}/min-amount?currency_from=usd&currency_to=btc', headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                min_amount = data.get('min_amount')
                self.stdout.write(self.style.SUCCESS(f"   ✓ Min amount: {min_amount} USD"))
            else:
                self.stdout.write(self.style.ERROR(f"   ✗ Min amount failed: {response.status_code}"))
                self.stdout.write(f"   Response: {response.text}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Min amount error: {e}"))
        
        # Test 4: Create a test payment (only if previous tests pass)
        self.stdout.write("\n4. Testing payment creation...")
        test_payment_data = {
            'price_amount': 1,
            'price_currency': 'USD',
            'pay_currency': 'btc',
            'order_id': 'test-order-123',
            'order_description': 'Test payment for API validation'
        }
        
        try:
            response = requests.post(
                f'{base_url}/payment',
                headers=headers,
                data=json.dumps(test_payment_data),
                timeout=10
            )
            if response.status_code == 201:
                data = response.json()
                payment_id = data.get('payment_id')
                self.stdout.write(self.style.SUCCESS(f"   ✓ Test payment created: {payment_id}"))
            else:
                self.stdout.write(self.style.ERROR(f"   ✗ Payment creation failed: {response.status_code}"))
                self.stdout.write(f"   Response: {response.text}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Payment creation error: {e}"))
        
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("💡 TROUBLESHOOTING TIPS:")
        self.stdout.write("1. If getting 403/Invalid API Key:")
        self.stdout.write("   - Verify your API key is correct")
        self.stdout.write("   - Check if you're using sandbox key with sandbox endpoint")
        self.stdout.write("   - Make sure your NOWPayments account is active")
        
        self.stdout.write("\n2. Getting your API key:")
        self.stdout.write("   - Login to https://account.nowpayments.io/")
        self.stdout.write("   - Go to Settings > API Keys")
        self.stdout.write("   - Generate a new API key if needed")
        
        self.stdout.write("\n3. Environment setup:")
        self.stdout.write("   - Set NOWPAYMENTS_API_KEY in your .env file")
        self.stdout.write("   - Set NOWPAYMENTS_SANDBOX=True for testing")
        self.stdout.write("   - Set NOWPAYMENTS_SANDBOX=False for production")
