# Email Provider Alternatives for Household Invitation System

Since SendGrid no longer offers a free tier (only a 60-day trial), here are alternative email API services suitable for transactional invitation emails.

> **⚠️ Future Multi-Channel Considerations**: If you plan to add SMS/WhatsApp features later, consider providers that offer unified platforms (email + SMS/WhatsApp) to avoid managing multiple services. See the [Multi-Channel Considerations](#multi-channel-considerations-smswhatsapp) section below.

## Comparison Summary

| Provider | Free Tier | Paid Starting | SMS/WhatsApp | Best For | Integration Complexity |
|----------|-----------|---------------|--------------|----------|------------------------|
| **Resend** | 3,000 emails/month | $20/month (50k) | ❌ No | Modern dev-friendly | ⭐ Very Easy |
| **Mailgun** | 100 emails/day | $15/month (10k) | ❌ No | Reliability | ⭐⭐ Easy |
| **Brevo** | 300 emails/day | $9/month (5k) | ✅ SMS included | Budget-friendly + multi-channel | ⭐⭐ Easy |
| **Twilio** | $15.50 credit | Pay-as-you-go | ✅ SMS + WhatsApp | Unified platform | ⭐⭐ Easy |
| **AWS SES** | 62k/month (from EC2) | $0.10/1k emails | ✅ SNS (SMS) | High volume + AWS ecosystem | ⭐⭐⭐ Moderate |
| **MailerSend** | 12,000/month | $28/month (50k) | ❌ No | Balance | ⭐⭐ Easy |

---

## 1. Resend ⭐ **RECOMMENDED**

**Modern, developer-first email API with excellent DX.**

### Pricing
- **Free Tier**: 3,000 emails/month, 100 emails/day
- **Pro**: $20/month for 50,000 emails
- **Pay-as-you-go**: $0.30 per 1,000 emails after limit

### Pros
- ✅ **Excellent developer experience** - clean API, great docs
- ✅ **Generous free tier** (3k/month) - perfect for development/testing
- ✅ **Fast setup** - no domain verification needed for free tier
- ✅ **Modern stack** - built for developers, not marketers
- ✅ **Simple integration** - REST API with `httpx` (already in your stack)
- ✅ **Good deliverability** - focused on transactional emails
- ✅ **No branding** on free tier

### Cons
- ❌ Newer service (founded 2021) - less established than competitors
- ❌ Smaller community/resources compared to Mailgun/SendGrid
- ❌ Limited to transactional emails (no marketing features)
- ❌ **No SMS/WhatsApp support** - would need separate provider for multi-channel

### Integration Steps

1. **Sign up**: https://resend.com (free account)

2. **Get API key**: Dashboard → API Keys → Create

3. **Update config** (`app/core/config.py`):
   ```python
   EMAIL_PROVIDER: str = "resend"  # console | resend | mailgun | brevo | aws_ses
   EMAIL_FROM: str = "onboarding@resend.dev"  # or your verified domain
   RESEND_API_KEY: str | None = None
   ```

4. **Add to requirements** (if needed):
   - Already have `httpx` ✅

5. **Implement client** (`app/services/email.py`):
   ```python
   @dataclass(frozen=True)
   class ResendEmailClient:
       """Resend email client using Resend API."""

       api_key: str
       from_email: str = settings.EMAIL_FROM

       def send_invitation(
           self,
           *,
           to_email: str,
           inviter_email: str,
           household_name: str,
           accept_url: str,
       ) -> None:
           subject = f"You've been invited to join {household_name}"
           text = (
               f"{inviter_email} invited you to join '{household_name}'.\n\n"
               f"Accept your invitation:\n{accept_url}\n"
           )

           payload = {
               "from": self.from_email,
               "to": to_email,
               "subject": subject,
               "text": text,
           }

           headers = {
               "Authorization": f"Bearer {self.api_key}",
               "Content-Type": "application/json",
           }

           try:
               with httpx.Client(timeout=5.0) as client:
                   resp = client.post(
                       "https://api.resend.com/emails",
                       headers=headers,
                       json=payload,
                   )
               if resp.status_code >= 300:
                   raise EmailSendError(
                       f"Resend error {resp.status_code}: {resp.text[:200]}")
           except EmailSendError:
               raise
           except Exception as e:
               raise EmailSendError(str(e)) from e
   ```

6. **Update `get_email_client()`**:
   ```python
   if provider == "resend":
       if not settings.RESEND_API_KEY:
           raise EmailSendError("RESEND_API_KEY is not configured")
       return ResendEmailClient(api_key=settings.RESEND_API_KEY)
   ```

**Integration Time**: ~15 minutes
**Documentation**: https://resend.com/docs

---

## 2. Mailgun

**Reliable, battle-tested email service with good free tier.**

### Pricing
- **Free Tier**: 100 emails/day (3,000/month)
- **Foundation**: $15/month for 10,000 emails
- **Growth**: $35/month for 50,000 emails
- **Pay-as-you-go**: $1.00 per 1,000 emails after limit

### Pros
- ✅ **Proven reliability** - used by many large companies
- ✅ **Excellent deliverability** - strong reputation
- ✅ **Comprehensive docs** - well-documented API
- ✅ **Domain verification** - improves sender reputation
- ✅ **Webhooks** - for bounce/complaint handling
- ✅ **Good free tier** for low-volume testing

### Cons
- ❌ **Daily limit** on free tier (100/day) - can be restrictive
- ❌ **Domain verification required** for production (adds setup time)
- ❌ **More complex** than Resend (more features = more complexity)

### Integration Steps

1. **Sign up**: https://www.mailgun.com

2. **Verify domain** (required for production):
   - Add DNS records (SPF, DKIM, DMARC)
   - Can use sandbox domain for testing (emails only to authorized recipients)

3. **Get API key**: Dashboard → Settings → API Keys

4. **Update config**:
   ```python
   EMAIL_PROVIDER: str = "mailgun"
   EMAIL_FROM: str = "noreply@yourdomain.com"  # verified domain
   MAILGUN_API_KEY: str | None = None
   MAILGUN_DOMAIN: str | None = None  # e.g., "mg.yourdomain.com"
   ```

5. **Implement client**:
   ```python
   @dataclass(frozen=True)
   class MailgunEmailClient:
       """Mailgun email client using Mailgun API."""

       api_key: str
       domain: str
       from_email: str = settings.EMAIL_FROM

       def send_invitation(
           self,
           *,
           to_email: str,
           inviter_email: str,
           household_name: str,
           accept_url: str,
       ) -> None:
           subject = f"You've been invited to join {household_name}"
           text = (
               f"{inviter_email} invited you to join '{household_name}'.\n\n"
               f"Accept your invitation:\n{accept_url}\n"
           )

           # Mailgun uses form-encoded data
           data = {
               "from": self.from_email,
               "to": to_email,
               "subject": subject,
               "text": text,
           }

           auth = ("api", self.api_key)

           try:
               with httpx.Client(timeout=5.0) as client:
                   resp = client.post(
                       f"https://api.mailgun.net/v3/{self.domain}/messages",
                       auth=auth,
                       data=data,
                   )
               if resp.status_code >= 300:
                   raise EmailSendError(
                       f"Mailgun error {resp.status_code}: {resp.text[:200]}")
           except EmailSendError:
               raise
           except Exception as e:
               raise EmailSendError(str(e)) from e
   ```

**Integration Time**: ~30-45 minutes (includes domain verification)
**Documentation**: https://documentation.mailgun.com

---

## 3. Brevo (formerly Sendinblue)

**Budget-friendly option with good free tier and marketing features.**

### Pricing
- **Free Tier**: 300 emails/day (9,000/month)
- **Starter**: $9/month for 5,000 emails
- **Business**: $25/month for 20,000 emails
- **Pay-as-you-go**: $0.25 per 1,000 emails after limit

### Pros
- ✅ **Best free tier** (300/day = 9k/month) - most generous
- ✅ **Very affordable** paid plans
- ✅ **Marketing + transactional** - can expand beyond invitations
- ✅ **✅ SMS support included** - unified platform for email + SMS (no separate service needed)
- ✅ **WhatsApp Business API** available (paid add-on)
- ✅ **No domain verification** needed for free tier
- ✅ **Good documentation**
- ✅ **Multi-channel ready** - perfect if you plan to add SMS/WhatsApp later

### Cons
- ❌ **Brevo branding** on free tier emails (footer)
- ❌ **Daily limit** (300/day) - can hit limit on busy days
- ❌ **More features** = more complexity (if you only need transactional)
- ❌ **Less developer-focused** than Resend
- ❌ **WhatsApp** requires paid plan (not on free tier)

### Integration Steps

1. **Sign up**: https://www.brevo.com

2. **Get API key**: SMTP & API → API Keys → Create

3. **Update config**:
   ```python
   EMAIL_PROVIDER: str = "brevo"
   EMAIL_FROM: str = "noreply@yourdomain.com"
   BREVO_API_KEY: str | None = None
   ```

4. **Implement client**:
   ```python
   @dataclass(frozen=True)
   class BrevoEmailClient:
       """Brevo email client using Brevo Transactional API."""

       api_key: str
       from_email: str = settings.EMAIL_FROM

       def send_invitation(
           self,
           *,
           to_email: str,
           inviter_email: str,
           household_name: str,
           accept_url: str,
       ) -> None:
           subject = f"You've been invited to join {household_name}"
           text = (
               f"{inviter_email} invited you to join '{household_name}'.\n\n"
               f"Accept your invitation:\n{accept_url}\n"
           )

           payload = {
               "sender": {"email": self.from_email},
               "to": [{"email": to_email}],
               "subject": subject,
               "textContent": text,
           }

           headers = {
               "api-key": self.api_key,
               "Content-Type": "application/json",
           }

           try:
               with httpx.Client(timeout=5.0) as client:
                   resp = client.post(
                       "https://api.brevo.com/v3/smtp/email",
                       headers=headers,
                       json=payload,
                   )
               if resp.status_code >= 300:
                   raise EmailSendError(
                       f"Brevo error {resp.status_code}: {resp.text[:200]}")
           except EmailSendError:
               raise
           except Exception as e:
               raise EmailSendError(str(e)) from e
   ```

**Integration Time**: ~20 minutes
**Documentation**:
- Email: https://developers.brevo.com
- SMS: https://developers.brevo.com/docs/send-sms

**SMS Integration** (when needed):
- Same API key works for SMS
- SMS pricing: ~$0.05-0.10 per SMS (varies by country)
- Free tier includes limited SMS credits
- WhatsApp Business API available on paid plans

---

## 4. Twilio (Unified Platform) ⭐ **BEST FOR MULTI-CHANNEL**

**Twilio owns SendGrid and offers unified email + SMS + WhatsApp platform.**

### Pricing
- **Free Trial**: $15.50 credit (enough for ~1,000 emails or ~150 SMS)
- **Email (SendGrid)**: $19.95/month for 50k emails (after trial)
- **SMS**: ~$0.0075-0.05 per SMS (varies by country)
- **WhatsApp**: ~$0.005-0.01 per message
- **Pay-as-you-go** model - no monthly minimums

### Pros
- ✅ **Unified platform** - email, SMS, WhatsApp from one provider
- ✅ **Industry leader** - most established CPaaS provider
- ✅ **Excellent APIs** - well-documented, developer-friendly
- ✅ **Global reach** - SMS/WhatsApp works worldwide
- ✅ **Flexible pricing** - pay only for what you use
- ✅ **SendGrid integration** - can use SendGrid email API alongside Twilio SMS/WhatsApp
- ✅ **No vendor lock-in** - can use email from one provider, SMS from another
- ✅ **Webhooks** - real-time delivery status

### Cons
- ❌ **No permanent free tier** - only trial credit
- ❌ **SendGrid email** requires paid plan (no free tier)
- ❌ **Can be expensive** at scale (SMS costs add up)
- ❌ **Two services** - Twilio for SMS/WhatsApp, SendGrid for email (same company, different APIs)
- ❌ **More complex** - managing multiple APIs (email vs SMS vs WhatsApp)

### Integration Steps

**For Email (SendGrid)**:
1. Sign up: https://sendgrid.com
2. Get API key: Settings → API Keys
3. Use SendGridEmailClient (already implemented)

**For SMS/WhatsApp (Twilio)**:
1. Sign up: https://www.twilio.com
2. Get Account SID and Auth Token
3. Install Twilio SDK: `pip install twilio`
4. Implement SMS client:
   ```python
   from twilio.rest import Client

   @dataclass(frozen=True)
   class TwilioSMSClient:
       """Twilio SMS client."""

       account_sid: str
       auth_token: str
       from_number: str  # Twilio phone number

       def send_invitation_sms(
           self,
           *,
           to_phone: str,
           inviter_name: str,
           household_name: str,
           accept_url: str,
       ) -> None:
           client = Client(self.account_sid, self.auth_token)
           message = (
               f"{inviter_name} invited you to join '{household_name}'. "
               f"Accept: {accept_url}"
           )
           try:
               client.messages.create(
                   body=message,
                   from_=self.from_number,
                   to=to_phone,
               )
           except Exception as e:
               raise EmailSendError(f"Twilio SMS error: {e}")
   ```

**Integration Time**:
- Email: Already implemented (SendGrid)
- SMS: ~30 minutes
- WhatsApp: ~1-2 hours (requires business verification)

**Documentation**:
- Email: https://docs.sendgrid.com
- SMS: https://www.twilio.com/docs/sms
- WhatsApp: https://www.twilio.com/docs/whatsapp

---

## 5. AWS SES (Simple Email Service) + AWS SNS (SMS)

**Ultra-cheap, highly scalable option for AWS users.**

### Pricing
- **Free Tier**: 62,000 emails/month (when sent from EC2/ECS/Lambda)
- **After free tier**: $0.10 per 1,000 emails
- **Dedicated IP**: $24.95/month (optional)

### Pros
- ✅ **Extremely cheap** - $0.10/1k = $10 per 100k emails
- ✅ **Massive free tier** (62k/month) if using AWS infrastructure
- ✅ **Highly scalable** - handles millions of emails
- ✅ **AWS integration** - seamless if already on AWS
- ✅ **No monthly minimums** - pay only for what you use
- ✅ **AWS SNS for SMS** - can add SMS via AWS SNS (same ecosystem)
- ✅ **Multi-channel ready** - SES + SNS + Pinpoint (WhatsApp via partners)

### Cons
- ❌ **AWS account required** - adds complexity if not using AWS
- ❌ **Sandbox mode** initially - can only send to verified emails
- ❌ **Domain verification required** - DNS setup needed
- ❌ **More complex setup** - IAM roles, policies, etc.
- ❌ **Less developer-friendly** - AWS console can be overwhelming
- ❌ **Free tier only from EC2/ECS/Lambda** - not from external servers
- ❌ **SMS via SNS** - separate service, more setup complexity
- ❌ **WhatsApp** - requires AWS Pinpoint + partner integration (complex)

### Integration Steps

1. **AWS Account**: Create at https://aws.amazon.com

2. **Verify domain**:
   - SES Console → Verified identities → Create
   - Add DNS records (SPF, DKIM)

3. **Request production access** (move out of sandbox):
   - SES Console → Account dashboard → Request production access

4. **Create IAM user** with SES permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": ["ses:SendEmail", "ses:SendRawEmail"],
       "Resource": "*"
     }]
   }
   ```

5. **Get access keys**: IAM → Users → Security credentials

6. **Install boto3** (if not already):
   ```bash
   pip install boto3
   ```

7. **Update config**:
   ```python
   EMAIL_PROVIDER: str = "aws_ses"
   EMAIL_FROM: str = "noreply@yourdomain.com"  # verified domain
   AWS_ACCESS_KEY_ID: str | None = None
   AWS_SECRET_ACCESS_KEY: str | None = None
   AWS_REGION: str = "us-east-1"  # or your preferred region
   ```

8. **Implement client**:
   ```python
   import boto3
   from botocore.exceptions import ClientError

   @dataclass(frozen=True)
   class AWSSESEmailClient:
       """AWS SES email client."""

       access_key: str
       secret_key: str
       region: str
       from_email: str = settings.EMAIL_FROM

       def send_invitation(
           self,
           *,
           to_email: str,
           inviter_email: str,
           household_name: str,
           accept_url: str,
       ) -> None:
           subject = f"You've been invited to join {household_name}"
           text = (
               f"{inviter_email} invited you to join '{household_name}'.\n\n"
               f"Accept your invitation:\n{accept_url}\n"
           )

           client = boto3.client(
               'ses',
               aws_access_key_id=self.access_key,
               aws_secret_access_key=self.secret_key,
               region_name=self.region,
           )

           try:
               response = client.send_email(
                   Source=self.from_email,
                   Destination={'ToAddresses': [to_email]},
                   Message={
                       'Subject': {'Data': subject},
                       'Body': {'Text': {'Data': text}},
                   },
               )
           except ClientError as e:
               raise EmailSendError(f"AWS SES error: {e}")
           except Exception as e:
               raise EmailSendError(str(e)) from e
   ```

**Integration Time**: ~1-2 hours (includes AWS setup, domain verification, sandbox exit)
**Documentation**:
- Email: https://docs.aws.amazon.com/ses
- SMS: https://docs.aws.amazon.com/sns (Simple Notification Service)
- WhatsApp: https://docs.aws.amazon.com/pinpoint (via partners)

**SMS Integration** (when needed):
- Use AWS SNS (Simple Notification Service)
- SMS pricing: ~$0.00645 per SMS (US), varies by country
- Requires separate SNS setup and phone number verification
- WhatsApp available via AWS Pinpoint + partner integration (complex)

---

## 6. MailerSend

**Balanced option with good free tier and developer-friendly API.**

### Pricing
- **Free Tier**: 12,000 emails/month
- **Premium**: $28/month for 50,000 emails
- **Pay-as-you-go**: $0.20 per 1,000 emails after limit

### Pros
- ✅ **Good free tier** (12k/month) - more than Mailgun
- ✅ **Developer-friendly** - clean REST API
- ✅ **Visual email builder** - for non-technical users
- ✅ **Webhooks** - for bounce/complaint handling
- ✅ **No daily limits** on free tier (unlike Mailgun/Brevo)

### Cons
- ❌ **Higher paid pricing** than competitors
- ❌ **Less established** than Mailgun/SendGrid
- ❌ **Domain verification** recommended for production
- ❌ **No SMS/WhatsApp support** - would need separate provider for multi-channel

### Integration Steps

1. **Sign up**: https://www.mailersend.com

2. **Verify domain** (optional for free tier, recommended for production)

3. **Get API token**: Settings → API Tokens → Generate

4. **Update config**:
   ```python
   EMAIL_PROVIDER: str = "mailersend"
   EMAIL_FROM: str = "noreply@yourdomain.com"
   MAILERSEND_API_TOKEN: str | None = None
   ```

5. **Implement client**:
   ```python
   @dataclass(frozen=True)
   class MailerSendEmailClient:
       """MailerSend email client using MailerSend API."""

       api_token: str
       from_email: str = settings.EMAIL_FROM

       def send_invitation(
           self,
           *,
           to_email: str,
           inviter_email: str,
           household_name: str,
           accept_url: str,
       ) -> None:
           subject = f"You've been invited to join {household_name}"
           text = (
               f"{inviter_email} invited you to join '{household_name}'.\n\n"
               f"Accept your invitation:\n{accept_url}\n"
           )

           payload = {
               "from": {"email": self.from_email},
               "to": [{"email": to_email}],
               "subject": subject,
               "text": text,
           }

           headers = {
               "Authorization": f"Bearer {self.api_token}",
               "Content-Type": "application/json",
           }

           try:
               with httpx.Client(timeout=5.0) as client:
                   resp = client.post(
                       "https://api.mailersend.com/v1/email",
                       headers=headers,
                       json=payload,
                   )
               if resp.status_code >= 300:
                   raise EmailSendError(
                       f"MailerSend error {resp.status_code}: {resp.text[:200]}")
           except EmailSendError:
               raise
           except Exception as e:
               raise EmailSendError(str(e)) from e
   ```

**Integration Time**: ~25 minutes
**Documentation**: https://developers.mailersend.com

---

## Multi-Channel Considerations (SMS/WhatsApp)

If you plan to add SMS/WhatsApp features in the future, here are key considerations:

### Unified Platform vs Separate Providers

**Option 1: Unified Platform** (Recommended for simplicity)
- ✅ Single API key/credentials
- ✅ Unified billing and dashboard
- ✅ Easier to manage
- ✅ Consistent error handling
- **Best Options**: Brevo, Twilio

**Option 2: Separate Providers**
- ✅ Best-of-breed for each channel
- ✅ More flexibility to switch providers
- ❌ Multiple API keys/credentials
- ❌ Separate billing
- ❌ More complex error handling
- **Example**: Resend (email) + Twilio (SMS/WhatsApp)

### Multi-Channel Provider Comparison

| Provider | Email | SMS | WhatsApp | Unified API | Best For |
|----------|-------|-----|----------|-------------|----------|
| **Brevo** | ✅ Free tier | ✅ Included | ✅ Paid add-on | ✅ Yes | Budget + multi-channel |
| **Twilio** | ✅ (SendGrid) | ✅ Yes | ✅ Yes | ⚠️ Separate APIs | Enterprise multi-channel |
| **AWS** | ✅ SES | ✅ SNS | ⚠️ Pinpoint | ⚠️ Separate services | AWS ecosystem |
| **Resend** | ✅ Yes | ❌ No | ❌ No | N/A | Email-only |
| **Mailgun** | ✅ Yes | ❌ No | ❌ No | N/A | Email-only |

### SMS/WhatsApp Pricing Considerations

- **SMS costs**: Typically $0.005-0.10 per message (varies by country)
- **WhatsApp costs**: Typically $0.005-0.01 per message
- **Volume matters**: SMS/WhatsApp can be expensive at scale
- **Free tiers**: Usually limited or non-existent for SMS/WhatsApp

### Recommendation for Multi-Channel

**If you're planning SMS/WhatsApp**:
1. **Brevo** - Best balance (email + SMS included, WhatsApp available)
2. **Twilio** - Most comprehensive (email + SMS + WhatsApp, but more expensive)
3. **Separate providers** - Use Resend for email, Twilio for SMS/WhatsApp (best-of-breed)

**If email-only for now**:
- Start with **Resend** (best DX)
- Can add Twilio later for SMS/WhatsApp (they integrate well)

---

## Recommendation

### For Development/Testing: **Resend** ⭐
- Best developer experience
- Generous free tier (3k/month)
- Fastest integration
- No domain verification needed initially
- **Note**: Will need separate provider for SMS/WhatsApp later

### For Production (Low-Medium Volume): **Brevo** ⭐ **BEST IF PLANNING SMS/WHATSAPP**
- Best free tier (9k/month)
- Most affordable paid plans
- **SMS included** - no separate service needed
- **WhatsApp available** on paid plans
- Good balance of features
- **Multi-channel ready** - perfect if you plan to add SMS/WhatsApp

### For Production (High Volume): **AWS SES + SNS**
- Cheapest at scale ($0.10/1k emails, ~$0.006/SMS)
- Massive free tier if on AWS
- Best for cost-conscious high-volume senders
- **Multi-channel ready** via AWS ecosystem

### For Enterprise Multi-Channel: **Twilio**
- Most comprehensive platform
- Email (SendGrid) + SMS + WhatsApp
- Industry leader, most reliable
- Best for mission-critical multi-channel needs
- **Note**: More expensive, but most feature-complete

### For Reliability-First (Email Only): **Mailgun**
- Most established
- Best deliverability reputation
- Good for mission-critical emails
- **Note**: Will need separate provider for SMS/WhatsApp

---

## Quick Integration Checklist

For any provider:

1. ✅ Sign up and get API key/token
2. ✅ Add provider-specific config to `app/core/config.py`
3. ✅ Implement `*EmailClient` class in `app/services/email.py`
4. ✅ Update `get_email_client()` to handle new provider
5. ✅ Add provider to `EMAIL_PROVIDER` enum/validation
6. ✅ Test with console provider first, then switch
7. ✅ (Optional) Verify domain for production

---

## Notes

- All providers support the existing `EmailClient` Protocol interface
- Current `httpx` dependency works for all REST-based providers
- AWS SES requires `boto3` (add to `requirements.txt` if chosen)
- Twilio requires `twilio` SDK (add to `requirements.txt` if chosen)
- Domain verification improves deliverability but isn't required for all providers' free tiers
- Consider rate limiting in your invitation endpoint to avoid hitting daily limits

### Free WhatsApp Messaging Options

**Short answer: No permanent free tier, but there are free messaging windows.**

WhatsApp Business API has **no permanent free tier** for proactive messaging. However, there are specific scenarios where messaging is free:

#### Free Messaging Windows (Meta's Policy)

1. **24-Hour Customer Service Window** ✅
   - When a customer initiates a conversation by messaging your business
   - You can send **free-form messages** for 24 hours after their last message
   - Perfect for: Customer support, responding to inquiries
   - **Use case**: User sends "How do I accept an invitation?" → You can reply free for 24h

2. **72-Hour Free Entry Point (FEP) Window** ✅
   - When a user contacts you via:
     - Click-to-WhatsApp ad
     - Facebook Page call-to-action button
     - QR code scan
   - You can send **template messages** for 72 hours
   - Perfect for: Marketing follow-ups, onboarding flows
   - **Use case**: User clicks "Contact us on WhatsApp" → You can send templates free for 72h

#### What Costs Money

- **Proactive messaging** outside free windows (business-initiated)
- **Template messages** sent outside FEP window
- Pricing varies by:
  - Message category (marketing, utility, authentication)
  - Recipient's country (US: ~$0.005-0.01, varies globally)

#### Free Trial Options

Some providers offer free trial credits:

- **Twilio**: $15.50 free credit (enough for ~1,500-3,000 WhatsApp messages)
- **SendPulse**: 7-day free trial
- **Brevo**: No WhatsApp free tier (paid only)

#### Practical Implications for Your App

**For household invitations via WhatsApp:**

**Scenario 1: User-initiated (FREE)** ✅
- User messages your WhatsApp number: "I got an invitation"
- You can send invitation details free for 24 hours
- **Limitation**: Requires user to message first (not proactive)

**Scenario 2: Proactive invitation (PAID)** 💰
- You send invitation link via WhatsApp proactively
- Costs ~$0.005-0.01 per message
- **Alternative**: Send email (free/cheap) with WhatsApp option for follow-up

**Scenario 3: Click-to-WhatsApp ad (FREE for 72h)** ✅
- User clicks WhatsApp button in your email/invitation
- Opens 72-hour FEP window
- You can send templates free for 72 hours
- **Best of both worlds**: Email invitation → WhatsApp follow-up

#### Recommendation

**For cost-effective WhatsApp invitations:**

1. **Primary**: Send invitation via **email** (free/cheap)
2. **Include**: "Reply on WhatsApp for help" button/link
3. **When user messages**: Use 24-hour free window for support
4. **Optional**: Use Click-to-WhatsApp ads to trigger 72-hour FEP window

**Bottom line**: WhatsApp is great for **reactive** messaging (customer support), but **proactive** invitations will cost money. Email remains the most cost-effective for invitations.

---

### Future-Proofing for SMS/WhatsApp

If you're planning to add SMS/WhatsApp later:

1. **Design abstraction layer** - Create a `MessageClient` Protocol that supports both email and SMS
2. **Consider Brevo or Twilio** - If multi-channel is likely, starting with a unified platform saves migration later
3. **Separate concerns** - Keep email and SMS logic separate but share common patterns (invitation sending, etc.)
4. **Cost planning** - SMS/WhatsApp can be 10-100x more expensive than email per message
5. **User preferences** - Allow users to choose email vs SMS for notifications
6. **Leverage free windows** - Design flows to maximize use of WhatsApp's 24h/72h free windows

### Architecture Recommendation

For a future-proof multi-channel setup:

```python
# Abstract message sending
class MessageClient(Protocol):
    def send_invitation(
        self,
        *,
        to_email: str | None,
        to_phone: str | None,
        inviter_email: str,
        household_name: str,
        accept_url: str,
    ) -> None:
        """Send invitation via email and/or SMS."""

# Implementation
class BrevoMultiChannelClient:
    """Brevo client supporting email + SMS."""
    # Uses Brevo email API + Brevo SMS API
    # Single API key, unified error handling
```

This allows you to:
- Start with email-only (Brevo email)
- Add SMS later (Brevo SMS) without changing architecture
- Support both channels from one provider

