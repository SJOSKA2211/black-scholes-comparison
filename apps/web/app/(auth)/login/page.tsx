"use client";

import { motion } from "framer-motion";
import { Github, Globe, Mail, Lock, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createBrowserClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const supabase = createBrowserClient();

  const handleLogin = async (provider: "github" | "google") => {
    await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/callback`,
      },
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Orbs */}
      <div className="absolute top-1/4 -left-20 w-96 h-96 bg-indigo-600/20 rounded-full blur-[120px] animate-pulse" />
      <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-emerald-600/10 rounded-full blur-[120px] animate-pulse delay-700" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="max-w-md w-full glass-card p-8 rounded-3xl relative z-10"
      >
        <div className="text-center mb-10">
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            className="w-16 h-16 bg-indigo-600/20 rounded-2xl flex items-center justify-center mx-auto mb-6 glow-blue border border-indigo-500/30"
          >
            <Lock className="w-8 h-8 text-indigo-400" />
          </motion.div>
          <h1 className="text-3xl font-bold font-display text-gradient mb-2">Research Portal</h1>
          <p className="text-slate-400">MATH499 Senior Research · UEAB</p>
        </div>

        <div className="space-y-4">
          <Button
            onClick={() => handleLogin("github")}
            className="w-full h-12 bg-slate-800 hover:bg-slate-700 text-white rounded-xl flex items-center justify-center gap-3 transition-all duration-300 border border-slate-700 group"
          >
            <Github className="w-5 h-5" />
            <span>Continue with GitHub</span>
            <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
          </Button>

          <Button
            onClick={() => handleLogin("google")}
            className="w-full h-12 bg-white hover:bg-slate-50 text-slate-900 rounded-xl flex items-center justify-center gap-3 transition-all duration-300 group"
          >
            <Globe className="w-5 h-5" />
            <span>Continue with Google</span>
            <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
          </Button>
        </div>

        <div className="mt-8 pt-8 border-t border-white/5 flex items-center gap-4">
          <div className="flex-1 h-px bg-white/5" />
          <span className="text-xs uppercase tracking-widest text-slate-500 font-medium">or magic link</span>
          <div className="flex-1 h-px bg-white/5" />
        </div>

        <div className="mt-8 space-y-4">
           <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
              <input 
                type="email" 
                placeholder="university-email@ueab.ac.ke"
                className="w-full h-12 bg-slate-950/50 border border-white/10 rounded-xl pl-12 pr-4 focus:ring-2 focus:ring-indigo-500/50 outline-none transition-all placeholder:text-slate-600"
              />
           </div>
           <Button className="w-full h-12 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-lg shadow-indigo-600/20 transition-all active:scale-95">
             Send Magic Link
           </Button>
        </div>

        <p className="mt-8 text-center text-xs text-slate-500 leading-relaxed">
          By continuing, you agree to the research protocol and data privacy terms established for MATH499.
        </p>
      </motion.div>
    </div>
  );
}
