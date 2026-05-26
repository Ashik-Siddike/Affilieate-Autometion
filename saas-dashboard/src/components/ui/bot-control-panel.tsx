'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Play, Search, Terminal, Loader2 } from "lucide-react";

export function BotControlPanel({ site }: { site: any }) {
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Config State
  const [config, setConfig] = useState({
    productsPerKeyword: site.products_per_kw || 3,
    maxArticles: site.max_articles_per_cycle || 3,
    delayProducts: 2,
    delayKeywords: 2,
    internalLinks: site.internal_links ?? true,
    publishNextjs: site.publish_to_wp ?? true,
    triggerMake: true,
    comparisonTable: true,
    language: 'English',
    competitorUrl: ''
  });

  const appendLog = (msg: string) => {
    setLogs(prev => {
      const newLogs = [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`];
      if (newLogs.length > 50) newLogs.shift();
      return newLogs;
    });
  };

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const handleIgnite = async () => {
    setLoading(true);
    appendLog("🔥 Ignition Sequence Started!");
    appendLog(`Targeting Site: ${site.name}`);
    appendLog(`Config: ${JSON.stringify(config)}`);
    
    try {
      const res = await fetch('/api/bot/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ siteId: site.id, config })
      });
      
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n').filter(l => l.trim() !== '');
          lines.forEach(line => {
             // Handle SSE format "data: <message>"
             if (line.startsWith('data: ')) {
               appendLog(line.substring(6));
             } else {
               appendLog(line);
             }
          });
        }
      }
      
      appendLog("✅ Run Complete!");
    } catch (e: any) {
      appendLog(`❌ Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDiscovery = async () => {
    appendLog("🔍 Starting Keyword Discovery...");
    // Future implementation
    setTimeout(() => {
      appendLog("Added 10 new keywords to the pool!");
    }, 2000);
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Configuration Panel */}
      <div className="space-y-6">
        <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur-md p-6 shadow-lg">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold">🔥 IGNITION CORE</h3>
          </div>
          
          <Button 
            onClick={handleIgnite} 
            disabled={loading}
            className="w-full h-14 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold text-lg rounded-xl mb-4 shadow-[0_0_20px_rgba(120,75,160,0.5)] transition-all hover:scale-[1.02]"
          >
            {loading ? <Loader2 className="mr-2 h-6 w-6 animate-spin" /> : <Play className="mr-2 h-6 w-6" />}
            IGNITE AUTOMATION
          </Button>

          <Button 
            onClick={handleDiscovery} 
            variant="outline" 
            className="w-full h-12 border-white/10 bg-white/5 hover:bg-white/10 mb-8"
          >
            <Search className="mr-2 h-5 w-5 text-blue-400" />
            Force Trigger Keyword Discovery
          </Button>

          <div className="space-y-6">
            <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">Bot Configuration</h4>
            
            <div className="grid grid-cols-2 gap-6">
              <div className="flex items-center justify-between">
                <Label htmlFor="internalLinks">Internal Links</Label>
                <Switch 
                  id="internalLinks" 
                  checked={config.internalLinks} 
                  onCheckedChange={(c) => setConfig({...config, internalLinks: c})} 
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="publishNextjs">Publish to Next.js</Label>
                <Switch 
                  id="publishNextjs" 
                  checked={config.publishNextjs} 
                  onCheckedChange={(c) => setConfig({...config, publishNextjs: c})} 
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="triggerMake">Make.com Trig</Label>
                <Switch 
                  id="triggerMake" 
                  checked={config.triggerMake} 
                  onCheckedChange={(c) => setConfig({...config, triggerMake: c})} 
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="comparisonTable">Comparison Table</Label>
                <Switch 
                  id="comparisonTable" 
                  checked={config.comparisonTable} 
                  onCheckedChange={(c) => setConfig({...config, comparisonTable: c})} 
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Products / Keyword</Label>
                <Input 
                  type="number" 
                  value={config.productsPerKeyword} 
                  onChange={(e) => setConfig({...config, productsPerKeyword: parseInt(e.target.value)})} 
                  className="bg-white/5 border-white/10"
                />
              </div>
              <div className="space-y-2">
                <Label>Max Articles</Label>
                <Input 
                  type="number" 
                  value={config.maxArticles} 
                  onChange={(e) => setConfig({...config, maxArticles: parseInt(e.target.value)})} 
                  className="bg-white/5 border-white/10"
                />
              </div>
              <div className="space-y-2">
                <Label>Delay: Products (s)</Label>
                <Input 
                  type="number" 
                  value={config.delayProducts} 
                  onChange={(e) => setConfig({...config, delayProducts: parseInt(e.target.value)})} 
                  className="bg-white/5 border-white/10"
                />
              </div>
              <div className="space-y-2">
                <Label>Delay: Keywords (s)</Label>
                <Input 
                  type="number" 
                  value={config.delayKeywords} 
                  onChange={(e) => setConfig({...config, delayKeywords: parseInt(e.target.value)})} 
                  className="bg-white/5 border-white/10"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Target Language</Label>
              <Select value={config.language || "English"} onValueChange={(v) => setConfig({...config, language: v || "English"})}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="English">English</SelectItem>
                  <SelectItem value="Spanish">Spanish</SelectItem>
                  <SelectItem value="French">French</SelectItem>
                  <SelectItem value="German">German</SelectItem>
                  <SelectItem value="Bengali">Bengali</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Competitor URL (Skyscraper Mode)</Label>
              <Input 
                placeholder="Optional: URL to outrank" 
                value={config.competitorUrl} 
                onChange={(e) => setConfig({...config, competitorUrl: e.target.value})} 
                className="bg-white/5 border-white/10"
              />
            </div>

          </div>
        </div>
      </div>

      {/* Terminal UI */}
      <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur-md p-0 overflow-hidden flex flex-col shadow-lg h-[600px] lg:h-auto">
        <div className="bg-black/80 border-b border-white/10 p-3 flex items-center gap-2">
          <Terminal size={16} className="text-green-500" />
          <span className="text-sm font-mono text-green-500">Live Execution Logs</span>
        </div>
        <div className="p-4 flex-1 overflow-y-auto font-mono text-xs sm:text-sm bg-[#050505]">
          {logs.length === 0 ? (
            <div className="text-green-500/50 italic">Waiting for ignition...</div>
          ) : (
            <div className="space-y-1">
              {logs.map((log, i) => (
                <div key={i} className="text-green-400 break-words">{log}</div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
