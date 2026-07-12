"use client";

import { useState, useEffect } from "react";
import { BrutalistButton } from "@/components/ui/BrutalistButton";
import { analyzeRepo, getJobStatus, JobStatus } from "@/lib/api";

interface RepoAnalyzerProps {
  onBundleReady: (repoName: string) => void;
}

export function RepoAnalyzer({ onBundleReady }: RepoAnalyzerProps) {
  const [sourcePath, setSourcePath] = useState("F:\\Data_Science_Project\\OKF\\backend");
  const [repoName, setRepoName] = useState("codemind-backend");
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);

  // Poll status while job is active
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (jobId && status?.status !== "done" && status?.status !== "error") {
      interval = setInterval(async () => {
        try {
          const updated = await getJobStatus(jobId);
          setStatus(updated);
          
          if (updated.status === "done") {
            onBundleReady(updated.repo_name);
            clearInterval(interval);
          } else if (updated.status === "error") {
            clearInterval(interval);
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 2000);
    }
    
    return () => clearInterval(interval);
  }, [jobId, status?.status, onBundleReady]);

  const handleAnalyze = async () => {
    try {
      setStatus(null); // reset
      const initialJob = await analyzeRepo(sourcePath, repoName);
      setJobId(initialJob.job_id);
      setStatus(initialJob);
    } catch (e: any) {
      alert(`Failed to start analysis: ${e.message}`);
    }
  };

  return (
    <div className="flex flex-col gap-4 font-mono w-full">
      <div className="flex gap-4">
        <div className="flex-1">
          <label className="block text-xs font-bold mb-1 uppercase">Source Path / URL</label>
          <input 
            type="text" 
            value={sourcePath}
            onChange={(e) => setSourcePath(e.target.value)}
            className="w-full border-3 border-brutal-black px-3 py-2 bg-brutal-white shadow-brutal focus:outline-none focus:bg-yellow-50"
          />
        </div>
        <div>
          <label className="block text-xs font-bold mb-1 uppercase">Bundle Name</label>
          <input 
            type="text" 
            value={repoName}
            onChange={(e) => setRepoName(e.target.value)}
            className="w-full border-3 border-brutal-black px-3 py-2 bg-brutal-white shadow-brutal focus:outline-none focus:bg-yellow-50"
          />
        </div>
      </div>
      
      <div className="flex gap-4">
        <BrutalistButton 
          onClick={handleAnalyze} 
          variant="orange" 
          disabled={!!(jobId && status?.status !== "done" && status?.status !== "error")}
          className="flex-1"
        >
          {status && status.status !== "done" && status.status !== "error" 
            ? "ANALYZING..." 
            : "GENERATE NEW"}
        </BrutalistButton>
        
        <BrutalistButton 
          onClick={() => onBundleReady(repoName)} 
          variant="acid" 
          className="shrink-0"
        >
          LOAD EXISTING
        </BrutalistButton>
      </div>

      {/* Progress Bar Area */}
      {status && (
        <div className="mt-2 border-3 border-brutal-black p-4 bg-brutal-white shadow-brutal">
          <div className="flex justify-between text-xs font-bold mb-2">
            <span>STATUS: {status.status.toUpperCase()}</span>
            <span>{status.progress}%</span>
          </div>
          
          <div className="w-full h-4 border-2 border-brutal-black bg-brutal-gray overflow-hidden">
            <div 
              className="h-full bg-brutal-green border-r-2 border-brutal-black transition-all duration-500 ease-out"
              style={{ width: `${status.progress}%` }}
            />
          </div>
          
          <p className="text-xs mt-2 truncate">
            {status.message}
            {status.total_files > 0 && ` (${status.files_processed}/${status.total_files})`}
          </p>

          {status.error_detail && (
            <p className="text-xs mt-2 text-red-600 bg-red-100 p-2 border-2 border-red-600">
              {status.error_detail}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
