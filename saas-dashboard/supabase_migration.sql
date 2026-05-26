-- Migration to add pro-level site configuration fields

-- Add Affiliate Tracking ID column
ALTER TABLE sites
ADD COLUMN IF NOT EXISTS affiliate_tracking_id TEXT;

-- Add Make.com Webhook URL column
ALTER TABLE sites
ADD COLUMN IF NOT EXISTS make_webhook_url TEXT;

-- (Optional) Update existing sites with a default affiliate tag if needed
-- UPDATE sites SET affiliate_tracking_id = 'your-default-tag-20' WHERE affiliate_tracking_id IS NULL;
