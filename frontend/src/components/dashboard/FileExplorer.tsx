"use client";

import { useState, useEffect } from "react";
import { getBundleFiles, getBundleFileContent, FileMeta } from "@/lib/api";
import { BrutalistButton } from "@/components/ui/BrutalistButton";

interface FileExplorerProps {
  repoName: string | null;
}

export function FileExplorer({ repoName }: FileExplorerProps) {
  const [files, setFiles] = useState<FileMeta[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<any>(null);

  useEffect(() => {
    if (!repoName) return;

    const fetchFiles = async () => {
      setLoading(true);
      try {
        const data = await getBundleFiles(repoName);
        setFiles(data.files);
      } catch (e) {
        console.error("Failed to load bundle files", e);
      } finally {
        setLoading(false);
      }
    };

    fetchFiles();
  }, [repoName]);

  const handleFileClick = async (filename: string) => {
    try {
      const data = await getBundleFileContent(repoName!, filename);
      setSelectedFile(data);
    } catch (e) {
      console.error("Failed to load file content", e);
    }
  };

  if (!repoName) {
    return (
      <div className="h-full flex items-center justify-center text-brutal-gray-dark font-mono text-sm p-4 text-center">
        Analyze a repository first to explore its OKF knowledge files.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full font-mono relative">
      <div className="flex justify-between items-center mb-4 shrink-0">
        <h3 className="font-bold text-sm bg-brutal-green px-2 border-2 border-brutal-black">
          BUNDLE: {repoName}
        </h3>
        <span className="text-xs font-bold">{files.length} FILES</span>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">LOADING...</div>
      ) : (
        <div className="flex-1 overflow-y-auto border-3 border-brutal-black bg-brutal-white shadow-brutal p-2 space-y-2">
          {files.map((f) => (
            <div 
              key={f.filename} 
              onClick={() => handleFileClick(f.filename)}
              className="p-3 border-2 border-brutal-black hover:bg-brutal-gray cursor-pointer transition-colors group"
            >
              <div className="flex justify-between items-start mb-1">
                <span className="font-bold text-sm group-hover:underline truncate">{f.title}</span>
                <span className="text-[10px] bg-brutal-black text-brutal-white px-1 ml-2 shrink-0">{f.type.toUpperCase()}</span>
              </div>
              <p className="text-xs text-gray-600 truncate">{f.description}</p>
            </div>
          ))}
        </div>
      )}

      {/* File Reader Modal */}
      {selectedFile && (
        <div className="absolute inset-0 z-50 bg-brutal-white border-3 border-brutal-black shadow-brutal flex flex-col">
          <div className="flex justify-between items-center p-3 border-b-3 border-brutal-black bg-brutal-green">
            <h3 className="font-bold truncate text-sm">{selectedFile.filename}</h3>
            <button 
              onClick={() => setSelectedFile(null)}
              className="font-bold bg-brutal-orange px-2 border-2 border-brutal-black hover:-translate-y-0.5 active:translate-y-0 transition-transform shadow-brutal-sm"
            >
              CLOSE [X]
            </button>
          </div>
          <div className="flex-1 p-6 overflow-auto bg-[#F9F9F9]">
            <pre className="text-xs whitespace-pre-wrap font-mono">
              {selectedFile.content}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
