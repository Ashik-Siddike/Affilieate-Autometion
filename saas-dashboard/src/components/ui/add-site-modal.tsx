'use client';

import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PlusCircle, Loader2 } from "lucide-react";
import { addSite } from "@/app/admin/sites/actions";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";

export function AddSiteModal() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sourceType, setSourceType] = useState('amazon');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    const formData = new FormData(e.currentTarget);
    const result = await addSite(formData);
    
    setLoading(false);
    
    if (result.error) {
      setError(result.error);
    } else {
      setOpen(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button className="gap-2" />}>
        <PlusCircle size={16} /> Add New Site
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] max-h-[85vh] overflow-y-auto bg-black border border-white/10 text-white">
        <DialogHeader>
          <DialogTitle className="text-xl">Add New Site</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Configure a new target site for professional affiliate or social media trend automation.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-6 pt-4">
          {error && <div className="text-red-500 text-sm bg-red-500/10 p-3 rounded border border-red-500/20">{error}</div>}
          
          <div className="space-y-4">
            <h4 className="text-sm font-semibold uppercase tracking-wider text-blue-400 border-b border-white/10 pb-2">1. General Information</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Site Name</Label>
                <Input id="name" name="name" placeholder="e.g. Tech Gadgets Pro" required className="bg-white/5 border-white/10" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="url">Target Website URL</Label>
                <Input id="url" name="url" placeholder="https://my-site.com" required className="bg-white/5 border-white/10" />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="source_type">Automation Mode</Label>
                <select
                  id="source_type"
                  name="source_type"
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-md p-2.5 text-white text-sm font-sans focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="amazon" className="bg-[#111]">Amazon Affiliate Scraper</option>
                  <option value="twitter" className="bg-[#111]">Twitter Trend Auto-Blog</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="nichePrompt">Niche Prompt (Optional)</Label>
                <Input id="nichePrompt" name="nichePrompt" placeholder="e.g. AI technology, Gadgets" className="bg-white/5 border-white/10" />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="text-sm font-semibold uppercase tracking-wider text-blue-400 border-b border-white/10 pb-2">2. Source & Monetization</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="affiliateTrackingId">Affiliate Tag / Tracker ID</Label>
                <Input id="affiliateTrackingId" name="affiliateTrackingId" placeholder="e.g. mytag-20" required className="bg-white/5 border-white/10" />
              </div>
              
              {sourceType === 'amazon' ? (
                <div className="space-y-2">
                  <Label htmlFor="amazonUrl">Amazon Bestseller URL</Label>
                  <Input id="amazonUrl" name="amazonUrl" placeholder="https://www.amazon.com/Best-Sellers..." className="bg-white/5 border-white/10" />
                </div>
              ) : (
                <div className="space-y-2">
                  <Label htmlFor="twitter_handles">Twitter Handles (comma-separated)</Label>
                  <Input id="twitter_handles" name="twitter_handles" placeholder="e.g. sama, karpathy, AndrewYNg" className="bg-white/5 border-white/10" />
                </div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="text-sm font-semibold uppercase tracking-wider text-blue-400 border-b border-white/10 pb-2">3. Automation Integration</h4>
            <div className="space-y-2">
              <Label htmlFor="makeWebhookUrl">Make.com Webhook URL (Optional)</Label>
              <Input id="makeWebhookUrl" name="makeWebhookUrl" placeholder="https://hook.us1.make.com/..." className="bg-white/5 border-white/10" />
            </div>
          </div>
          
          <div className="pt-6 flex justify-end gap-3 border-t border-white/10 mt-6">
            <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white">
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save Configuration
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
