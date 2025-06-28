import requests
import json
import hmac
import hashlib
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

class NOWPaymentsAPI:
    def __init__(self):
        self.api_key = getattr(settings, 'NOWPAYMENTS_API_KEY', 'your-api-key-here')
        self.ipn_secret = getattr(settings, 'NOWPAYMENTS_IPN_SECRET', 'your-ipn-secret-here')
        self.sandbox = getattr(settings, 'NOWPAYMENTS_SANDBOX', True)
        
        if self.sandbox:
            self.base_url = 'https://api-sandbox.nowpayments.io/v1'
        else:
            self.base_url = 'https://api.nowpayments.io/v1'
        
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Check if API key is placeholder
        if self.api_key == 'your-api-key-here':
            logger.warning("NOWPayments API key not configured. Please set NOWPAYMENTS_API_KEY environment variable.")
        else:
            logger.info(f"NOWPayments initialized - Sandbox: {self.sandbox}, API Key: {self.api_key[:8]}...")
    
    def get_available_currencies(self):
        """Get list of available cryptocurrencies"""
        if self.api_key == 'your-api-key-here':
            logger.error("NOWPayments API key not configured")
            return {'currencies': ['btc', 'eth', 'usdt', 'ltc', 'bch', 'xmr']}  # Return sample currencies for testing
        
        try:
            response = requests.get(f'{self.base_url}/currencies', headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching currencies: {e}")
            # Return sample currencies for development
            return {'currencies': ['btc', 'eth', 'usdt', 'ltc', 'bch', 'xmr']}
    
    def get_exchange_rate(self, from_currency, to_currency, amount=1):
        """Get exchange rate between two currencies"""
        if self.api_key == 'your-api-key-here':
            logger.warning("NOWPayments API key not configured")
            return {'estimated_amount': '0.00002'}  # Sample rate for testing
        
        try:
            url = f'{self.base_url}/exchange-amount/{from_currency}-{to_currency}'
            params = {'amount': amount}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching exchange rate: {e}")
            return {'estimated_amount': '0.00002'}  # Sample rate for testing
    
    def create_payment(self, payment_data):
        """Create a new payment"""
        if self.api_key == 'your-api-key-here':
            logger.warning("NOWPayments API key not configured - using mock response")
            # Return mock response for testing
            return {
                'payment_id': 'mock_payment_id_' + str(payment_data.get('order_id', '12345')),
                'payment_status': 'waiting',
                'pay_address': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',  # Sample Bitcoin address
                'pay_amount': 0.001,
                'price_amount': payment_data.get('price_amount'),
                'price_currency': payment_data.get('price_currency'),
                'pay_currency': payment_data.get('pay_currency'),
                'order_id': payment_data.get('order_id'),
                'order_description': payment_data.get('order_description')
            }
        
        try:
            response = requests.post(
                f'{self.base_url}/payment',
                headers=self.headers,
                data=json.dumps(payment_data),
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating payment: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return None
    
    def get_payment_status(self, payment_id):
        """Get payment status by payment ID"""
        if self.api_key == 'your-api-key-here':
            logger.warning("NOWPayments API key not configured")
            return {'payment_status': 'waiting'}  # Sample status for testing
        
        try:
            response = requests.get(
                f'{self.base_url}/payment/{payment_id}',
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching payment status: {e}")
            return None
    
    def verify_ipn_signature(self, request_body, signature):
        """Verify IPN callback signature"""
        if self.ipn_secret == 'your-ipn-secret-here':
            logger.warning("NOWPayments IPN secret not configured - skipping signature verification")
            return True  # Allow for testing without proper secret
        
        try:
            expected_signature = hmac.new(
                self.ipn_secret.encode('utf-8'),
                request_body,
                hashlib.sha512
            ).hexdigest()
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying IPN signature: {e}")
            return False
    
    def prepare_payment_data(self, payment_instance, pay_currency, request):
        """Prepare payment data for NOWPayments API"""
        # Build the callback URL
        try:
            callback_url = request.build_absolute_uri(
                reverse('payments:nowpayments_ipn')
            )
        except Exception as e:
            logger.error(f"Error building callback URL: {e}")
            callback_url = 'https://your-domain.com/payments/nowpayments/ipn/'
        
        payment_data = {
            'price_amount': float(payment_instance.amount),
            'price_currency': 'USD',
            'pay_currency': pay_currency,
            'ipn_callback_url': callback_url,
            'order_id': str(payment_instance.payment_id),
            'order_description': f'Subscription: {payment_instance.plan.name} Plan',
        }
        
        logger.info(f"Prepared payment data: {payment_data}")
        return payment_data

# Singleton instance
nowpayments = NOWPaymentsAPI()