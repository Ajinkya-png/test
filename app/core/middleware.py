from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator
from ..core.config import settings

validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)

async def verify_twilio_request(request: Request):
    # Twilio sends form-encoded body; construct full URL + params
    url = str(request.url)
    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Twilio signature")
    form = await request.form()
    params = dict(form)
    valid = validator.validate(url, params, signature)
    if not valid:
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    return True
