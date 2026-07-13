"use client";

import { useState, useEffect } from "react";
import { BrutalistButton } from "@/components/ui/BrutalistButton";
import { askQuestion, ChatResponse, ChatSource } from "@/lib/api";
import ReactMarkdown from "react-markdown";

interface ChatMessage {
  role: "user" | "agent";
  content: string;
  sources?: ChatSource[];
  metrics?: { scanned: number; tokens: number | null };
}

interface ChatInterfaceProps {
  repoName: string | null;
}

export function ChatInterface({ repoName }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Load chat history on mount or repo change
  useEffect(() => {
    if (repoName) {
      const saved = localStorage.getItem(`chat_${repoName}`);
      if (saved) {
        try {
          setMessages(JSON.parse(saved));
        } catch (e) {
          console.error("Failed to parse chat history");
        }
      } else {
        setMessages([]); // Reset for new repo
      }
    }
  }, [repoName]);

  // Save chat history on update
  useEffect(() => {
    if (repoName && messages.length > 0) {
      localStorage.setItem(`chat_${repoName}`, JSON.stringify(messages));
    }
  }, [messages, repoName]);

  const handleSend = async () => {
    if (!input.trim() || !repoName) return;

    const userMessage: ChatMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await askQuestion(repoName, userMessage.content);
      
      const agentMessage: ChatMessage = {
        role: "agent",
        content: response.answer,
        sources: response.sources_used,
        metrics: { scanned: response.files_scanned, tokens: response.tokens_used }
      };
      
      setMessages((prev) => [...prev, agentMessage]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev, 
        { role: "agent", content: `ERROR: Failed to connect to CodeMind agent. ${e.message}` }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!repoName) {
    return (
      <div className="h-full flex items-center justify-center text-brutal-gray-dark font-mono text-sm p-4 text-center border-2 border-dashed border-brutal-black m-4 bg-brutal-white">
        Waiting for active OKF Bundle...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full font-mono bg-brutal-white border-3 border-brutal-black shadow-brutal">
      {/* Input Area (Moved to Top) */}
      <div className="p-4 border-b-3 border-brutal-black bg-brutal-gray flex gap-2 shrink-0">
        <input 
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask a question about the code..."
          className="flex-1 border-3 border-brutal-black px-4 py-3 bg-brutal-white shadow-brutal focus:outline-none focus:bg-yellow-50"
          disabled={isLoading}
        />
        <BrutalistButton 
          variant="orange" 
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          className="px-8"
        >
          SEND
        </BrutalistButton>
      </div>

      {/* Chat History Area (Newest at top) */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {isLoading && (
          <div className="flex justify-start shrink-0">
            <div className="bg-brutal-white border-2 border-brutal-black p-3 text-sm font-bold animate-pulse shadow-brutal-sm">
              AGENT IS THINKING...
            </div>
          </div>
        )}

        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-2 opacity-50">
            <span className="text-4xl">🤖</span>
            <p className="font-bold">AGENT ONLINE</p>
            <p className="text-xs">Ask me anything about the {repoName} codebase.</p>
          </div>
        ) : (
          (() => {
            const pairs = [];
            for (let i = 0; i < messages.length; i++) {
              if (messages[i].role === "user") {
                pairs.push({ user: messages[i], agent: messages[i + 1] });
              }
            }
            return pairs.reverse().map((pair, idx) => (
              <div key={idx} className="flex flex-col gap-4">
                
                {/* USER MESSAGE */}
                <div className="flex flex-col shrink-0 items-end">
                  <div className="max-w-[85%] border-2 border-brutal-black p-3 shadow-brutal-sm bg-brutal-green text-brutal-black">
                    <span className="block text-[10px] font-bold mb-2 uppercase opacity-60">YOU</span>
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{pair.user.content}</p>
                  </div>
                </div>

                {/* AGENT MESSAGE */}
                {pair.agent && (
                  <div className="flex flex-col shrink-0 items-start w-full">
                    <div className="w-full border-2 border-brutal-black p-5 shadow-brutal-sm bg-brutal-gray text-brutal-black">
                      <span className="block text-[10px] font-bold mb-3 uppercase opacity-60">CODEMIND</span>
                      
                      {/* Render Markdown! */}
                      <div className="text-sm leading-relaxed prose prose-sm max-w-none prose-headings:font-black prose-headings:uppercase prose-a:text-brutal-orange prose-a:font-bold prose-code:bg-brutal-white prose-code:px-1 prose-code:border prose-code:border-brutal-black prose-pre:bg-brutal-white prose-pre:text-brutal-black prose-pre:border-2 prose-pre:border-brutal-black">
                        <ReactMarkdown>{pair.agent.content}</ReactMarkdown>
                      </div>
                      
                      {pair.agent.sources && (
                        <div className="mt-4 pt-3 border-t-2 border-brutal-black/20">
                          <div className="flex gap-4 text-[10px] font-bold mb-2 uppercase">
                            <span>FILES SCANNED: {pair.agent.metrics?.scanned || 0}</span>
                            {pair.agent.metrics?.tokens && <span>TOKENS: {pair.agent.metrics.tokens}</span>}
                          </div>
                          {pair.agent.sources.length > 0 && (
                            <div className="space-y-1">
                              <span className="text-[10px] uppercase font-bold">Sources Used:</span>
                              {pair.agent.sources.map((s, sIdx) => (
                                <div key={sIdx} className="bg-brutal-white/50 border border-brutal-black p-1 text-[10px] truncate">
                                  📄 {s.filename} <span className="opacity-50">({Math.round(s.relevance_score * 100)}%)</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
              </div>
            ));
          })()
        )}
      </div>
    </div>
  );
}
