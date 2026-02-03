"use client";

import { useEffect, useState, useRef } from "react";
import { Check, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { AnalysisStep } from "@/types";

interface LoadingProgressProps {
    steps: AnalysisStep[];
    logs?: string[];
    className?: string;
    progress?: number;
}

export function LoadingProgress({ steps, logs = [], className, progress = 0 }: LoadingProgressProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    const completedCount = steps.filter(s => s.status === "completed" || s.status === "error").length;
    // The 'progress' prop is now used, so the internal calculation is removed to avoid redeclaration.
    // If 'progress' prop is not provided, it defaults to 0.
    // If you still need to calculate progress based on steps when the prop is not provided,
    // you might want to use a different variable name or conditional logic.
    // For now, assuming the prop 'progress' takes precedence.

    // Auto-scroll to bottom when logs update
    useEffect(() => {
        if (bottomRef.current) {
            bottomRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
        }
    }, [logs]);

    return (
        <div className={cn("w-full max-w-xl mx-auto", className)}>
            {/* Progress bar */}
            <div className="relative h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-8">
                <div
                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-violet-600 via-blue-500 to-cyan-400 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                />
                {/* Shimmer effect */}
                <div
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"
                    style={{
                        backgroundSize: "200% 100%",
                        animation: "shimmer 2s infinite linear"
                    }}
                />
            </div>

            {/* Premium Live Terminal */}
            <div className="mt-8 group relative">
                {/* Glowing Border Effect */}
                <div className="absolute -inset-0.5 bg-gradient-to-r from-violet-600 to-blue-600 rounded-xl blur opacity-20 group-hover:opacity-40 transition duration-1000"></div>

                <div className="relative bg-[#0a0a0b] rounded-xl border border-white/10 shadow-2xl overflow-hidden h-[320px] flex flex-col">
                    {/* Terminal Header */}
                    <div className="flex items-center px-4 py-3 border-b border-white/5 bg-white/5 backdrop-blur-sm shrink-0">
                        <div className="flex gap-2">
                            <div className="w-3 h-3 rounded-full bg-[#ff5f56] border border-[#ff5f56]/20 shadow-[0_0_8px_rgba(255,95,86,0.3)]" />
                            <div className="w-3 h-3 rounded-full bg-[#ffbd2e] border border-[#ffbd2e]/20 shadow-[0_0_8px_rgba(255,189,46,0.3)]" />
                            <div className="w-3 h-3 rounded-full bg-[#27c93f] border border-[#27c93f]/20 shadow-[0_0_8px_rgba(39,201,63,0.3)]" />
                        </div>
                        <div className="ml-6 text-xs font-mono text-zinc-400 flex items-center gap-2 select-none">
                            <span className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-[pulse_2s_infinite]"></span>
                            root@scanner: ~
                        </div>
                    </div>

                    {/* Terminal Content */}
                    <div className="flex-1 p-6 font-mono text-sm overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent overscroll-contain" id="terminal-content">
                        <div className="space-y-2">
                            {/* Initial Command Echo */}
                            <div className="text-zinc-500 mb-6 pb-2 border-b border-white/5 flex items-center gap-2">
                                <span className="text-violet-400 font-bold">➜</span>
                                <span className="text-cyan-300">~</span>
                                <span className="text-zinc-300">./start_audit.sh</span>
                                <span className="text-zinc-500">--target="{typeof window !== 'undefined' ? window.location.hostname : 'unknown'}" --deep-scan --verbose</span>
                            </div>

                            {logs && logs.map((log, i) => {
                                const isSuccess = log.includes("✅") || log.toLowerCase().includes("completed") || log.toLowerCase().includes("finish");
                                const isError = log.includes("❌") || log.toLowerCase().includes("fail") || log.toLowerCase().includes("error");
                                const isWarning = log.includes("Warning");
                                const time = new Date().toLocaleTimeString().split(' ')[0];

                                return (
                                    <div key={i} className="flex gap-3 animate-fade-in-up items-start group/line">
                                        <span className="text-zinc-600 select-none text-xs mt-0.5 w-16 text-right opacity-50 group-hover/line:opacity-100 transition-opacity">[{time}]</span>
                                        <div className="flex-1">
                                            {log.includes(">>") ? (
                                                <span className="text-violet-400 font-bold tracking-wide block py-1 border-l-2 border-violet-500/50 pl-3 bg-violet-500/5 my-2">
                                                    {log.replace(">>", "").trim()}
                                                </span>
                                            ) : (
                                                <span className={cn(
                                                    "break-words lead-relaxed block",
                                                    isSuccess ? "text-emerald-400" :
                                                        isError ? "text-red-400 font-bold" :
                                                            isWarning ? "text-amber-400" :
                                                                "text-zinc-300"
                                                )}>
                                                    {isSuccess && <span className="inline-block mr-2 scale-110">✨</span>}
                                                    {isError && <span className="inline-block mr-2 text-lg">✗</span>}
                                                    {log.replace("✅", "").replace("❌", "").trim()}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}

                            {/* Active Processing Indicator */}
                            <div className="flex items-center gap-2 text-violet-500 mt-4 pt-4 border-t border-white/5 animate-pulse pl-20" ref={bottomRef}>
                                <span className="font-bold">➜</span>
                                <span className="w-2.5 h-5 bg-violet-500/80 block"></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}


// Add shimmer and scrollbar styles to globals if needed
const globalStyles = `
@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* Custom Scrollbar for Terminal */
.scrollbar-thin::-webkit-scrollbar {
    width: 6px;
}
.scrollbar-thin::-webkit-scrollbar-track {
    background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
}
.scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background-color: rgba(255, 255, 255, 0.2);
}
`;

if (typeof document !== "undefined") {
    // Check if style already exists to avoid duplicates
    if (!document.getElementById('loading-progress-styles')) {
        const style = document.createElement("style");
        style.id = 'loading-progress-styles';
        style.textContent = globalStyles;
        document.head.appendChild(style);
    }
}
