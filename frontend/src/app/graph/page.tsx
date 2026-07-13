import { GraphView } from "@/components/graph/GraphView";

export default function GraphPage({ searchParams }: { searchParams: { repo?: string } }) {
  const repoName = searchParams.repo || null;

  return (
    <main className="min-h-screen p-8 max-w-[1600px] mx-auto flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-5xl font-black uppercase tracking-tighter">Knowledge Graph</h1>
          <p className="font-mono mt-2 font-bold bg-brutal-orange inline-block px-2 py-1 border-2 border-brutal-black">
            BUNDLE: {repoName || "NONE"}
          </p>
        </div>
        <a 
          href={repoName ? `/?repo=${repoName}` : "/"}
          className="font-mono font-bold bg-brutal-white px-6 py-3 border-3 border-brutal-black shadow-brutal hover:-translate-y-1 hover:shadow-brutal-lg active:translate-y-1 active:shadow-brutal-hover transition-all"
        >
          &larr; BACK TO DASHBOARD
        </a>
      </header>

      <GraphView repoName={repoName} />
    </main>
  );
}
