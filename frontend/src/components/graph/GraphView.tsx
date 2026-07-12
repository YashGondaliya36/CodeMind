"use client";

import { useEffect, useState } from "react";
import ReactFlow, { Background, Controls, Node, Edge, MarkerType } from "reactflow";
import "reactflow/dist/style.css";
import { getBundleFileContent } from "@/lib/api";

interface GraphViewProps {
  repoName: string | null;
}

export function GraphView({ repoName }: GraphViewProps) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!repoName) return;

    const fetchGraph = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await getBundleFileContent(repoName, "graph.json");
        
        let data;
        try {
            // Try to parse it. It might be in response.content, response.raw, or already parsed
            const rawString = response.content || response.raw || response;
            data = typeof rawString === "string" ? JSON.parse(rawString) : rawString;
        } catch (parseError: any) {
            throw new Error(`Failed to parse graph JSON: ${parseError.message}`);
        }

        // Calculate Hierarchical Flowchart Layout
        const nodeLevels: Record<string, number> = {};
        const incomingEdges: Record<string, number> = {};
        const adjList: Record<string, string[]> = {};

        data.nodes.forEach((n: any) => {
            incomingEdges[n.id] = 0;
            adjList[n.id] = [];
        });

        data.edges.forEach((e: any) => {
            if (adjList[e.source]) adjList[e.source].push(e.target);
            if (incomingEdges[e.target] !== undefined) incomingEdges[e.target]++;
        });

        // Find roots (nodes with 0 incoming edges)
        let queue = data.nodes.filter((n: any) => incomingEdges[n.id] === 0).map((n: any) => n.id);
        
        // If there are no roots (e.g. all circular), just use the first node
        if (queue.length === 0 && data.nodes.length > 0) {
            queue.push(data.nodes[0].id);
        }

        queue.forEach((id: string) => { nodeLevels[id] = 0; });

        let currentLevel = 0;
        while (queue.length > 0) {
            const nextQueue: string[] = [];
            queue.forEach((id: string) => {
                adjList[id].forEach((target: string) => {
                    if (nodeLevels[target] === undefined) {
                        nodeLevels[target] = currentLevel + 1;
                        nextQueue.push(target);
                    }
                });
            });
            queue = nextQueue;
            currentLevel++;
        }

        // Put any completely disconnected nodes at the bottom level
        data.nodes.forEach((n: any) => {
            if (nodeLevels[n.id] === undefined) {
                nodeLevels[n.id] = currentLevel;
            }
        });

        // Group nodes by their calculated level
        const nodesByLevel: Record<number, string[]> = {};
        Object.keys(nodeLevels).forEach((id) => {
            const level = nodeLevels[id];
            if (!nodesByLevel[level]) nodesByLevel[level] = [];
            nodesByLevel[level].push(id);
        });

        const spacingX = 450; 
        const spacingY = 350; // Increased vertical spacing so lines have room to route around boxes

        // Acid/Brutalist colors for the nodes
        const colors = ["#C1FF00", "#FF4500", "#FFD700", "#00FFFF", "#FF00FF", "#E5E5E5"];
        const getTagColor = (tags?: string[]) => {
            if (!tags || tags.length === 0) return "#fff";
            const hash = tags[0].split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
            return colors[hash % colors.length];
        };

        // Convert the backend graph data to ReactFlow format
        const rfNodes: Node[] = data.nodes.map((n: any) => {
          const level = nodeLevels[n.id];
          const siblings = nodesByLevel[level];
          const indexInLevel = siblings.indexOf(n.id);
          
          // Center the row horizontally
          const totalWidth = siblings.length * spacingX;
          const startX = -(totalWidth / 2);

          return {
            id: n.id,
            sourcePosition: "bottom" as any, // Force lines to exit from bottom
            targetPosition: "top" as any, // Force lines to enter from top
            position: { 
              x: startX + (indexInLevel * spacingX), 
              y: level * spacingY 
            }, 
            data: { label: n.label || n.id },
            style: { 
              backgroundColor: getTagColor(n.tags), 
              border: "3px solid #000", 
              borderRadius: "0",
              fontWeight: "900", 
              fontSize: "14px",
              textAlign: "center", 
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "15px", 
              width: 320, 
              minHeight: 60, 
              boxShadow: "6px 6px 0px 0px rgba(0,0,0,1)" 
            }
          };
        });

        const rfEdges: Edge[] = data.edges.map((e: any, i: number) => ({
          id: `e${i}`,
          source: e.source,
          target: e.target,
          label: e.label, 
          labelStyle: { fill: '#000', fontWeight: 900, fontSize: 13, fontFamily: 'monospace' },
          labelBgStyle: { fill: '#fff', stroke: '#000', strokeWidth: 2, rx: 0, ry: 0 }, // rx/ry 0 removes border radius!
          labelBgPadding: [8, 4] as [number, number], // Bigger edge boxes

          style: { stroke: "#000", strokeWidth: 2.5, opacity: 0.6 }, 
          animated: true, // Animation shows the direction of the flow
          type: "smoothstep", // Right-angled flow lines
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20,
            height: 20,
            color: '#000',
          },
        }));

        setNodes(rfNodes);
        setEdges(rfEdges);
      } catch (e: any) {
        console.error("Failed to load graph.json", e);
        setError(e.message || "Unknown error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchGraph();
  }, [repoName]);

  if (!repoName) {
    return (
      <div className="h-full flex items-center justify-center font-mono text-brutal-gray-dark border-2 border-dashed border-brutal-black m-4 bg-brutal-white">
        Waiting for active OKF Bundle...
      </div>
    );
  }

  if (loading) {
    return <div className="h-full flex items-center justify-center font-mono font-bold">LOADING GRAPH...</div>;
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center font-mono bg-red-100 p-8 border-4 border-brutal-black m-4 text-center">
        <h2 className="text-xl font-bold mb-4">ERROR LOADING GRAPH</h2>
        <p className="text-sm bg-brutal-white p-4 border-2 border-brutal-black text-red-600">{error}</p>
      </div>
    );
  }

  if (nodes.length === 0) {
    return <div className="h-full flex items-center justify-center font-mono">No graph data available (graph.json not found or empty).</div>;
  }

  return (
    <div className="w-full h-[80vh] border-3 border-brutal-black shadow-brutal bg-[#E5E5E5]">
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background color="#000" gap={20} size={1} />
        <Controls className="border-2 border-brutal-black shadow-brutal-sm rounded-none" />
      </ReactFlow>
    </div>
  );
}
