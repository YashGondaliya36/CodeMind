"use client";

import { useState, useEffect, useRef } from "react";
import { BrutalistButton } from "@/components/ui/BrutalistButton";
import { analyzeRepo, getJobStatus, JobStatus } from "@/lib/api";

interface RepoAnalyzerProps {
  onBundleReady: (repoName: string) => void;
}

function isGitHubUrl(val: string): boolean {
  return /^https?:\/\/(www\.)?github\.com\/.+\/.+/.test(val.trim());
}

function deriveBundleName(val: string): string {
  if (isGitHubUrl(val)) {
    const parts = val.trim().replace(/\.git$/, "").split("/");
    return (parts[parts.length - 1] || "repo").toLowerCase().replace(/[^a-z0-9]/g, "-");
  }
  const parts = val.trim().replace(/\\/g, "/").split("/");
  return (parts[parts.length - 1] || "repo").toLowerCase().replace(/[^a-z0-9]/g, "-");
}

const STATUS_COLORS: Record<string, string> = {
  queued:      "text-gray-400",
  cloning:     "text-blue-400",
  crawling:    "text-purple-400",
  parsing:     "text-yellow-400",
  summarizing: "text-green-400",
  indexing:    "text-orange-400",
  done:        "text-green-400",
  error:       "text-red-400",
};

const STATUS_ICONS: Record<string, string> = {
  queued:      "○",
  cloning:     "⬇",
  crawling:    "◎",
  parsing:     "⟳",
  summarizing: "⚡",
  indexing:    "◈",
  done:        "✓",
  error:       "✗",
};

export function RepoAnalyzer({ onBundleReady }: RepoAnalyzerProps) {
  const [source, setSource] = useState("F:\\Data_Science_Project\\OKF\\backend");
  const [repoName, setRepoName] = useState("codemind-backend");
  const [autoName, setAutoName] = useState(true);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [fastMode, setFastMode] = useState(true);
  const [fileLog, setFileLog] = useState<string[]>([]);
  const logRef = useRef<HTMLDivElement>(null);

  const isRunning = !!(jobId && status?.status !== "done" && status?.status !== "error");
  const isGitHub = isGitHubUrl(source);

  const handleSourceChange = (val: string) => {
    setSource(val);
    if (autoName) {
      const derived = deriveBundleName(val);
      if (derived) setRepoName(derived);
    }
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (jobId && status?.status !== "done" && status?.status !== "error") {
      interval = setInterval(async () => {
        try {
          const updated = await getJobStatus(jobId);
          setStatus(updated);

          if (updated.current_file) {
            setFileLog((prev) => {
              const last = prev[prev.length - 1];
              if (last === updated.current_file) return prev;
              return [...prev.slice(-99), updated.current_file!];
            });
          }

          if (updated.status === "done") {
            onBundleReady(updated.repo_name);
            clearInterval(interval);
          } else if (updated.status === "error") {
            clearInterval(interval);
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 800);
    }
    return () => clearInterval(interval);
  }, [jobId, status?.status, onBundleReady]);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [fileLog]);

  const handleAnalyze = async () => {
    try {
      setStatus(null);
      setFileLog([]);
      const initialJob = await analyzeRepo(source, repoName, fastMode);
      setJobId(initialJob.job_id);
      setStatus(initialJob);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      alert(`Failed to start analysis: ${msg}`);
    }
  };

  const progressPct = status?.progress ?? 0;
  const statusKey = status?.status ?? "queued";

  return (
    <div className="flex flex-col gap-3 font-mono w-full">

      {/* Source Input */}
      <div>
        <label className="block text-[10px] font-bold mb-1 uppercase tracking-widest">
          {isGitHub ? "🐙 GitHub Repository URL" : "📁 Source Path / URL"}
        </label>
        <div className="relative">
          <input
            type="text"
            value={source}
            onChange={(e) => handleSourceChange(e.target.value)}
            placeholder="https://github.com/owner/repo  or  C:\path\to\project"
            className="w-full border-2 border-brutal-black px-3 py-2 bg-brutal-white focus:outline-none focus:bg-yellow-50 text-sm pr-10"
          />
          {isGitHub && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-green-600 font-black text-xs">GH</span>
          )}
        </div>
        {isGitHub && (
          <p className="text-[10px] text-green-700 mt-1 font-bold">
            ✓ GitHub URL detected — will clone automatically
          </p>
        )}
      </div>

      {/* Bundle Name */}
      <div>
        <label className="block text-[10px] font-bold mb-1 uppercase tracking-widest">Bundle Name</label>
        <input
          type="text"
          value={repoName}
          onChange={(e) => { setAutoName(false); setRepoName(e.target.value); }}
          className="w-full border-2 border-brutal-black px-3 py-2 bg-brutal-white focus:outline-none focus:bg-yellow-50 text-sm"
        />
      </div>

      {/* Fast Mode */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="fastMode"
          checked={fastMode}
          onChange={(e) => setFastMode(e.target.checked)}
          className="w-4 h-4 border-2 border-brutal-black accent-brutal-green cursor-pointer"
        />
        <label htmlFor="fastMode" className="text-[11px] font-bold uppercase cursor-pointer">
          Fast Mode (Zero-Cost AST Parsing)
        </label>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2.5">
        <BrutalistButton
          onClick={handleAnalyze}
          variant="orange"
          disabled={isRunning}
          className="flex-1 text-xs md:text-sm"
        >
          {isRunning ? "ANALYZING..." : isGitHub ? "⬇ CLONE & ANALYZE" : "GENERATE NEW"}
        </BrutalistButton>
        <BrutalistButton
          onClick={() => onBundleReady(repoName)}
          variant="acid"
          className="shrink-0 text-xs md:text-sm"
        >
          LOAD EXISTING
        </BrutalistButton>
      </div>

      {/* ── Cinematic Build Screen ── */}
      {status && (
        <div className="border-2 border-brutal-black bg-brutal-black text-white overflow-hidden">

          {/* Header Bar */}
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/10 text-xs">
            <div className="flex items-center gap-2">
              <span className={`font-black ${STATUS_COLORS[statusKey] ?? "text-white"}`}>
                {STATUS_ICONS[statusKey] ?? "○"} {statusKey.toUpperCase()}
              </span>
              {status.total_files > 0 && (
                <span className="text-[10px] text-white/50 font-mono">
                  {status.files_processed}/{status.total_files} FILES
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className={`font-black tabular-nums ${progressPct === 100 ? "text-green-400" : "text-white"}`}>
                {progressPct}%
              </span>
              {(statusKey === "done" || statusKey === "error") && (
                <button
                  onClick={() => setStatus(null)}
                  className="text-[10px] text-white/40 hover:text-white border border-white/20 px-1 rounded ml-1"
                  title="Dismiss build log"
                >
                  ✕
                </button>
              )}
            </div>
          </div>

          {/* Animated Progress Bar */}
          <div className="h-1.5 bg-white/10 w-full">
            <div
              className={`h-full transition-all duration-500 ease-out ${
                statusKey === "error" ? "bg-red-500" :
                statusKey === "done"  ? "bg-green-400" :
                "bg-brutal-orange"
              }`}
              style={{ width: `${progressPct}%` }}
            />
          </div>

          {/* Scrolling File Log */}
          {fileLog.length > 0 && statusKey !== "done" && statusKey !== "error" && (
            <div
              ref={logRef}
              className="h-24 overflow-y-auto px-3 py-2 space-y-0.5"
            >
              {fileLog.map((f, i) => (
                <div
                  key={i}
                  className={`text-[10px] font-mono truncate ${
                    i === fileLog.length - 1
                      ? "text-green-400"
                      : "text-white/30"
                  }`}
                >
                  <span className="mr-1">{i === fileLog.length - 1 ? "▶" : "·"}</span>
                  {f}
                </div>
              ))}
            </div>
          )}

          {/* Done state */}
          {statusKey === "done" && (
            <div className="px-3 py-3 flex items-center gap-4">
              <span className="text-green-400 text-xl font-black">✓ COMPLETE</span>
              <span className="text-white/60 text-[11px]">
                {status.total_files} OKF files generated
              </span>
            </div>
          )}

          {/* Error state */}
          {statusKey === "error" && status.error_detail && (
            <div className="px-3 py-2 text-[10px] text-red-400">
              {status.error_detail}
            </div>
          )}

          {/* Idle message */}
          {fileLog.length === 0 && statusKey !== "done" && statusKey !== "error" && (
            <div className="px-3 py-2 text-[11px] text-white/60 truncate animate-pulse">
              {status.message}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
