'use client';

import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Trash2, Loader2 } from "lucide-react";
import { deleteSite } from "@/app/admin/sites/actions";

export function DeleteSiteButton({ siteId }: { siteId: string }) {
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    if (confirm("Are you sure you want to delete this site? This action cannot be undone.")) {
      setLoading(true);
      await deleteSite(siteId);
      setLoading(false);
    }
  };

  return (
    <Button 
      variant="ghost" 
      size="icon" 
      className="h-8 w-8 -mr-2 text-red-500 hover:text-red-600 hover:bg-red-500/10"
      onClick={handleDelete}
      disabled={loading}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 size={16} />}
    </Button>
  );
}
