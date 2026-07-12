"use client";
import { useState } from "react";
import { BrutalistCard, BrutalistCardContent, BrutalistCardHeader, BrutalistCardTitle } from "@/components/ui/BrutalistCard"
import { RepoAnalyzer } from "@/components/dashboard/RepoAnalyzer"
import { FileExplorer } from "@/components/dashboard/FileExplorer"
import { ChatInterface } from "@/components/dashboard/ChatInterface"

export default function Dashboard() {
  const [activeRepo, setActiveRepo] = useState<string | null>(null);

  return (
    <main className="min-h-screen p-8 max-w-[1600px] mx-auto">
      
      {/* HEADER SECTION */}
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-5xl font-black uppercase tracking-tighter">CodeMind</h1>
          <p className="font-mono mt-2 font-bold bg-brutal-green inline-block px-2 py-1 border-2 border-brutal-black">
            OKF GENERATOR & BROWSER v1.0
          </p>
        </div>
        <div className="text-right font-mono font-bold">
          <p>STATUS: <span className="text-brutal-green drop-shadow-[1px_1px_0_black]">ONLINE</span></p>
          <p>SYSTEM: NOMINAL</p>
        </div>
      </header>

      {/* MAIN GRID */}
      <div className="grid grid-cols-12 gap-8 h-[80vh]">
        
        {/* LEFT COLUMN: Repo Analysis & File Explorer (4 columns) */}
        <div className="col-span-4 flex flex-col gap-8 h-full">
          
          <BrutalistCard className="shrink-0">
            <BrutalistCardHeader>
              <BrutalistCardTitle>1. ANALYZE REPO</BrutalistCardTitle>
            </BrutalistCardHeader>
            <BrutalistCardContent className="pt-6">
              <p className="font-mono text-sm mb-4">Input a path to generate an OKF bundle.</p>
              <RepoAnalyzer onBundleReady={(repo) => setActiveRepo(repo)} />
            </BrutalistCardContent>
          </BrutalistCard>

          <BrutalistCard className="flex-1 flex flex-col min-h-0">
            <BrutalistCardHeader>
              <BrutalistCardTitle>2. OKF BUNDLE</BrutalistCardTitle>
            </BrutalistCardHeader>
            <BrutalistCardContent className="pt-6 flex-1 overflow-auto">
              <FileExplorer repoName={activeRepo} />
            </BrutalistCardContent>
          </BrutalistCard>

        </div>

        {/* RIGHT COLUMN: Graph & Chat (8 columns) */}
        <div className="col-span-8 flex flex-col gap-8 h-full">
          
          <BrutalistCard className="h-full flex flex-col">
            <BrutalistCardHeader className="flex flex-row items-center justify-between">
              <BrutalistCardTitle>3. CODEMIND AGENT</BrutalistCardTitle>
              {activeRepo && (
                <a 
                  href={`/graph?repo=${activeRepo}`}
                  className="font-mono text-xs bg-brutal-orange px-3 py-1 border-2 border-black font-bold hover:bg-brutal-white transition-colors"
                >
                  OPEN KNOWLEDGE GRAPH &rarr;
                </a>
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
