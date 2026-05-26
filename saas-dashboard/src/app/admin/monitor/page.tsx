import { Button } from "@/components/ui/button"
import { Activity, RefreshCw, CheckCircle2, AlertCircle, Clock } from "lucide-react"
import { supabase } from "@/lib/supabase"

export default async function LiveMonitor() {
  const { data: sites } = await supabase.from('sites').select('id, status');
  const activeBots = sites ? sites.filter(s => s.status === 'active').length : 0;

  const { count: pendingKeywords } = await supabase.from('keyword_pool').select('*', { count: 'exact', head: true }).eq('status', 'pending');
  
  // Calculate 24h ago
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const isoYesterday = yesterday.toISOString();

  const { count: success24h } = await supabase.from('products').select('*', { count: 'exact', head: true }).eq('is_published', true).gte('created_at', isoYesterday);

  // Recent activity logs (mixed from products and keyword_pool)
  const { data: recentProducts } = await supabase.from('products')
    .select('title, created_at, is_published, sites(name)')
    .order('created_at', { ascending: false })
    .limit(5);
    
  const { data: recentKeywords } = await supabase.from('keyword_pool')
    .select('keyword, status, created_at, sites(name)')
    .order('created_at', { ascending: false })
    .limit(5);

  let logs: any[] = [];
  
  if (recentProducts) {
    recentProducts.forEach(p => {
      const siteObj = p.sites as any;
      const siteName = Array.isArray(siteObj) ? siteObj[0]?.name : siteObj?.name;
      logs.push({
        site: siteName || "Unknown",
        action: p.is_published ? "Published Article" : "Scraped Product",
        item: p.title,
        status: "success",
        time: p.created_at
      });
    });
  }

  if (recentKeywords) {
    recentKeywords.forEach(k => {
      const siteObj = k.sites as any;
      const siteName = Array.isArray(siteObj) ? siteObj[0]?.name : siteObj?.name;
      logs.push({
        site: siteName || "Unknown",
        action: k.status === 'pending' ? "Discovered Keyword" : "Keyword Completed",
        item: k.keyword,
        status: k.status === 'pending' ? "processing" : "success",
        time: k.created_at
      });
    });
  }

  // Sort logs by time descending and take top 8
  logs.sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());
  logs = logs.slice(0, 8);

  const timeAgo = (dateStr: string) => {
    const diff = Math.floor((new Date().getTime() - new Date(dateStr).getTime()) / 1000);
    if (diff < 60) return `${diff} sec ago`;
    if (diff < 3600) return `${Math.floor(diff/60)} min ago`;
    if (diff < 86400) return `${Math.floor(diff/3600)} hours ago`;
    return `${Math.floor(diff/86400)} days ago`;
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Live Monitor</h2>
          <p className="text-muted-foreground opacity-70">
            Real-time status of your scraping and publishing pipeline.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm bg-green-500/10 text-green-400 px-3 py-1.5 rounded-full border border-green-500/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            System Operational
          </div>
          <Button variant="outline" size="sm" className="gap-2 border-white/10 bg-black/40">
            <RefreshCw size={14} /> Refresh
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4 mt-8">
        <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur-md p-5 flex items-center gap-4">
           <div className="h-12 w-12 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400">
             <Activity size={24} />
           </div>
           <div>
             <div className="text-sm opacity-70">Active Sites</div>
             <div className="text-2xl font-bold">{activeBots}</div>
           </div>
        </div>
        <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur-md p-5 flex items-center gap-4">
           <div className="h-12 w-12 rounded-full bg-amber-500/20 flex items-center justify-center text-amber-400">
             <Clock size={24} />
           </div>
           <div>
             <div className="text-sm opacity-70">Pending Keywords</div>
             <div className="text-2xl font-bold">{pendingKeywords || 0}</div>
           </div>
        </div>
        <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur-md p-5 flex items-center gap-4">
           <div className="h-12 w-12 rounded-full bg-green-500/20 flex items-center justify-center text-green-400">
             <CheckCircle2 size={24} />
           </div>
           <div>
             <div className="text-sm opacity-70">Success (24h)</div>
             <div className="text-2xl font-bold">{success24h || 0}</div>
           </div>
        </div>
        <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur-md p-5 flex items-center gap-4">
           <div className="h-12 w-12 rounded-full bg-red-500/20 flex items-center justify-center text-red-400">
             <AlertCircle size={24} />
           </div>
           <div>
             <div className="text-sm opacity-70">Failed (24h)</div>
             <div className="text-2xl font-bold">0</div>
           </div>
        </div>
      </div>

      <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur-md overflow-hidden mt-6 shadow-lg shadow-blue-900/5">
        <div className="p-4 border-b border-white/5 font-semibold bg-white/5">Recent Activity Log</div>
        <div className="divide-y divide-white/5">
          {logs && logs.length > 0 ? logs.map((log, i) => (
            <div key={i} className="p-4 flex items-center justify-between hover:bg-white/5 transition-colors">
              <div className="flex items-center gap-4">
                {log.status === 'success' && <CheckCircle2 className="text-green-400" size={18} />}
                {log.status === 'processing' && <RefreshCw className="text-blue-400 animate-spin" size={18} />}
                {log.status === 'error' && <AlertCircle className="text-red-400" size={18} />}
                <div>
                  <div className="font-medium text-sm">{log.action}</div>
                  <div className="text-xs text-muted-foreground flex items-center gap-2 mt-0.5">
                    <span className="bg-white/10 px-1.5 py-0.5 rounded text-[10px] uppercase">{log.site}</span>
                    <span>{log.item}</span>
                  </div>
                </div>
              </div>
              <div className="text-xs text-muted-foreground">{timeAgo(log.time)}</div>
            </div>
          )) : (
            <div className="p-8 text-center text-muted-foreground">No recent activity found in database.</div>
          )}
        </div>
      </div>
    </div>
  )
}
