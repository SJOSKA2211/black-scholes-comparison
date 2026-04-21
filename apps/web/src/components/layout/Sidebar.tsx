"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { 
  LayoutDashboard, 
  Calculator, 
  FlaskConical, 
  BarChart3, 
  Database, 
  Layers 
} from "lucide-react";

const navItems = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Live Pricer", href: "/pricer", icon: Calculator },
  { name: "Experiments", href: "/experiments", icon: FlaskConical },
  { name: "Validation", href: "/validation", icon: BarChart3 },
  { name: "Scrapers", href: "/scrapers", icon: Database },
  { name: "Methods", href: "/methods", icon: Layers },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/50 p-4">
      <div className="mb-8 flex items-center gap-3 px-2">
        <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold">B</div>
        <span className="font-bold tracking-tight text-white">BS Research</span>
      </div>
      <nav className="space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link key={item.name} href={item.href}>
              <div className={`relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive ? "text-white" : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}>
                {isActive && (
                  <motion.div
                    layoutId="active-nav"
                    className="absolute inset-0 rounded-lg bg-blue-600/10 border-r-2 border-blue-600"
                  />
                )}
                <item.icon className={`h-4 w-4 ${isActive ? "text-blue-500" : ""}`} />
                {item.name}
              </div>
            </Link>
          );
        })}
      </nav>
      <div className="absolute bottom-8 left-4 right-4">
        <div className="rounded-xl bg-slate-800/50 p-4 border border-slate-700/50">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Academic Project</p>
          <p className="mt-1 text-xs text-slate-300">MATH499 Senior Research</p>
          <p className="text-[10px] text-slate-500">UEAB · SJOSKA2211</p>
        </div>
      </div>
    </aside>
  );
}
