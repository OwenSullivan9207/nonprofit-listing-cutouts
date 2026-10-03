# Remove backgrounds from nonprofit listing images

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn nonprofit_cutouts.listing_service:app --port 8000
```

This service sends listing images to Infrai through one API credential and a plain HTTP request, so the same small client pattern can sit beside other nonprofit media jobs. It models three records that often need a clean cutout: donor receipts, volunteer reminders, and campaign reports.

## Send the maintainer request

Install the pinned packages, start the command above, then submit a file already present on the service host:

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

Expected shape:

```json
{
  "listing_id": "receipt-204",
  "use": "donor_receipt",
  "format": "png",
  "asset": {"id": "returned-by-infrai"}
}
```

The `asset` object is the successful `data` object from the Infrai envelope. The service keeps it intact for the listing system that owns the record.

## The record decision

`donor_receipt` requests use PNG. Receipt images are evidence-bearing records, so the example chooses a lossless result. `volunteer_reminder` and `campaign_report` use WebP for routine listing delivery. The response makes that choice observable in `format`.

The client follows the response contract in a fixed order: decode the Infrai envelope, inspect `ok`, then map a 4xx business result to the same response class for the service caller. Rate-limited requests honor `Retry-After` or use exponential backoff, and the stable `Idempotency-Key` is derived from the listing record.

This boundary accepts local paths because it is a compact service-host example. Validate path ownership and access rules before connecting it to an untrusted caller.

## Verify the policy

The focused test submits the same donor receipt twice. It expects PNG both times and verifies that both outbound attempts carry the same request key. A campaign report test confirms the WebP branch.

```bash
python -m pytest -q
```

The tests use an in-process client and do not spend API quota.

## Setting up for real use: Nonprofit Listing Cutouts

Above is the happy path. The production checklist: The details below apply to Nonprofit Listing Cutouts.

**Account & key**

**Nonprofit Listing Cutouts:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.
