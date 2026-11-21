# DFW trades outreach

`scan.py` scrapes Google Maps (via Apify) for trades in DFW, filters, and creates
GHL contacts tagged `dfw-trades` + `to-review`, each with a drafted email in Notes.

Setup: `pip install requests`, then set `APIFY_TOKEN`, `GHL_TOKEN`
(Settings > Private Integrations; scopes: contacts read/write), `GHL_LOCATION_ID`,
`SENDER_NAME`, `OFFER`. Try `python scan.py --dry-run` first.

Phone workflow in the GHL app: filter by tag `to-review` -> open contact -> read draft
in Notes -> send via Conversations -> swap tag to `contacted`. Replies land in the same thread.

Rules for cold email: identify yourself, include a physical address and an easy opt-out,
honor opt-outs (GHL's DND flag), and keep volume low at first to protect your domain.
Never commit lead data to this repo (it's public); `.gitignore` blocks the preview CSV.
