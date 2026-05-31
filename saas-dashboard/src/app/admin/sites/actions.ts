'use server';

import { supabase } from "@/lib/supabase";
import { revalidatePath } from "next/cache";

import { defaultSiteSettings } from "@/types/site";

export async function addSite(formData: FormData) {
  const name = formData.get('name') as string;
  const url = formData.get('url') as string;
  const amazonUrl = formData.get('amazonUrl') as string;
  const nichePrompt = formData.get('nichePrompt') as string;
  const affiliateTrackingId = formData.get('affiliateTrackingId') as string;
  const makeWebhookUrl = formData.get('makeWebhookUrl') as string;
  const sourceType = (formData.get('source_type') as string) || 'amazon';
  const twitterHandlesRaw = formData.get('twitter_handles') as string;
  
  if (!name || !url || !affiliateTrackingId) {
    return { error: 'Site name, URL, and Affiliate Tracking ID are required' };
  }

  const twitterHandles = twitterHandlesRaw
    ? twitterHandlesRaw.split(',').map(h => h.trim().replace(/^@/, '')).filter(Boolean)
    : [];

  // Fetch global settings to inherit
  const { data: globalData } = await supabase
    .from('global_settings')
    .select('settings')
    .eq('id', 1)
    .single();

  const settingsToApply = globalData?.settings || defaultSiteSettings;

  const { data, error } = await supabase
    .from('sites')
    .insert([{ 
      name, 
      url,
      amazon_bestseller_url: amazonUrl,
      niche_prompt: nichePrompt,
      affiliate_tracking_id: affiliateTrackingId,
      make_webhook_url: makeWebhookUrl,
      source_type: sourceType,
      twitter_handles: twitterHandles,
      settings: settingsToApply,
      status: 'active'
    }]);

  if (error) {
    return { error: error.message };
  }

  revalidatePath('/admin/sites');
  revalidatePath('/admin');
  return { success: true };
}

export async function deleteSite(siteId: string) {
  if (!siteId) return { error: 'Site ID is required' };

  const { error } = await supabase
    .from('sites')
    .delete()
    .eq('id', siteId);

  if (error) {
    return { error: error.message };
  }

  revalidatePath('/admin/sites');
  revalidatePath('/admin');
  return { success: true };
}

export async function updateSiteSettings(id: string, settings: any) {
  const { data, error } = await supabase
    .from('sites')
    .update({ settings })
    .eq('id', id);

  if (error) {
    return { error: error.message };
  }
  
  revalidatePath(`/admin/sites/${id}`);
  return { success: true };
}

export async function updateSiteDetails(id: string, details: {
  source_type?: string;
  twitter_handles?: string[];
  api_url?: string;
  bot_api_secret?: string;
  name?: string;
  url?: string;
  amazon_bestseller_url?: string;
  niche_prompt?: string;
  affiliate_tracking_id?: string;
  make_webhook_url?: string;
}) {
  const { data, error } = await supabase
    .from('sites')
    .update(details)
    .eq('id', id);

  if (error) {
    return { error: error.message };
  }

  // If source_type is updated, we sync twitter handles table or update processed logs as needed
  revalidatePath(`/admin/sites/${id}`);
  revalidatePath('/admin/sites');
  return { success: true };
}

