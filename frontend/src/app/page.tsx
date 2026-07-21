"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { BrutalistCard, BrutalistCardContent, BrutalistCardHeader, BrutalistCardTitle } from "@/components/ui/BrutalistCard"
import { RepoAnalyzer } from "@/components/dashboard/RepoAnalyzer"
import { FileExplorer } from "@/components/dashboard/FileExplorer"
import { ChatInterface } from "@/components/dashboard/ChatInterface"
import Link from "next/link";

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const repoFromUrl = searchParams.get("repo");

  const [activeRepo, setActiveRepo] = useState<string | null>(repoFromUrl);

  // Sync state to URL without reloading
  useEffect(() => {
    if (activeRepo && activeRepo !== repoFromUrl) {
      router.replace(`/?repo=${activeRepo}`);
    }
  }, [activeRepo, repoFromUrl, router]);

  return (
    <main className="h-screen p-4 md:p-6 max-w-[1700px] mx-auto flex flex-col overflow-hidden">
      
      {/* HEADER SECTION */}
      <header className="shrink-0 mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-4xl md:text-5xl font-black uppercase tracking-tighter">CodeMind</h1>
          <p className="font-mono mt-1 font-bold bg-brutal-green inline-block px-2 py-1 border-2 border-brutal-black text-xs md:text-sm">
            OKF GENERATOR & BROWSER v1.0
          </p>
        </div>
        <div className="text-right font-mono font-bold text-xs md:text-base">
          <p>STATUS: <span className="text-brutal-green drop-shadow-[1px_1px_0_black]">ONLINE</span></p>
          <p>SYSTEM: NOMINAL</p>
        </div>
      </header>

      {/* MAIN GRID — Balanced 4-col (34%) / 8-col (66%) split at max-w 1700px */}
      <div className="flex-1 grid grid-cols-12 gap-4 md:gap-6 min-h-0">
        
        {/* LEFT COLUMN: Repo Analysis & File Explorer (4 columns) */}
        <div className="col-span-12 lg:col-span-4 xl:col-span-4 flex flex-col gap-4 h-full min-h-0">
          
          <BrutalistCard className="shrink-0 max-h-[52%] flex flex-col min-h-0">
            <BrutalistCardHeader className="py-2.5 px-4 shrink-0">
              <BrutalistCardTitle className="text-base">1. ANALYZE REPO</BrutalistCardTitle>
            </BrutalistCardHeader>
            <BrutalistCardContent className="p-4 pt-3 overflow-y-auto">
              <p className="font-mono text-xs mb-3 text-brutal-black/70">
                Paste a <span className="font-black">GitHub URL</span> or local path to generate an OKF knowledge bundle.
              </p>
              <RepoAnalyzer onBundleReady={(repo) => setActiveRepo(repo)} />
            </BrutalistCardContent>
          </BrutalistCard>

          <BrutalistCard className="flex-1 flex flex-col min-h-[220px] overflow-hidden">
            <BrutalistCardHeader className="py-2.5 px-4 shrink-0">
              <BrutalistCardTitle className="text-base">2. OKF BUNDLE</BrutalistCardTitle>
            </BrutalistCardHeader>
            <BrutalistCardContent className="p-4 pt-3 flex-1 overflow-hidden flex flex-col">
              <FileExplorer repoName={activeRepo} />
            </BrutalistCardContent>
          </BrutalistCard>

        </div>

        {/* RIGHT COLUMN: Graph & Chat (8 columns) */}
        <div className="col-span-12 lg:col-span-8 xl:col-span-8 flex flex-col gap-4 h-full min-h-0">
          
          <BrutalistCard className="h-full flex flex-col">
            <BrutalistCardHeader className="flex flex-row items-center justify-between">
              <BrutalistCardTitle>3. CODEMIND AGENT</BrutalistCardTitle>
              {activeRepo && (
                <Link 
                  href={`/graph?repo=${activeRepo}`}
                  className="font-mono text-xs bg-brutal-orange px-3 py-1 border-2 border-black font-bold hover:bg-brutal-white transition-colors"
                >
                  OPEN KNOWLEDGE GRAPH &rarr;
                </Link>
              )}
            </BrutalistCardHeader>
            <BrutalistCardContent className="flex-1 pt-6 overflow-hidden">
              <ChatInterface repoName={activeRepo} />
            </BrutalistCardContent>
          </BrutalistCard>

        </div>

      </div>
    </main>
  )
}

export default function Dashboard() {
  return (
    <Suspense fallback={<div className="min-h-screen p-8 max-w-[1600px] mx-auto font-mono text-xl">Loading CodeMind...</div>}>
      <DashboardContent />
    </Suspense>
  )
}
