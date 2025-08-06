from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
from .models import SubscriptionPlan, Subscription, PaymentInfo, Payment, BankTransferInfo
from django.contrib import messages
from .forms import PaymentForm
from .nowpayments import nowpayments

logger = logging.getLogger(__name__)


# Create your views here.
@login_required
def subscription_plans(request):
    """
    Render the subscription plans page and show the user's active subscription if any.
    """
    plans = SubscriptionPlan.objects.all().order_by('price')
    current_subscription = Subscription.objects.filter(
        user=request.user,
        is_active=True,
        end_date__gt=timezone.now()
    ).first()
    return render(request, 'payments/subscription_plans.html', {
        'plans': plans,
        'current_subscription': current_subscription
    })

# Subscribe to plan view
@login_required
def subscribe_to_plan(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    # Redirect to the payment page with the plan_id
    return redirect('payments:payment', plan_id=plan.id)

# Payment View
@login_required
def payment(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    # Get available payment methods
    # Get available cryptocurrencies from NOWPayments
    currencies_data = nowpayments.get_available_currencies()
    available_currencies = currencies_data.get('currencies', []) if currencies_data else []
    # Sort currencies alphabetically
    available_currencies = sorted(available_currencies)
    
    # Define popular cryptocurrencies and filter only those available
    popular_crypto_list = ['btc', 'eth','sol', 'usdttrc20', 'ada','matic']
    popular_currencies = [crypto for crypto in popular_crypto_list if crypto in available_currencies]
    
    # Get active bank transfer options
    bank_transfer_options = BankTransferInfo.objects.filter(is_active=True)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        if not payment_method:
            messages.error(request, 'Please select a payment method.')
            return render(request, 'payments/payment_instructions.html', {
                'plan': plan,
                'available_currencies': available_currencies,
                'popular_currencies': popular_currencies,
                'bank_transfer_options': bank_transfer_options,
            })
        
        if payment_method == 'crypto':
            pay_currency = request.POST.get('pay_currency')
            
            if not pay_currency:
                messages.error(request, 'Please select a cryptocurrency.')
                return render(request, 'payments/payment_instructions.html', {
                    'plan': plan,
                    'available_currencies': available_currencies,
                    'popular_currencies': popular_currencies,
                    'bank_transfer_options': bank_transfer_options,
                })
            
            # Allow hardcoded currencies for development/testing
            allowed_currencies = ['btc', 'eth', 'sol', 'usdttrc20', 'ada', 'matic']
            if pay_currency not in allowed_currencies and pay_currency not in available_currencies:
                messages.error(request, 'Please select a valid cryptocurrency.')
                return render(request, 'payments/payment_instructions.html', {
                    'plan': plan,
                    'available_currencies': available_currencies,
                    'popular_currencies': popular_currencies,
                    'bank_transfer_options': bank_transfer_options,
                })
            
            # Create crypto payment record
            payment = Payment.objects.create(
                user=request.user,
                plan=plan,
                amount=plan.price,
                price_amount=plan.price,
                price_currency='USD',
                pay_currency=pay_currency,
                payment_method='crypto',
                status='waiting',
                order_id=None,  # Will be set to payment_id
                order_description=f'Subscription: {plan.name} Plan'
            )
            
            # Update order_id to payment_id
            payment.order_id = str(payment.payment_id)
            payment.save()
            
            # Prepare payment data for NOWPayments
            payment_data = nowpayments.prepare_payment_data(payment, pay_currency, request)
            
            # Create payment with NOWPayments
            nowpayments_response = nowpayments.create_payment(payment_data)
            
            if nowpayments_response:
                # Update payment with NOWPayments data
                payment.nowpayments_id = str(nowpayments_response.get('payment_id'))
                payment.pay_address = nowpayments_response.get('pay_address')
                payment.pay_amount = nowpayments_response.get('pay_amount')
                payment.status = nowpayments_response.get('payment_status', 'waiting')
                payment.ipn_callback_url = payment_data.get('ipn_callback_url')
                payment.save()
                
                # Redirect to payment instructions page
                return redirect('payments:payment_instructions', payment_id=payment.payment_id)
            else:
                messages.error(request, 'Failed to create payment. Please try again.')
                payment.delete()
                
        elif payment_method == 'bank_transfer':
            bank_info_id = request.POST.get('bank_info_id')
            
            if not bank_info_id:
                messages.error(request, 'Please select a bank transfer option.')
                return render(request, 'payments/payment_instructions.html', {
                    'plan': plan,
                    'available_currencies': available_currencies,
                    'popular_currencies': popular_currencies,
                    'bank_transfer_options': bank_transfer_options,
                })
            
            bank_info = get_object_or_404(BankTransferInfo, id=bank_info_id, is_active=True)
            
            # Create bank transfer payment record
            payment = Payment.objects.create(
                user=request.user,
                plan=plan,
                amount=plan.price,
                payment_method='bank_transfer',
                bank_transfer_info=bank_info,
                status='waiting',
                order_description=f'Subscription: {plan.name} Plan'
            )
            
            # Redirect to bank transfer instructions
            return redirect('payments:bank_transfer_instructions', payment_id=payment.payment_id)
        
        else:
            messages.error(request, 'Invalid payment method selected.')
            return render(request, 'payments/payment_instructions.html', {
                'plan': plan,
                'available_currencies': available_currencies,
                'popular_currencies': popular_currencies,
                'bank_transfer_options': bank_transfer_options,
            })
    
    return render(request, 'payments/payment_instructions.html', {
        'plan': plan,
        'available_currencies': available_currencies,
        'popular_currencies': popular_currencies,
        'bank_transfer_options': bank_transfer_options,
    })

@login_required
def check_payment_status(request, payment_id):
    payment = get_object_or_404(Payment, payment_id=payment_id)
    if payment.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Check with NOWPayments API for latest status
    if payment.nowpayments_id:
        nowpayments_status = nowpayments.get_payment_status(payment.nowpayments_id)
        if nowpayments_status:
            old_status = payment.status
            payment.status = nowpayments_status.get('payment_status', payment.status)
            payment.outcome_amount = nowpayments_status.get('outcome_amount')
            payment.outcome_currency = nowpayments_status.get('outcome_currency')
            payment.save()
            
            logger.info(f"Payment {payment_id} status updated from {old_status} to {payment.status}")
    
    # Always get the latest status from the database
    payment.refresh_from_db()
    
    # Return the current payment status
    return JsonResponse({
        'status': payment.get_status_display(),
        'completed': payment.status == 'finished',
        'pay_amount': str(payment.pay_amount) if payment.pay_amount else None,
        'pay_currency': payment.pay_currency,
        'pay_address': payment.pay_address,
    })

@login_required
def payment_instructions(request, payment_id):
    """
    Show cryptocurrency payment instructions to the user
    """
    payment = get_object_or_404(Payment, payment_id=payment_id, user=request.user)
    
    # Ensure payment is in waiting status
    if payment.status in ['finished', 'failed', 'expired', 'refunded']:
        messages.warning(request, 'This payment is no longer awaiting completion.')
        return redirect('payments:subscription_plans')
    
    # Check that payment has NOWPayments data
    if not payment.pay_address or not payment.pay_amount:
        messages.error(request, 'Payment information is missing.')
        return redirect('payments:payment', plan_id=payment.plan.id)
    
    return render(request, 'payments/payment_instructions.html', {
        'payment': payment,
        'plan': payment.plan
    })


@login_required
def bank_transfer_instructions(request, payment_id):
    """
    Show bank transfer payment instructions to the user
    """
    payment = get_object_or_404(Payment, payment_id=payment_id, user=request.user)
    
    # Ensure this is a bank transfer payment
    if payment.payment_method != 'bank_transfer':
        messages.error(request, 'Invalid payment method.')
        return redirect('payments:subscription_plans')
    
    # Ensure payment is in waiting status
    if payment.status in ['finished', 'failed', 'expired', 'refunded']:
        messages.warning(request, 'This payment is no longer awaiting completion.')
        return redirect('payments:subscription_plans')
    
    if request.method == 'POST':
        transfer_reference = request.POST.get('transfer_reference')
        transfer_proof = request.FILES.get('transfer_proof')
        
        if transfer_reference:
            payment.transfer_reference = transfer_reference
            payment.status = 'confirming'
            
        if transfer_proof:
            payment.transfer_proof = transfer_proof
            
        payment.save()
        messages.success(request, 'Transfer details submitted successfully. Your payment is now under review.')
        return redirect('payments:subscription_plans')
    
    return render(request, 'payments/bank_transfer_instructions.html', {
        'payment': payment,
        'plan': payment.plan,
        'bank_info': payment.bank_transfer_info
    })

# NOWPayments IPN (Instant Payment Notification) webhook
@csrf_exempt
@require_POST
def nowpayments_ipn(request):
    """Handle NOWPayments IPN callbacks"""
    try:
        # Get the signature from headers
        signature = request.META.get('HTTP_X_NOWPAYMENTS_SIG')
        
        if not signature:
            logger.warning("IPN received without signature")
            return HttpResponse(status=400)
        
        # Verify the signature
        if not nowpayments.verify_ipn_signature(request.body, signature):
            logger.warning("IPN signature verification failed")
            return HttpResponse(status=400)
        
        # Parse the payload
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in IPN payload")
            return HttpResponse(status=400)
        
        # Get payment data
        payment_id = payload.get('order_id')
        nowpayments_id = str(payload.get('payment_id'))
        payment_status = payload.get('payment_status')
        
        if not payment_id:
            logger.error("No order_id in IPN payload")
            return HttpResponse(status=400)
        
        # Find the payment
        try:
            payment = Payment.objects.get(payment_id=payment_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for order_id: {payment_id}")
            return HttpResponse(status=404)
        
        # Update payment status and data
        old_status = payment.status
        payment.nowpayments_id = nowpayments_id
        payment.status = payment_status
        payment.outcome_amount = payload.get('outcome_amount')
        payment.outcome_currency = payload.get('outcome_currency')
        payment.purchase_id = payload.get('purchase_id')
        payment.save()
        
        logger.info(f"Payment {payment_id} status updated from {old_status} to {payment_status} via IPN")
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Error processing IPN: {e}")
        return HttpResponse(status=500)


@login_required
def get_exchange_rate(request):
    """Get exchange rate for a specific currency pair"""
    from_currency = request.GET.get('from', 'USD')
    to_currency = request.GET.get('to', 'BTC')
    
    rate_data = nowpayments.get_exchange_rate(from_currency, to_currency)
    
    if rate_data:
        return JsonResponse(rate_data)
    else:
        return JsonResponse({'error': 'Failed to get exchange rate'}, status=500)


@login_required
def bank_transfer_selection(request, plan_id):
    """Handle bank transfer selection and create payment"""
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id)
        
        if request.method == 'POST':
            bank_info_id = request.POST.get('bank_info_id')
            
            if not bank_info_id:
                messages.error(request, 'Please select a bank account.')
                return redirect('payments:bank_transfer_selection', plan_id=plan_id)
            
            try:
                bank_info = BankTransferInfo.objects.get(id=bank_info_id, is_active=True)
            except BankTransferInfo.DoesNotExist:
                messages.error(request, 'Selected bank account is not available.')
                return redirect('payments:bank_transfer_selection', plan_id=plan_id)
            
            # Create payment record
            payment = Payment.objects.create(
                user=request.user,
                plan=plan,
                amount=plan.price_in_ngn if plan.price_in_ngn else plan.price,
                payment_method='bank_transfer',
                bank_info=bank_info,
                status='waiting'
            )
            
            return redirect('payments:bank_transfer_instructions', payment_id=payment.payment_id)
        
        # GET request - show bank selection page
        bank_transfer_options = BankTransferInfo.objects.filter(is_active=True)
        
        context = {
            'plan': plan,
            'bank_transfer_options': bank_transfer_options,
        }
        
        return render(request, 'payments/bank_transfer_selection.html', context)
        
    except SubscriptionPlan.DoesNotExist:
        messages.error(request, 'Selected plan not found.')
        return redirect('payments:subscription_plans')


@login_required
def bank_transfer_direct(request, plan_id):
    """Create payment directly and redirect to bank transfer instructions"""
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id)
        
        # Get the first active bank transfer info (since we're going direct)
        bank_info = BankTransferInfo.objects.filter(is_active=True).first()
        
        if not bank_info:
            messages.error(request, 'Bank transfer option is currently unavailable.')
            return redirect('payments:subscription_plans')
        
        # Create payment record directly
        payment = Payment.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price_in_ngn if plan.price_in_ngn else plan.price,
            payment_method='bank_transfer',
            bank_transfer_info=bank_info,
            status='waiting'
        )
        
        return redirect('payments:bank_transfer_instructions', payment_id=payment.payment_id)
        
    except SubscriptionPlan.DoesNotExist:
        messages.error(request, 'Selected plan not found.')
        return redirect('payments:subscription_plans')