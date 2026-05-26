import { GlobalSettingsPanel } from "@/components/ui/global-settings-panel";
import { supabase } from "@/lib/supabase";
import { defaultSiteSettings } from "@/types/site";

export default async function SettingsPage() {
  // Fetch global settings
  const { data } = await supabase
    .from('global_settings')
    .select('settings')
    .eq('id', 1)
    .single();

  const settings = data?.settings || defaultSiteSettings;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
      <p className="text-muted-foreground opacity-70">
        Global application settings. These rules will apply to all newly created sites automatically.
      </p>
      
      <GlobalSettingsPanel initialSettings={settings} />
    </div>
  )
}
