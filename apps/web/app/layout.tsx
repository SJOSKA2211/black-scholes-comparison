import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata: Metadata = {
  title: "Black-Scholes Research Platform | SJOSKA2211",
  description: "Advanced numerical methods research platform for option pricing. FDM, Monte Carlo, and Binomial Trees.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${outfit.variable} font-sans antialiased bg-slate-950 text-slate-50 min-h-screen selection:bg-indigo-500/30`}>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
