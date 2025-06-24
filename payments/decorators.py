from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from .models import Subscription
from django.contrib.auth.decorators import login_required

def subscription_required(check_usage=True, min_plan_level=None):
    """
    Decorator to restrict access to users with active subscriptions.
    
    Args:
        check_usage: If True, checks if user has reached their monthly email limit
        min_plan_level: Minimum subscription plan required (by price)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Check if user has any active subscription
            subscription = Subscription.objects.filter(
                user=user,
                is_active=True,
                end_date__gt=timezone.now()
            ).first()
            
            if not subscription or not subscription.is_valid():
                messages.error(request, 'Active subscription required for this feature.')
                return redirect('payments:subscription_plans')  # Redirect to plans page
            
            # Check if user has required plan level
            #if min_plan_level is not None:
            #    if subscription.plan.price < min_plan_level:
            #        messages.error(request, f'This feature requires a higher subscription tier.')
            #        return redirect('payments:subscription_plans')
            
            # Check monthly usage if needed
            if check_usage:
                monthly_usage = subscription.get_monthly_usage()
                if subscription.has_reached_limit():
                    messages.error(request, 
                        f'Monthly limit of {subscription.plan.max_emails} emails reached. '
                        f'Upgrade your plan for more capacity.'
                    )
                    return redirect('payments:subscription_plans')  # Redirect to plans page
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator