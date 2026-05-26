import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, Globe, Link as LinkIcon, Database, ArrowRight } from "lucide-react"
import { supabase } from "@/lib/supabase"
import { AddSiteModal } from "@/components/ui/add-site-modal"
import { DeleteSiteButton } from "@/components/ui/delete-site-button"
import Link from "next/link"

export default async function SitesManager() {
  // Fetch real sites data
  const { data: sites, error } = await supabase.from('sites').select('*').order('created_at', { ascending: false });
  
  // Also fetch keyword counts and published products
  const { data: keywords } = await supabase.from('keyword_pool').select('site_id');
  const { data: products } = await supabase.from('products').select('site_id, is_published').eq('is_published', true);

  const siteStats: Record<string, { kw: number, pub: number }> = {};
  
  if (sites) {
    sites.forEach(site => {
      siteStats[site.id] = { kw: 0, pub: 0 };
    });
  }

  if (keywords) {
    keywords.forEach(k => {
      if (k.site_id && siteStats[k.site_id]) siteStats[k.site_id].kw++;
    });
  }

  if (products) {
    products.forEach(p => {
      if (p.site_id && siteStats[p.site_id]) siteStats[p.site_id].pub++;
    });
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Site Manager</h2>
          <p className="text-muted-foreground opacity-70">
            Manage your connected SaaS clients and affiliate sites.
          </p>
        </div>
        <AddSiteModal />
      </div>

      <div className="flex items-center gap-4 bg-black/20 p-2 rounded-lg border border-white/10 backdrop-blur-md">
        <Search className="text-muted-foreground ml-2" size={18} />
        <Input 
          placeholder="Search sites by name or domain..." 
          className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 px-0" 
        />
      </div>

      {error && <div className="text-red-500 bg-red-500/10 p-4 rounded-md border border-red-500/20">{error.message}</div>}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {sites && sites.map((site) => {
          const stats = siteStats[site.id] || { kw: 0, pub: 0 };
          return (
          <div key={site.id} className="rounded-xl border border-white/10 bg-black/40 backdrop-blur-md overflow-hidden hover:border-blue-500/30 transition-all flex flex-col">
            <div className="p-5 flex justify-between items-start border-b border-white/5">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${site.status === 'active' ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]' : 'bg-yellow-500 shadow-[0_0_10px_rgba(234,179,8,0.5)]'}`} />
                <h3 className="font-semibold text-lg">{site.name || "Unnamed Site"}</h3>
              </div>
              <DeleteSiteButton siteId={site.id} />
            </div>
            
            <div className="p-5 space-y-4 flex-1">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Globe size={14} className="opacity-70" />
                <span className="truncate" title={site.amazon_bestseller_url}>{site.amazon_bestseller_url || "No Amazon URL"}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <LinkIcon size={14} className="opacity-70" />
                <span className="truncate" title={site.niche_prompt}>Niche: {site.niche_prompt || "N/A"}</span>
              </div>
              
              <div className="pt-2 grid grid-cols-2 gap-2">
                <div className="bg-white/5 rounded-md p-3">
                  <div className="text-xs opacity-50 mb-1 flex items-center gap-1">
                    <Database size={10} /> Keywords
                  </div>
                  <div className="text-xl font-bold">{stats.kw}</div>
                </div>
                <div className="bg-white/5 rounded-md p-3">
                  <div className="text-xs opacity-50 mb-1">Published</div>
                  <div className="text-xl font-bold">{stats.pub}</div>
                </div>
              </div>
            </div>
            
            <div className="bg-white/5 p-3">
              <Button variant="secondary" className="w-full h-10 bg-blue-600 hover:bg-blue-700 text-white gap-2 font-semibold" asChild>
                <Link href={`/admin/sites/${site.id}`}>
                  Bot Control Panel <ArrowRight size={16} />
                </Link>
              </Button>
            </div>
          </div>
        )})}
        {(!sites || sites.length === 0) && (
          <div className="col-span-full p-8 text-center text-muted-foreground border border-dashed border-white/20 rounded-xl">
            No sites found in the database.
          </div>
        )}
      </div>
    </div>
  )
}
