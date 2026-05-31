'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Loader2, Save, Settings, Database, Share2, Wrench } from "lucide-react";
import { updateSiteSettings, updateSiteDetails } from "@/app/admin/sites/actions";
import { SiteSettings, defaultSiteSettings } from "@/types/site";
import { toast } from "sonner";

export function SiteSettingsPanel({ site }: { site: any }) {
  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState<SiteSettings>(
    site.settings || defaultSiteSettings
  );

  // Automation Core fields
  const [sourceType, setSourceType] = useState(site.source_type || 'amazon');
  const [twitterHandles, setTwitterHandles] = useState(
    site.twitter_handles ? site.twitter_handles.join(', ') : ''
  );
  const [apiUrl, setApiUrl] = useState(site.api_url || '');
  const [botApiSecret, setBotApiSecret] = useState(site.bot_api_secret || '');

  // General fields
  const [name, setName] = useState(site.name || '');
  const [url, setUrl] = useState(site.url || '');
  const [amazonBestsellerUrl, setAmazonBestsellerUrl] = useState(site.amazon_bestseller_url || '');
  const [nichePrompt, setNichePrompt] = useState(site.niche_prompt || '');
  const [affiliateTrackingId, setAffiliateTrackingId] = useState(site.affiliate_tracking_id || '');
  const [makeWebhookUrl, setMakeWebhookUrl] = useState(site.make_webhook_url || '');

  const handleSave = async () => {
    setLoading(true);
    
    // Parse twitter handles
    const twitterHandlesList = twitterHandles
      ? twitterHandles.split(',').map(h => h.trim().replace(/^@/, '')).filter(Boolean)
      : [];

    const detailsResult = await updateSiteDetails(site.id, {
      name,
      url,
      source_type: sourceType,
      twitter_handles: twitterHandlesList,
      api_url: apiUrl,
      bot_api_secret: botApiSecret,
      amazon_bestseller_url: amazonBestsellerUrl,
      niche_prompt: nichePrompt,
      affiliate_tracking_id: affiliateTrackingId,
      make_webhook_url: makeWebhookUrl,
    });

    const settingsResult = await updateSiteSettings(site.id, settings);
    
    setLoading(false);
    
    if (detailsResult.error) {
      toast.error(`Details error: ${detailsResult.error}`);
    } else if (settingsResult.error) {
      toast.error(`Settings error: ${settingsResult.error}`);
    } else {
      toast.success("Site configuration and settings updated.");
    }
  };

  const updateSetting = (category: keyof SiteSettings, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  return (
    <div className="bg-[#111] border border-white/10 rounded-xl overflow-hidden shadow-2xl">
      <div className="p-5 border-b border-white/10 bg-black/40 flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-lg text-white">⚙️ Site Configuration & Settings</h3>
          <p className="text-xs text-muted-foreground opacity-80">Manage general details, core automation pipeline settings, and content strategies.</p>
        </div>
        <Button onClick={handleSave} disabled={loading} size="sm" className="bg-blue-600 hover:bg-blue-700 text-white font-semibold">
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
          Save Changes
        </Button>
      </div>

      <div className="p-6">
        <Tabs defaultValue="core" className="w-full flex flex-col">
          <TabsList className="flex w-full mb-6 bg-black/40 border border-white/10 rounded-lg p-1 h-auto flex-wrap sm:flex-nowrap">
            <TabsTrigger className="flex-1 py-2 gap-1.5" value="core">
              <Wrench size={14} /> Automation Core
            </TabsTrigger>
            <TabsTrigger className="flex-1 py-2 gap-1.5" value="content">
              <Settings size={14} /> Content Strategy
            </TabsTrigger>
            <TabsTrigger className="flex-1 py-2 gap-1.5" value="publishing">
              <Database size={14} /> Scheduling & Limits
            </TabsTrigger>
            <TabsTrigger className="flex-1 py-2 gap-1.5" value="distribution">
              <Share2 size={14} /> Distribution
            </TabsTrigger>
          </TabsList>

          {/* AUTOMATION CORE */}
          <TabsContent value="core" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Site Identity */}
              <div className="space-y-4 border border-white/10 p-4 rounded-lg bg-black/20">
                <h4 className="font-semibold text-sm text-blue-400 border-b border-white/5 pb-2">1. Site Identity & Paths</h4>
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="site_name">Site Name</Label>
                    <Input id="site_name" className="bg-white/5 mt-1" value={name} onChange={e => setName(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="site_url">Target Site URL</Label>
                    <Input id="site_url" className="bg-white/5 mt-1" value={url} onChange={e => setUrl(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="niche_prompt">Niche Description / Prompt</Label>
                    <Input id="niche_prompt" className="bg-white/5 mt-1" value={nichePrompt} onChange={e => setNichePrompt(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="affiliate_id">Affiliate / Tracker Tag</Label>
                    <Input id="affiliate_id" className="bg-white/5 mt-1" value={affiliateTrackingId} onChange={e => setAffiliateTrackingId(e.target.value)} />
                  </div>
                </div>
              </div>

              {/* Engine Configuration */}
              <div className="space-y-4 border border-white/10 p-4 rounded-lg bg-black/20">
                <h4 className="font-semibold text-sm text-blue-400 border-b border-white/5 pb-2">2. Automation Engine</h4>
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="core_source_type">Automation Mode</Label>
                    <select
                      id="core_source_type"
                      value={sourceType}
                      onChange={e => setSourceType(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-md p-2 mt-1 text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="amazon" className="bg-[#111]">Amazon Affiliate Scraper Mode</option>
                      <option value="twitter" className="bg-[#111]">Twitter Trend Auto-Blog Mode</option>
                    </select>
                  </div>

                  {sourceType === 'amazon' ? (
                    <div>
                      <Label htmlFor="amazon_url">Amazon Bestseller URL</Label>
                      <Input id="amazon_url" className="bg-white/5 mt-1" value={amazonBestsellerUrl} onChange={e => setAmazonBestsellerUrl(e.target.value)} />
                    </div>
                  ) : (
                    <div>
                      <Label htmlFor="twitter_handles">Monitored Twitter Handles</Label>
                      <Input 
                        id="twitter_handles" 
                        placeholder="sama, karpathy, AndrewYNg (comma-separated)" 
                        className="bg-white/5 mt-1" 
                        value={twitterHandles} 
                        onChange={e => setTwitterHandles(e.target.value)} 
                      />
                      <p className="text-[10px] text-muted-foreground mt-1">Handles the bot pulls tweets from to write trends.</p>
                    </div>
                  )}

                  <div>
                    <Label htmlFor="api_url">Publishing Endpoint (API URL)</Label>
                    <Input id="api_url" className="bg-white/5 mt-1 font-mono text-xs" value={apiUrl} onChange={e => setApiUrl(e.target.value)} placeholder="https://site.com/api/posts" />
                  </div>

                  <div>
                    <Label htmlFor="bot_api_secret">Bot API Secret Token</Label>
                    <Input id="bot_api_secret" type="password" className="bg-white/5 mt-1 font-mono text-xs" value={botApiSecret} onChange={e => setBotApiSecret(e.target.value)} />
                  </div>
                </div>
              </div>

            </div>
          </TabsContent>

          {/* CONTENT STRATEGY */}
          <TabsContent value="content" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4 border border-white/10 p-4 rounded-lg bg-black/20">
                <h4 className="font-medium text-sm text-blue-400">Article Mix (%)</h4>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>Review Articles</Label>
                    <Input 
                      type="number" 
                      className="w-24 bg-white/5" 
                      value={settings.content_strategy?.article_type_mix?.review || 70}
                      onChange={(e) => updateSetting('content_strategy', 'article_type_mix', {
                        ...settings.content_strategy.article_type_mix,
                        review: parseInt(e.target.value)
                      })}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Listicles (Top 10)</Label>
                    <Input 
                      type="number" 
                      className="w-24 bg-white/5" 
                      value={settings.content_strategy?.article_type_mix?.listicle || 30}
                      onChange={(e) => updateSetting('content_strategy', 'article_type_mix', {
                        ...settings.content_strategy.article_type_mix,
                        listicle: parseInt(e.target.value)
                      })}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-4 border border-white/10 p-4 rounded-lg bg-black/20">
                <h4 className="font-medium text-sm text-blue-400">Features</h4>
                <div className="flex items-center justify-between py-2">
                  <div className="space-y-0.5">
                    <Label>Always Include Comparison</Label>
                    <div className="text-xs text-muted-foreground">Force a comparison table in every article.</div>
                  </div>
                  <Switch 
                    checked={settings.content_strategy?.always_include_comparison}
                    onCheckedChange={(c) => updateSetting('content_strategy', 'always_include_comparison', c)}
                  />
                </div>
                <div className="flex items-center justify-between py-2">
                  <Label>Internal Links per Post</Label>
                  <Input 
                    type="number" 
                    className="w-24 bg-white/5" 
                    value={settings.content_strategy?.internal_links_per_post || 2}
                    onChange={(e) => updateSetting('content_strategy', 'internal_links_per_post', parseInt(e.target.value))}
                  />
                </div>
                <div className="flex items-center justify-between py-2">
                  <Label>Target Language</Label>
                  <Input 
                    className="w-32 bg-white/5" 
                    value={settings.content_strategy?.language || 'English'}
                    onChange={(e) => updateSetting('content_strategy', 'language', e.target.value)}
                  />
                </div>
              </div>
            </div>
          </TabsContent>

          {/* SCHEDULING */}
          <TabsContent value="publishing" className="space-y-6">
            <div className="space-y-4 border border-white/10 p-4 rounded-lg bg-black/20 max-w-md">
              <h4 className="font-medium text-sm text-green-400">Quotas & Timing</h4>
              
              <div className="flex items-center justify-between py-2">
                <div className="space-y-0.5">
                  <Label>Max Articles Per Day</Label>
                  <div className="text-xs text-muted-foreground">Bot stops when limit reached.</div>
                </div>
                <Input 
                  type="number" 
                  className="w-24 bg-white/5" 
                  value={settings.publishing_rules?.articles_per_day || 5}
                  onChange={(e) => updateSetting('publishing_rules', 'articles_per_day', parseInt(e.target.value))}
                />
              </div>

              <div className="flex items-center justify-between py-2">
                <div className="space-y-0.5">
                  <Label>Delay Between Posts (Min)</Label>
                  <div className="text-xs text-muted-foreground">Prevent spamming your blog.</div>
                </div>
                <Input 
                  type="number" 
                  className="w-24 bg-white/5" 
                  value={settings.publishing_rules?.delay_between_posts_minutes || 120}
                  onChange={(e) => updateSetting('publishing_rules', 'delay_between_posts_minutes', parseInt(e.target.value))}
                />
              </div>

              <div className="flex items-center justify-between py-2 border-t border-white/10 mt-2 pt-4">
                <div className="space-y-0.5">
                  <Label>Save as Draft</Label>
                  <div className="text-xs text-muted-foreground">Require manual review before publishing.</div>
                </div>
                <Switch 
                  checked={settings.publishing_rules?.save_as_draft}
                  onCheckedChange={(c) => updateSetting('publishing_rules', 'save_as_draft', c)}
                />
              </div>
            </div>
          </TabsContent>

          {/* DISTRIBUTION */}
          <TabsContent value="distribution" className="space-y-6">
            <div className="space-y-4 border border-white/10 p-4 rounded-lg bg-black/20 max-w-md">
              <h4 className="font-medium text-sm text-purple-400">Omnichannel Publishing</h4>
              
              <div className="flex items-center justify-between py-2">
                <Label>Publish to Blog (WordPress/Next.js)</Label>
                <Switch 
                  checked={settings.distribution?.publish_to_blog}
                  onCheckedChange={(c) => updateSetting('distribution', 'publish_to_blog', c)}
                />
              </div>
              
              <div className="flex items-center justify-between py-2">
                <Label>Post to Facebook</Label>
                <Switch 
                  checked={settings.distribution?.post_to_facebook}
                  onCheckedChange={(c) => updateSetting('distribution', 'post_to_facebook', c)}
                />
              </div>

              <div className="flex items-center justify-between py-2">
                <Label>Post to Pinterest</Label>
                <Switch 
                  checked={settings.distribution?.post_to_pinterest}
                  onCheckedChange={(c) => updateSetting('distribution', 'post_to_pinterest', c)}
                />
              </div>

              <div className="flex items-center justify-between py-2">
                <Label>Post to X (Twitter)</Label>
                <Switch 
                  checked={settings.distribution?.post_to_x}
                  onCheckedChange={(c) => updateSetting('distribution', 'post_to_x', c)}
                />
              </div>
            </div>
          </TabsContent>

        </Tabs>
      </div>
    </div>
  );
}
