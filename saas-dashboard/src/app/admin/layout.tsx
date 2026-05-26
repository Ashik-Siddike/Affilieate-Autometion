import ShaderBackground from "@/components/ui/shader-background";
import { AnimatedDock } from "@/components/ui/animated-dock";
import { LayoutDashboard, Settings, Globe, BarChart } from "lucide-react";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen relative overflow-hidden flex flex-col text-white">
      <ShaderBackground />
      
      {/* Top Navbar */}
      <header className="h-16 border-b border-white/10 bg-black/20 backdrop-blur-md flex items-center px-6 sticky top-0 z-50">
        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          Whit Logic SaaS
        </h1>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-6 z-10 overflow-auto pb-32">
        {children}
      </main>

      {/* Bottom Dock Navigation */}
      <div className="fixed bottom-6 left-0 right-0 z-50 pointer-events-none flex justify-center">
        <div className="pointer-events-auto">
          <AnimatedDock
            items={[
              { link: "/admin", Icon: <LayoutDashboard size={22} /> },
              { link: "/admin/sites", Icon: <Globe size={22} /> },
              { link: "/admin/monitor", Icon: <BarChart size={22} /> },
              { link: "/admin/settings", Icon: <Settings size={22} /> },
            ]}
          />
        </div>
      </div>
    </div>
  );
}
