"use client";

import { useState, useEffect, useRef } from "react";
import { BrutalistButton } from "@/components/ui/BrutalistButton";
import { ChatSource } from "@/lib/api";

// ── Minimal GFM-compatible Markdown Renderer ───────────────────────────────────
function MarkdownBlock({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  const inlineFormat = (text: string): React.ReactNode => {
    // Replace **bold**, *italic*, and `code` inline
    const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/);
    return parts.map((part, idx) => {
      if (part.startsWith("**") && part.endsWith("**"))
        return <strong key={idx} className="font-black">{part.slice(2, -2)}</strong>;
      if (part.startsWith("*") && part.endsWith("*"))
        return <em key={idx}>{part.slice(1, -1)}</em>;
      if (part.startsWith("`") && part.endsWith("`"))
        return <code key={idx} className="bg-brutal-white border border-brutal-black px-1 text-[11px] font-mono rounded">{part.slice(1, -1)}</code>;
      return part;
    });
  };

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code block
    if (line.startsWith("```")) {
      const lang = line.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      elements.push(
        <pre key={i} className="bg-brutal-white border-2 border-brutal-black p-3 overflow-x-auto text-[11px] font-mono my-3 rounded">
          <code>{codeLines.join("\n")}</code>
        </pre>
      );
      i++;
      continue;
    }

    // GFM Table: detect separator row (---, :---:, etc.)
    if (i + 1 < lines.length && /^\s*\|?[\s:-]+\|[\s|:-]+$/.test(lines[i + 1])) {
      const headerCells = line.split("|").map(c => c.trim()).filter(c => c);
      const tableRows: string[][] = [];
      i += 2; // skip header + separator
      while (i < lines.length && lines[i].includes("|")) {
        tableRows.push(lines[i].split("|").map(c => c.trim()).filter(c => c));
        i++;
      }
      elements.push(
        <div key={i} className="overflow-x-auto my-4">
          <table className="w-full border-collapse border-2 border-brutal-black text-[12px]">
            <thead>
              <tr className="bg-brutal-black text-white">
                {headerCells.map((h, hi) => (
                  <th key={hi} className="border border-brutal-black/30 px-3 py-1.5 text-left font-black uppercase">{inlineFormat(h)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row, ri) => (
                <tr key={ri} className={ri % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                  {row.map((cell, ci) => (
                    <td key={ci} className="border border-brutal-black/20 px-3 py-1.5">{inlineFormat(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    // Headings
    const hMatch = line.match(/^(#{1,4})\s+(.+)/);
    if (hMatch) {
      const level = hMatch[1].length;
      const text = hMatch[2];
      const cls = ["text-xl", "text-lg", "text-base", "text-sm"][level - 1] + " font-black uppercase mt-4 mb-1";
      elements.push(<div key={i} className={cls}>{inlineFormat(text)}</div>);
      i++;
      continue;
    }

    // Horizontal rule
    if (/^---+$/.test(line.trim())) {
      elements.push(<hr key={i} className="border-brutal-black/30 my-3" />);
      i++;
      continue;
    }

    // Ordered list item
    const olMatch = line.match(/^\d+\.\s+(.+)/);
    if (olMatch) {
      elements.push(<li key={i} className="ml-5 list-decimal mb-0.5">{inlineFormat(olMatch[1])}</li>);
      i++;
      continue;
    }

    // Unordered list item
    const ulMatch = line.match(/^[-*+]\s+(.+)/);
    if (ulMatch) {
      elements.push(<li key={i} className="ml-5 list-disc mb-0.5">{inlineFormat(ulMatch[1])}</li>);
      i++;
      continue;
    }

    // Blockquote
    if (line.startsWith(">")) {
      elements.push(<blockquote key={i} className="border-l-4 border-brutal-black/40 pl-3 italic opacity-80 my-1">{inlineFormat(line.slice(1).trim())}</blockquote>);
      i++;
      continue;
    }

    // Blank line
    if (line.trim() === "") {
      elements.push(<div key={i} className="h-2" />);
      i++;
      continue;
    }

    // Regular paragraph
    elements.push(<p key={i} className="leading-relaxed mb-1">{inlineFormat(line)}</p>);
    i++;
  }

  return <div className="text-sm space-y-0.5">{elements}</div>;
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface AgentEvent {
  type: "routing" | "thinking" | "file_found" | "tool_call" | "tool_result" | "escalating" | "agent_answer" | "done" | "error";
  message?: string;
  tool?: string;
  args?: Record<string, unknown>;
  filename?: string;
  title?: string;
  score?: number;
  found?: boolean;
  step?: number;
  path?: string;
  response?: {
    answer: string;
    sources_used: ChatSource[];
    files_scanned: number;
    tokens_used: number | null;
    tokens_input: number | null;
    tokens_output: number | null;
  };
}

interface ChatMessage {
  role: "user" | "agent";
  content: string;
  sources?: ChatSource[];
  metrics?: { scanned: number; tokens: number | null; tokensIn: number | null; tokensOut: number | null };
  events?: AgentEvent[];
  route?: string;
}

interface ChatInterfaceProps {
  repoName: string | null;
}

// ── Event Icons and Colors ────────────────────────────────────────────────────

const EVENT_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  routing:     { icon: "→", color: "text-blue-600 bg-blue-50 border-blue-300",   label: "ROUTING"   },
  thinking:    { icon: "⟳", color: "text-gray-600 bg-gray-100 border-gray-300",  label: "THINKING"  },
  file_found:  { icon: "◉", color: "text-green-700 bg-green-50 border-green-300",label: "MATCH"     },
  tool_call:   { icon: "⚡", color: "text-orange-700 bg-orange-50 border-orange-300", label: "TOOL" },
  tool_result: { icon: "✓", color: "text-purple-700 bg-purple-50 border-purple-300", label: "RESULT"},
  escalating:  { icon: "↑", color: "text-yellow-700 bg-yellow-50 border-yellow-300", label: "ESCALATE"},
  error:       { icon: "✗", color: "text-red-700 bg-red-100 border-red-300",     label: "ERROR"     },
};

// ── Main Component ────────────────────────────────────────────────────────────

export function ChatInterface({ repoName }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [liveEvents, setLiveEvents] = useState<AgentEvent[]>([]);
  const [expandedEvents, setExpandedEvents] = useState<Set<number>>(new Set());
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load chat history on mount or repo change
  useEffect(() => {
    if (repoName) {
      const saved = localStorage.getItem(`chat_${repoName}`);
      if (saved) {
        try { setMessages(JSON.parse(saved)); } catch { setMessages([]); }
      } else {
        setMessages([]);
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
    if (!input.trim() || !repoName || isLoading) return;
    const question = input.trim();

    const userMessage: ChatMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setLiveEvents([]);

    const eventLog: AgentEvent[] = [];

    try {
      // Build last-3 Q&A history from completed message pairs
      const history = messages
        .reduce((acc: Array<{question: string; answer: string}>, msg, i, arr) => {
          if (msg.role === "user" && arr[i + 1]?.role === "agent") {
            acc.push({ question: msg.content, answer: arr[i + 1].content });
          }
          return acc;
        }, [])
        .slice(-3); // Last 3 turns only

      const response = await fetch("http://localhost:8000/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_name: repoName, question, max_files: 5, conversation_history: history }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const chunk of lines) {
          if (!chunk.startsWith("data: ")) continue;
          try {
            const event: AgentEvent = JSON.parse(chunk.slice(6));
            eventLog.push(event);
            setLiveEvents([...eventLog]);

            if (event.type === "done" && event.response) {
              const agentMessage: ChatMessage = {
                role: "agent",
                content: event.response.answer,
                sources: event.response.sources_used,
                metrics: {
                  scanned: event.response.files_scanned,
                  tokens: event.response.tokens_used,
                  tokensIn: event.response.tokens_input ?? null,
                  tokensOut: event.response.tokens_output ?? null,
                },
                events: [...eventLog],
                route: eventLog.find(e => e.type === "routing")?.path,
              };
              setMessages((prev) => [...prev, agentMessage]);
              setLiveEvents([]);
              setIsLoading(false);
              return;
            }
          } catch {}
        }
      }
    } catch (e: unknown) {
      const errMsg = e instanceof Error ? e.message : String(e);
      setMessages((prev) => [...prev, {
        role: "agent",
        content: `ERROR: Could not connect to CodeMind agent. ${errMsg}`,
      }]);
    } finally {
      setIsLoading(false);
      setLiveEvents([]);
    }
  };

  const toggleEvents = (idx: number) => {
    setExpandedEvents((prev) => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  if (!repoName) {
    return (
      <div className="h-full flex items-center justify-center text-brutal-gray-dark font-mono text-sm p-4 text-center border-2 border-dashed border-brutal-black m-4 bg-brutal-white">
        Waiting for active OKF Bundle...
      </div>
    );
  }

  // Build pairs (user + agent)
  const pairs: { user: ChatMessage; agent?: ChatMessage }[] = [];
  for (let i = 0; i < messages.length; i++) {
    if (messages[i].role === "user") {
      pairs.push({ user: messages[i], agent: messages[i + 1] });
    }
  }

  return (
    <div className="flex flex-col h-full font-mono bg-brutal-white border-3 border-brutal-black shadow-brutal">
      {/* Input Area */}
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

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-6">

        {/* Live Agent Thinking Panel */}
        {isLoading && (
          <div className="border-3 border-brutal-black shadow-brutal bg-white shrink-0">
            <div className="px-4 py-2 bg-brutal-black text-white text-[10px] font-bold uppercase flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              AGENT REASONING — LIVE
            </div>
            <div className="p-3 flex flex-col gap-1 max-h-64 overflow-y-auto">
              {liveEvents.length === 0 && (
                <div className="text-xs text-gray-400 animate-pulse">Classifying query...</div>
              )}
              {liveEvents.map((evt, i) => {
                const cfg = EVENT_CONFIG[evt.type] || EVENT_CONFIG.thinking;
                return (
                  <div key={i} className={`flex items-start gap-2 text-[11px] font-mono border px-2 py-1 rounded ${cfg.color}`}>
                    <span className="font-bold shrink-0 w-4">{cfg.icon}</span>
                    <span className="font-bold shrink-0 w-16 opacity-70">{cfg.label}</span>
                    <span className="flex-1">{evt.message}</span>
                    {evt.step && <span className="opacity-40 shrink-0">#{evt.step}</span>}
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>
          </div>
        )}

        {/* Message History */}
        {pairs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-2 opacity-50">
            <span className="text-4xl">*</span>
            <p className="font-bold">AGENT ONLINE</p>
            <p className="text-xs">Ask me anything about the {repoName} codebase.</p>
          </div>
        ) : (
          pairs.slice().reverse().map((pair, idx) => (
            <div key={idx} className="flex flex-col gap-4">

              {/* USER BUBBLE */}
              <div className="flex flex-col shrink-0 items-end">
                <div className="max-w-[85%] border-2 border-brutal-black p-3 shadow-brutal-sm bg-brutal-green text-brutal-black">
                  <span className="block text-[10px] font-bold mb-2 uppercase opacity-60">YOU</span>
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{pair.user.content}</p>
                </div>
              </div>

              {/* AGENT BUBBLE */}
              {pair.agent && (
                <div className="flex flex-col shrink-0 items-start w-full">
                  <div className="w-full border-2 border-brutal-black shadow-brutal-sm bg-brutal-gray text-brutal-black">

                    {/* Header */}
                    <div className="px-5 pt-4 pb-2 flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase opacity-60">CODEMIND</span>
                      {pair.agent.route && (
                        <span className={`text-[9px] font-bold uppercase px-2 py-0.5 border ${
                          pair.agent.route === "agentic"
                            ? "bg-orange-100 border-orange-400 text-orange-700"
                            : pair.agent.route === "direct"
                            ? "bg-blue-100 border-blue-400 text-blue-700"
                            : "bg-gray-100 border-gray-400 text-gray-600"
                        }`}>
                          {pair.agent.route === "agentic" ? "AGENT LOOP" : pair.agent.route === "direct" ? "DIRECT" : "RAG"}
                        </span>
                      )}
                    </div>

                    {/* Agent Thinking Trail — Collapsible (shown ABOVE the answer) */}
                    {pair.agent.events && pair.agent.events.filter(e => e.type !== "done").length > 0 && (
                      <div className="mx-5 mb-3 border border-brutal-black/20">
                        <button
                          onClick={() => toggleEvents(idx)}
                          className="text-[10px] font-bold uppercase px-3 py-2 w-full text-left bg-brutal-black/5 hover:bg-brutal-black/10 transition-colors flex items-center gap-1"
                        >
                          {expandedEvents.has(idx) ? "▾" : "▸"} AGENT TRACE ({pair.agent.events.filter(e => e.type !== "done").length} steps)
                        </button>
                        {expandedEvents.has(idx) && (
                          <div className="flex flex-col gap-1 p-2">
                            {pair.agent.events.filter(e => e.type !== "done").map((evt, eIdx) => {
                              const cfg = EVENT_CONFIG[evt.type] || EVENT_CONFIG.thinking;
                              return (
                                <div key={eIdx} className={`flex items-start gap-2 text-[10px] font-mono border px-2 py-1 rounded ${cfg.color}`}>
                                  <span className="font-bold shrink-0 w-3">{cfg.icon}</span>
                                  <span className="font-bold shrink-0 w-14 opacity-70">{cfg.label}</span>
                                  <span className="flex-1 opacity-90">{evt.message}</span>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Answer */}
                    <div className="px-5 pb-4">
                      <MarkdownBlock content={pair.agent.content} />
                    </div>

                    {/* Sources Only */}
                    {pair.agent.sources && pair.agent.sources.length > 0 && (
                      <div className="px-5 pb-4 border-t-2 border-brutal-black/20 pt-3">
                        <div className="space-y-1">
                          <span className="text-[10px] uppercase font-bold">Sources Used:</span>
                          {pair.agent.sources.map((s, sIdx) => (
                            <div key={sIdx} className="bg-brutal-white/50 border border-brutal-black p-1 text-[10px] truncate">
                              [{s.filename}] <span className="opacity-50">({Math.round(s.relevance_score * 100)}%)</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Metrics Footer for this Bubble */}
                    {pair.agent.metrics && (
                      <div className="px-5 py-2 border-t-2 border-brutal-black bg-brutal-black text-white flex items-center flex-wrap gap-x-6 gap-y-2 text-[10px] font-bold uppercase">
                        <span className="flex items-center gap-1">
                          <span className="opacity-60">FILES SCANNED</span>
                          <span className="text-brutal-green">{pair.agent.metrics.scanned}</span>
                        </span>
                        {pair.agent.metrics.tokensIn != null && (
                          <span className="flex items-center gap-1">
                            <span className="opacity-60">IN</span>
                            <span className="text-cyan-400">{pair.agent.metrics.tokensIn.toLocaleString()}</span>
                          </span>
                        )}
                        {pair.agent.metrics.tokensOut != null && (
                          <span className="flex items-center gap-1">
                            <span className="opacity-60">OUT</span>
                            <span className="text-yellow-400">{pair.agent.metrics.tokensOut.toLocaleString()}</span>
                          </span>
                        )}
                        {pair.agent.metrics.tokensIn == null && pair.agent.metrics.tokens && (
                          <span className="flex items-center gap-1">
                            <span className="opacity-60">TOKENS</span>
                            <span className="text-yellow-400">{pair.agent.metrics.tokens.toLocaleString()}</span>
                          </span>
                        )}
                      </div>
                    )}

                  </div>
                </div>
              )}

            </div>
          ))
        )}
      </div>
    </div>
  );
}
