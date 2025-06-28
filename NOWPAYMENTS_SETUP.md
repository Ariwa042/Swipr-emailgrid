# NOWPayments Integration Setup Guide

## Prerequisites

1. **Create a NOWPayments Account**
   - Go to https://account.nowpayments.io/create-account
   - Verify your email and complete the setup

2. **Get Your API Credentials**
   - Login to your NOWPayments dashboard
   - Go to Settings > API Keys
   - Generate your API key and IPN secret

## Environment Configuration

1. **Create a .env file in your project root:**
```
# NOWPayments Configuration
NOWPAYMENTS_API_KEY=your-actual-api-key-here
NOWPAYMENTS_IPN_SECRET=your-actual-ipn-secret-here
NOWPAYMENTS_SANDBOX=True  # Set to False for production
```

2. **For production deployment, set these environment variables on your hosting platform:**
   - NOWPAYMENTS_API_KEY
   - NOWPAYMENTS_IPN_SECRET
   - NOWPAYMENTS_SANDBOX=False

## Testing

1. **Test API connection:**
```bash
python manage.py test_nowpayments
```

2. **Test payment flow:**
   - Go to your subscription plans page
   - Select a plan and proceed to checkout
   - Choose a cryptocurrency
   - Complete the payment process

## Important Notes

1. **Sandbox vs Production:**
   - Sandbox: Use for testing (fake payments)
   - Production: Use for real payments with real cryptocurrencies

2. **IPN Webhook URL:**
   - The system automatically sets the IPN callback URL
   - Make sure your domain is accessible from the internet for IPN callbacks

3. **Security:**
   - Never commit your actual API keys to version control
   - Always use environment variables for sensitive data

## Payment Statuses

NOWPayments uses the following statuses:
- PENDING: Payment created but not yet sent
- WAITING: Waiting for customer to send payment
- CONFIRMING: Payment sent, waiting for confirmations
- CONFIRMED: Payment confirmed
- SENDING: Sending to merchant
- PARTIALLY_PAID: Partial payment received
- FINISHED: Payment completed successfully
- FAILED: Payment failed
- REFUNDED: Payment refunded
- EXPIRED: Payment expired

## Troubleshooting

1. **403 Forbidden Error:**
   - Check your API key is correct
   - Make sure you're using the right API endpoint (sandbox vs production)

2. **IPN Not Working:**
   - Ensure your domain is publicly accessible
   - Check your IPN secret is correct
   - Verify the webhook URL is reachable

3. **Payment Not Updating:**
   - Check the payment status manually in NOWPayments dashboard
   - Verify IPN callbacks are being received
   - Check application logs for errors
