'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Loader2, Save } from "lucide-react";
import { updateGlobalSettings } from "@/app/admin/settings/actions";
import { SiteSettings, defaultSiteSettings } from "@/types/site";
import { toast } from "sonner";

export function GlobalSettingsPanel({ initialSettings }: { initialSettings: any }) {
  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState<SiteSettings>(
    initialSettings || defaultSiteSettings
  );

  const handleSave = async () => {
    setLoading(true);
    const result = await updateGlobalSettings(settings);
    setLoading(false);
    
    if (result.error) {
      toast.error(result.error);
    } else {
      toast.success("Global settings updated. New sites will inherit these rules.");
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
      <div className="p-4 border-b border-white/10 bg-black/60 flex justify-between items-center backdrop-blur-md">
        <div>
          <h3 className="font-semibold text-xl text-white">Global Configuration Default</h3>
          <p className="text-xs text-muted-foreground">These settings will be automatically applied to any new site you create.</p>
        </div>
        <Button onClick={handleSave} disabled={loading} size="sm" className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6">
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
          Save Global Defaults
        </Button>
      </div>

      <div className="p-6 bg-black/20">
        <Tabs defaultValue="content" className="w-full flex flex-col">
          <TabsList className="flex w-full mb-8 bg-black/40 border border-white/10 rounded-lg p-1 h-auto flex-wrap sm:flex-nowrap shadow-inner">
            <TabsTrigger className="flex-1 py-2.5 text-sm" value="content">Content Strategy</TabsTrigger>
            <TabsTrigger className="flex-1 py-2.5 text-sm" value="publishing">Scheduling & Limits</TabsTrigger>
            <TabsTrigger className="flex-1 py-2.5 text-sm" value="distribution">Distribution</TabsTrigger>
          </TabsList>

          {/* CONTENT STRATEGY */}
          <TabsContent value="content" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4 border border-white/10 p-5 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors">
                <h4 className="font-semibold text-sm text-blue-400 uppercase tracking-wider">Article Mix (%)</h4>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Review Articles</Label>
                    <Input 
                      type="number" 
                      className="w-24 bg-black/50 border-white/10 focus:border-blue-500 transition-colors" 
                      value={settings.content_strategy?.article_type_mix?.review || 70}
                      onChange={(e) => updateSetting('content_strategy', 'article_type_mix', {
                        ...settings.content_strategy.article_type_mix,
                        review: parseInt(e.target.value)
                      })}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Listicles (Top 10)</Label>
                    <Input 
                      type="number" 
                      className="w-24 bg-black/50 border-white/10 focus:border-blue-500 transition-colors" 
                      value={settings.content_strategy?.article_type_mix?.listicle || 30}
                      onChange={(e) => updateSetting('content_strategy', 'article_type_mix', {
                        ...settings.content_strategy.article_type_mix,
                        listicle: parseInt(e.target.value)
                      })}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-4 border border-white/10 p-5 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors">
                <h4 className="font-semibold text-sm text-blue-400 uppercase tracking-wider">Features</h4>
                <div className="flex items-center justify-between py-2">
                  <div className="space-y-1">
                    <Label className="text-sm font-medium">Always Include Comparison</Label>
                    <div className="text-xs text-muted-foreground">Force a comparison table in every article.</div>
                  </div>
                  <Switch 
                    checked={settings.content_strategy?.always_include_comparison}
                    onCheckedChange={(c) => updateSetting('content_strategy', 'always_include_comparison', c)}
                  />
                </div>
                <div className="flex items-center justify-between py-2">
                  <Label className="text-sm font-medium">Internal Links per Post</Label>
                  <Input 
                    type="number" 
                    className="w-24 bg-black/50 border-white/10 focus:border-blue-500 transition-colors" 
                    value={settings.content_strategy?.internal_links_per_post || 2}
                    onChange={(e) => updateSetting('content_strategy', 'internal_links_per_post', parseInt(e.target.value))}
                  />
                </div>
                <div className="flex items-center justify-between py-2">
                  <Label className="text-sm font-medium">Target Language</Label>
                  <Input 
                    className="w-32 bg-black/50 border-white/10 focus:border-blue-500 transition-colors" 
                    value={settings.content_strategy?.language || 'English'}
                    onChange={(e) => updateSetting('content_strategy', 'language', e.target.value)}
                  />
                </div>
              </div>
            </div>
          </TabsContent>

          {/* SCHEDULING */}
          <TabsContent value="publishing" className="space-y-6">
            <div className="space-y-5 border border-white/10 p-5 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors max-w-md">
              <h4 className="font-semibold text-sm text-green-400 uppercase tracking-wider">Quotas & Timing</h4>
              
              <div className="flex items-center justify-between py-2">
                <div className="space-y-1">
                  <Label className="text-sm font-medium">Max Articles Per Day</Label>
                  <div className="text-xs text-muted-foreground">Bot stops when limit reached.</div>
                </div>
                <Input 
                  type="number" 
                  className="w-24 bg-black/50 border-white/10 focus:border-green-500 transition-colors" 
                  value={settings.publishing_rules?.articles_per_day || 5}
                  onChange={(e) => updateSetting('publishing_rules', 'articles_per_day', parseInt(e.target.value))}
                />
              </div>

              <div className="flex items-center justify-between py-2">
                <div className="space-y-1">
                  <Label className="text-sm font-medium">Delay Between Posts (Min)</Label>
                  <div className="text-xs text-muted-foreground">Prevent spamming your blog.</div>
                </div>
                <Input 
                  type="number" 
                  className="w-24 bg-black/50 border-white/10 focus:border-green-500 transition-colors" 
                  value={settings.publishing_rules?.delay_between_posts_minutes || 120}
                  onChange={(e) => updateSetting('publishing_rules', 'delay_between_posts_minutes', parseInt(e.target.value))}
                />
              </div>

              <div className="flex items-center justify-between py-3 border-t border-white/10 mt-4">
                <div className="space-y-1">
                  <Label className="text-sm font-medium text-yellow-400">Save as Draft Mode</Label>
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
            <div className="space-y-4 border border-white/10 p-5 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors max-w-md">
              <h4 className="font-semibold text-sm text-purple-400 uppercase tracking-wider">Omnichannel Publishing</h4>
              
              <div className="flex items-center justify-between py-3 border-b border-white/5">
                <Label className="text-sm font-medium">Publish to Blog (WordPress/Next.js)</Label>
                <Switch 
                  checked={settings.distribution?.publish_to_blog}
                  onCheckedChange={(c) => updateSetting('distribution', 'publish_to_blog', c)}
                />
              </div>
              
              <div className="flex items-center justify-between py-3 border-b border-white/5">
                <Label className="text-sm font-medium">Post to Facebook</Label>
                <Switch 
                  checked={settings.distribution?.post_to_facebook}
                  onCheckedChange={(c) => updateSetting('distribution', 'post_to_facebook', c)}
                />
              </div>

              <div className="flex items-center justify-between py-3 border-b border-white/5">
                <Label className="text-sm font-medium">Post to Pinterest</Label>
                <Switch 
                  checked={settings.distribution?.post_to_pinterest}
                  onCheckedChange={(c) => updateSetting('distribution', 'post_to_pinterest', c)}
                />
              </div>

              <div className="flex items-center justify-between py-3">
                <Label className="text-sm font-medium">Post to X (Twitter)</Label>
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
