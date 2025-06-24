from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from .models import SubscriptionPlan, Subscription, PaymentInfo, Payment
from django.contrib import messages
from .forms import PaymentForm
from django.http import JsonResponse


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
    payment_methods = PaymentInfo.objects.all()
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            
            # Create payment record
            payment = Payment.objects.create(
                user=request.user,
                plan=plan,
                payment_wallet=payment_method,
                amount=plan.price,
                status='WAITING'  # Waiting for payment
            )
            
            # Redirect to payment instructions page
            return redirect('payments:payment_instructions', payment_id=payment.payment_id)
    else:
        form = PaymentForm()
    
    return render(request, 'payments/checkout.html', {
        'plan': plan,
        'payment_methods': payment_methods,
        'form': form
    })

@login_required
def check_payment_status(request, payment_id):
    payment = get_object_or_404(Payment, payment_id=payment_id)
    if payment.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Always get the latest status from the database
    payment.refresh_from_db()
    
    # Return the current payment status
    return JsonResponse({
        'status': payment.get_status_display(),
        'completed': payment.status == 'COMPLETED'
    })

@login_required
def payment_instructions(request, payment_id):
    """
    Show cryptocurrency payment instructions to the user
    """
    payment = get_object_or_404(Payment, payment_id=payment_id, user=request.user)
    
    # Ensure payment is in waiting status
    if payment.status not in ['WAITING', 'PENDING']:
        messages.warning(request, 'This payment is no longer awaiting completion.')
        return redirect('payments:subscription_plans')
    
    # Check that payment has wallet info
    if not payment.payment_wallet:
        messages.error(request, 'Payment method information is missing.')
        return redirect('payments:checkout', plan_id=payment.plan.id)
    
    return render(request, 'payments/payment_instructions.html', {
        'payment': payment,
        'wallet': payment.payment_wallet,
        'plan': payment.plan
    })