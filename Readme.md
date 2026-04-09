## School OS - Production Setup

### Twilio WhatsApp (REQUIRED)

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_32_char_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

1. [Twilio Console](https://console.twilio.com)
2. Get Sandbox: WhatsApp → Try it out → Sandbox
3. Add your mobile: Send "join <code>" to sandbox WA number

### Railway Deploy

1. Backend: Railway → New Project → GitHub → school-os → backend/
2. Add vars above
3. ✅ Deploy

### Local Dev

```bash
docker-compose up
# Frontend: localhost:3000
# Backend: localhost:8000
```

**Test WhatsApp:**

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"phone":"+91YOURNO","message":"Test from School OS"}' \\
  https://your-app.up.railway.app/api/notifications/send-whatsapp
```

**Performance:** Bulk attendance saves 30 students in ~500ms (was 15s+)
