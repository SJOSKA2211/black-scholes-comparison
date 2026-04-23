"use client";
import { motion } from "framer-motion";
import { createBrowserClient } from "@/lib/supabase/client";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Github, Mail, LineChart, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

function LoginContent() {
  const searchParams = useSearchParams();
  const errorParam = searchParams.get("error");
  const supabase = createBrowserClient();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const signInWithGitHub = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "github",
      options: { redirectTo: `${window.location.origin}/callback` },
    });
  };

  const signInWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/callback` },
    });
  };

  const sendMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/callback` },
    });
    setSent(true);
    setLoading(false);
  };

  const containerVariants: any = {
    hidden: { opacity: 0, y: 24 },
    visible: { opacity: 1, y: 0, transition: { staggerChildren: 0.05, duration: 0.4, ease: "easeOut" } },
  };

  const itemVariants: any = {
    hidden: { opacity: 0, y: 16 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-6">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(37,99,235,0.1),transparent_50%)]" />
      
      <motion.div 
        variants={containerVariants} 
        initial="hidden" 
        animate="visible"
        className="w-full max-w-md relative"
      >
        <motion.div variants={itemVariants} className="flex justify-center mb-8">
           <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-500/40">
             <LineChart className="w-8 h-8 text-white" />
           </div>
        </motion.div>

        <motion.div variants={itemVariants} className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-3xl p-8 shadow-2xl">
          <div className="text-center mb-10">
            <h1 className="text-2xl font-black text-white tracking-tight mb-2">Research Platform</h1>
            <p className="text-slate-500 text-sm">Numerical methods for option pricing · MATH499</p>
          </div>

          {errorParam === "auth_failed" && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-red-400 text-xs"
            >
              <AlertCircle className="w-4 h-4 shrink-0" />
              <p>Authentication failed. Please ensure your Supabase keys in <code className="bg-red-500/20 px-1 rounded">.env.local</code> are valid and GitHub OAuth is configured.</p>
            </motion.div>
          )}

          <div className="space-y-4">
            <Button 
              variant="outline" 
              className="w-full h-12 gap-3" 
              onClick={signInWithGitHub}
            >
              <Github className="w-5 h-5" />
              Continue with GitHub
            </Button>
            
            <Button 
              variant="outline" 
              className="w-full h-12 gap-3" 
              onClick={signInWithGoogle}
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
            </Button>
          </div>

          <div className="relative my-10">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-800"></div></div>
            <div className="relative flex justify-center text-xs uppercase"><span className="bg-slate-900 px-4 text-slate-500 font-bold tracking-widest">Or Magic Link</span></div>
          </div>

          {!sent ? (
            <form onSubmit={sendMagicLink} className="space-y-4">
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-600" />
                <input 
                  type="email" 
                  placeholder="Enter your email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full h-12 pl-12 pr-4 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-all"
                />
              </div>
              <Button 
                type="submit" 
                disabled={loading}
                className="w-full h-12"
              >
                {loading ? "Sending..." : "Send Magic Link"}
              </Button>
            </form>
          ) : (
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center p-6 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl"
            >
              <h3 className="text-emerald-400 font-bold mb-2">Check your inbox</h3>
              <p className="text-slate-400 text-xs">We&apos;ve sent a magic link to {email}.</p>
            </motion.div>
          )}
        </motion.div>
 
        <motion.p variants={itemVariants} className="text-center mt-8 text-xs text-slate-600">
          By continuing, you agree to the Research Platform&apos;s terms of service and methodology guidelines.
        </motion.p>
      </motion.div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950" />}>
      <LoginContent />
    </Suspense>
  );
}
