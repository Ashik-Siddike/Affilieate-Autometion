import { supabase } from "@/lib/supabase"
import { notFound } from "next/navigation"
import { BotControlPanel } from "@/components/ui/bot-control-panel"
import { ChevronLeftIcon } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

import { SiteSettingsPanel } from "@/components/ui/site-settings-panel"

export default async function SiteDashboardPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  
  const { data: site, error } = await supabase
    .from('sites')
    .select('*')
    .eq('id', id)
    .single();

  if (error || !site) {
    notFound();
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/admin/sites">
            <ChevronLeftIcon className="size-5" />
          </Link>
        </Button>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{site.name} - Dashboard</h2>
          <p className="text-muted-foreground opacity-70">
            Manage configuration and automation jobs for this site.
          </p>
        </div>
      </div>
      
      <div className="space-y-8">
        <SiteSettingsPanel site={site} />
        <BotControlPanel site={site} />
      </div>
    </div>
  );
}
