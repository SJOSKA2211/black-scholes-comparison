"use client";

import React, { useState } from "react";
import { createBrowserClient } from "@/lib/supabase/client";
import { motion } from "framer-motion";
import {
  Github,
  Mail,
  ArrowRight,
  Activity,
  TrendingUp,
  ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const supabase = createBrowserClient();

  const handleGithubLogin = async () => {
    setLoading(true);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "github",
        options: {
          redirectTo: `${window.location.origin}/callback`,
        },
      });
      if (error) throw error;
    } catch (err: any) {
      toast.error(err.message || "Auth failed");
      setLoading(false);
    }
  };

  const handleMagicLink = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    const email = (
      e.currentTarget.elements.namedItem("email") as HTMLInputElement
    ).value;

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/callback`,
        },
      });
      if (error) throw error;
      toast.success("Magic link sent! Check your inbox.");
    } catch (err: any) {
      toast.error(err.message || "Failed to send link");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4">
      {/* Background Glows */}
      <div className="absolute top-1/4 -left-20 h-96 w-96 rounded-full bg-blue-600/20 blur-[120px] animate-pulse" />
      <div className="absolute bottom-1/4 -right-20 h-96 w-96 rounded-full bg-purple-600/10 blur-[120px] animate-pulse delay-700" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="glass-card relative w-full max-w-md overflow-hidden p-8"
      >
        <div className="relative z-10 space-y-8">
          {/* Header */}
          <div className="text-center space-y-2">
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              className="inline-flex items-center justify-center p-3 rounded-2xl bg-blue-500/10 border border-blue-500/20 mb-4"
            >
              <TrendingUp className="w-8 h-8 text-blue-400" />
            </motion.div>
            <h1 className="text-3xl font-bold tracking-tight text-white font-outfit">
              Research <span className="text-gradient">Platform</span>
            </h1>
            <p className="text-slate-400 text-sm">
              Black-Scholes Numerical Comparison · MATH499
            </p>
          </div>

          {/* Social Auth */}
          <div className="space-y-4">
            <button
              onClick={handleGithubLogin}
              disabled={loading}
              className="group relative flex w-full items-center justify-center gap-3 rounded-xl bg-white/5 border border-white/10 p-3.5 text-sm font-medium text-white transition-all hover:bg-white/10 hover:border-white/20 disabled:opacity-50"
            >
              <Github className="w-5 h-5" />
              Continue with GitHub
              <ArrowRight className="w-4 h-4 opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0" />
            </button>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-white/5" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-slate-950 px-3 text-slate-500">
                Or continue with email
              </span>
            </div>
          </div>

          {/* Email Auth */}
          <form onSubmit={handleMagicLink} className="space-y-4">
            <div className="space-y-2">
              <div className="relative">
                <Mail className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
                <input
                  name="email"
                  type="email"
                  placeholder="name@example.com"
                  required
                  disabled={loading}
                  className="w-full rounded-xl bg-white/5 border border-white/10 p-3 pl-10 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-blue-600 p-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition-all hover:bg-blue-500 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
            >
              {loading ? "Sending link..." : "Send Magic Link"}
            </button>
          </form>

          {/* Footer Features */}
          <div className="grid grid-cols-3 gap-2 pt-4">
            <div className="flex flex-col items-center gap-1">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
                Realtime
              </span>
            </div>
            <div className="flex flex-col items-center gap-1">
              <TrendingUp className="w-4 h-4 text-blue-400" />
              <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
                Live Data
              </span>
            </div>
            <div className="flex flex-col items-center gap-1">
              <ShieldCheck className="w-4 h-4 text-purple-400" />
              <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
                Secure
              </span>
            </div>
          </div>
        </div>

        {/* Decorative corner element */}
        <div className="absolute -top-10 -right-10 h-32 w-32 bg-blue-500/10 rounded-full blur-2xl" />
      </motion.div>
    </div>
  );
}
