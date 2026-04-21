"use client";
import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { 
  LayoutDashboard, 
  Calculator, 
  FlaskConical, 
  TrendingUp, 
  Database, 
  BookOpen,
  Settings
} from "lucide-react";
import { cn } from "@/lib/utils";

const menuItems = [
  { name: "Overview", icon: LayoutDashboard, href: "/" },
  { name: "Live Pricer", icon: Calculator, href: "/pricer" },
  { name: "Experiments", icon: FlaskConical, href: "/experiments" },
  { name: "Validation", icon: TrendingUp, href: "/validation" },
  { name: "Scrapers", icon: Database, href: "/scrapers" },
  { name: "Methods Guide", icon: BookOpen, href: "/methods" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-800 flex flex-col bg-slate-900/50 backdrop-blur-xl">
      <div className="p-6">
        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          Black-Scholes
        </h1>
        <p className="text-xs text-slate-500 mt-1">Research Platform</p>
      </div>

      <nav className="flex-1 px-4 space-y-1">
        {menuItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link key={item.name} href={item.href}>
              <div className={cn(
                "group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-all relative",
                isActive 
                  ? "text-white bg-blue-600/10" 
                  : "text-slate-400 hover:text-white hover:bg-slate-800"
              )}>
                {isActive && (
                  <motion.div 
                    layoutId="active-pill"
                    className="absolute left-0 w-1 h-6 bg-blue-500 rounded-full"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                <item.icon className={cn(
                  "mr-3 h-5 w-5 transition-colors",
                  isActive ? "text-blue-400" : "group-hover:text-white"
                )} />
                {item.name}
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <Link href="/settings">
          <div className="flex items-center px-3 py-2 text-sm font-medium text-slate-400 rounded-lg hover:text-white hover:bg-slate-800">
            <Settings className="mr-3 h-5 w-5" />
            Settings
          </div>
        </Link>
      </div>
    </aside>
  );
}
