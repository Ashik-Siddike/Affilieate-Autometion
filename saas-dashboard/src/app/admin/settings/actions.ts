'use server';

import { supabase } from "@/lib/supabase";
import { revalidatePath } from "next/cache";
import { SiteSettings } from "@/types/site";

export async function updateGlobalSettings(settings: SiteSettings) {
  const { error } = await supabase
    .from('global_settings')
    .update({ settings })
    .eq('id', 1);

  if (error) {
    return { error: error.message };
  }
  
  revalidatePath('/admin/settings');
  return { success: true };
}
