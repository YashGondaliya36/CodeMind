import axios from "axios";

// Our FastAPI backend URL
const API_BASE = "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
});

// ── Types ─────────────────────────────────────────────────────────────────

export interface JobStatus {
  job_id: string;
  repo_name: string;
  status: string;
  progress: number;
  message: string;
  files_processed: number;
  total_files: number;
  error_detail: string | null;
  bundle_path: string | null;
}

export interface FileMeta {
  filename: string;
  type: string;
  title: string;
  description: string;
  resource: string;
  tags: string[];
  timestamp: string;
}

export interface BundleFilesResponse {
  repo_name: string;
  total_files: number;
  files: FileMeta[];
}

export interface ChatSource {
  filename: string;
  title: string;
  relevance_score: number;
  tags: string[];
}

export interface ChatResponse {
  answer: string;
  sources_used: ChatSource[];
  files_scanned: number;
  tokens_used: number | null;
  repo_name: string;
  question: string;
}

// ── API Functions ────────────────────────────────────────────────────────

export async function analyzeRepo(sourcePath: string, repoName: string, fastMode: boolean = true) {
  const res = await api.post<JobStatus>("/repo/analyze", {
    source: sourcePath,
    repo_name: repoName,
    languages: ["python", "javascript", "typescript"],
    fast_mode: fastMode
  });
  return res.data;
}

export async function getJobStatus(jobId: string) {
  const res = await api.get<JobStatus>(`/repo/status/${jobId}`);
  return res.data;
}

export async function getBundleFiles(repoName: string) {
  const res = await api.get<BundleFilesResponse>(`/bundle/${repoName}/files`);
  return res.data;
}

export async function getBundleFileContent(repoName: string, filename: string) {
  // It returns the full detail including raw string content
  const res = await api.get(`/bundle/${repoName}/file/${filename}`);
  return res.data;
}

export async function askQuestion(repoName: string, question: string) {
  const res = await api.post<ChatResponse>("/chat/ask", {
    repo_name: repoName,
    question: question,
    max_files: 5
  });
  return res.data;
}
