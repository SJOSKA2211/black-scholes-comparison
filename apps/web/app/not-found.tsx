import Link from "next/link";
import { SearchX } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-950 text-center px-4">
      <div className="mb-8 rounded-3xl bg-blue-500/10 p-6 border border-blue-500/20 shadow-2xl shadow-blue-500/10">
        <SearchX className="h-16 w-16 text-blue-500" />
      </div>
      <h1 className="text-6xl font-black text-white tracking-tighter mb-4">404</h1>
      <h2 className="text-2xl font-bold text-slate-200 mb-6">Algorithm Not Found</h2>
      <p className="max-w-md text-slate-500 mb-10 leading-relaxed">
        The research path you are looking for does not exist or has been moved to a different coordinate.
      </p>
      <Link href="/">
        <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-xl transition-all shadow-lg shadow-blue-600/20">
          Return to Dashboard
        </button>
      </Link>
    </div>
  );
}
