import { supabase } from "@/lib/supabase"

export default async function AdminDashboard() {
  const { data: sites } = await supabase.from('sites').select('id, status');
  const { count: productsCount } = await supabase.from('products').select('*', { count: 'exact', head: true });
  const { count: publishedCount } = await supabase.from('products').select('*', { count: 'exact', head: true }).eq('is_published', true);
  const { count: keywordsCount } = await supabase.from('keyword_pool').select('*', { count: 'exact', head: true });
  
  const { data: recentPublications } = await supabase.from('products')
    .select('title, post_link, created_at, sites(name)')
    .eq('is_published', true)
    .order('created_at', { ascending: false })
    .limit(5);

  const activeSites = sites ? sites.filter(s => s.status === 'active').length : 0;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Overview</h2>
        <p className="text-muted-foreground opacity-70">
          Welcome back! Here is a summary of your affiliate automation network.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Bento Box Style Cards */}
        {[
          { title: "Active Sites", value: activeSites.toString(), desc: "Total connected sites" },
          { title: "Products Scraped", value: (productsCount || 0).toString(), desc: "Products in DB" },
          { title: "Live Articles", value: (publishedCount || 0).toString(), desc: "Successfully published" },
          { title: "Keywords in Pool", value: (keywordsCount || 0).toString(), desc: "Pending & completed" },
        ].map((stat, i) => (
          <div key={i} className="rounded-xl border border-white/10 bg-black/40 backdrop-blur-md p-6 shadow-lg shadow-blue-900/10 hover:border-blue-500/30 transition-all">
            <h3 className="text-sm font-medium opacity-70">{stat.title}</h3>
            <div className="mt-2 text-3xl font-bold">{stat.value}</div>
            <p className="text-xs opacity-50 mt-1">{stat.desc}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7 mt-6">
        <div className="col-span-4 rounded-xl border border-white/10 bg-black/40 backdrop-blur-md p-6 shadow-lg flex flex-col items-center justify-center min-h-[300px]">
           <h3 className="text-lg font-semibold w-full text-left mb-4">Network Activity</h3>
           <div className="flex-1 w-full flex items-center justify-center border border-dashed border-white/10 rounded-lg bg-white/5">
             <p className="opacity-50">Chart visualization coming soon</p>
           </div>
        </div>
        <div className="col-span-3 rounded-xl border border-white/10 bg-black/40 backdrop-blur-md p-6 shadow-lg">
           <h3 className="text-lg font-semibold mb-4">Recent Publications</h3>
           <div className="space-y-4">
              {recentPublications && recentPublications.length > 0 ? recentPublications.map((pub, i) => (
                <div key={i} className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded bg-green-500/20 flex items-center justify-center text-green-400">
                    <span className="text-xs font-bold">LIVE</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <a href={pub.post_link || "#"} target="_blank" className="text-sm font-medium truncate block hover:underline">
                      {pub.title}
                    </a>
                    <p className="text-xs opacity-50 truncate">
                      {new Date(pub.created_at).toLocaleDateString()} • {(Array.isArray(pub.sites) ? pub.sites[0]?.name : (pub.sites as any)?.name) || 'Unknown Site'}
                    </p>
                  </div>
                </div>
              )) : (
                <p className="text-sm opacity-50 text-center py-4">No recent publications</p>
              )}
           </div>
        </div>
      </div>
    </div>
  );
}
