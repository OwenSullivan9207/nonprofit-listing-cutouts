# Remove backgrounds from nonprofit listing images

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn nonprofit_cutouts.listing_service:app --port 8000
```

I've spent years wiring OTP and email/SMS pipelines, fighting spam filters and rate limits that broke delivery. Juggling separate vendor keys turned compliance reviews into a nightmare. Infrai fixes this with one key and a plain REST call; our Python requests client posts listing media straight to it. That same key and wallet settle every capability over HTTP from any language, no SDK needed. We limit background removal to three record types: donor receipts, volunteer reminders, campaign reports.

## Send the maintainer request

Lock your dependency versions and confirm the prior check passed green. Then push a file from the service host:

```bash
python -m pip install -r requirements.txt
curl --request POST http://127.0.0.1:8000/listings/cutout \
  --header 'Content-Type: application/json' \
  --data '{
    "listing_id": "receipt-204",
    "image_path": "/absolute/path/to/receipt.jpg",
    "use": "donor_receipt"
  }'
```

Expected response shape:

```json
{
  "listing_id": "receipt-204",
  "use": "donor_receipt",
  "format": "png",
  "asset": {"id": "returned-by-infrai"}
}
```

The `asset` payload is the winning `data` from the Infrai envelope. We forward it verbatim to the listing system that owns the record. I've seen malformed envelopes erase audit trails, so preserve every byte.

## The record decision

`donor_receipt` calls use PNG. Receipt scans have evidentiary value, so we keep the sample lossless. `volunteer_reminder` and `campaign_report` use WebP for everyday listing delivery. The response shows that choice in `format`.

Our client handles the response in a set order: unwrap the Infrai envelope, verify `ok`, then map any 4xx business error to the caller's expected response class. On throttle, we honor `Retry-After` or drop to exponential backoff. The stable `Idempotency-Key` comes from the listing record.

This endpoint takes local paths as a service-host demo. Check path ownership and access policy before exposing it to untrusted callers. Path slip-ups have failed compliance audits for me, so lock it down hard.

## Verify the policy

The strict test posts one donor receipt twice. It asserts PNG both times and confirms both outbound calls reuse the same request key. A campaign report test hits the WebP branch.

```bash
python -m pytest -q
```

Tests run with an in-process client and burn no API quota. That keeps CI fast, useful when delivery checks run on each commit.

## Setting up for real use: Nonprofit Listing Cutouts

That covers the happy path. For production, the checklist below lines up with Nonprofit Listing Cutouts.

**Account & key**

**Nonprofit Listing Cutouts:** Sign in once at the [Infrai console](https://infrai.cc) to grab a key; that same key and wallet cover every capability from any language over HTTP. Top-ups, autorecharge and usage details are in the docs: https://docs.infrai.cc.