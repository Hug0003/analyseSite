"use client";

import { useState, FormEvent } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Loader2, Globe, Swords } from "lucide-react";
import { cn } from "@/lib/utils";

interface SearchBarProps {
    onSearch: (url: string, competitorUrl?: string) => void;
    isLoading?: boolean;
    placeholder?: string;
    buttonText?: string;
    loadingText?: string;
    helperText?: string;
    className?: string;
}

export function SearchBar({
    onSearch,
    isLoading = false,
    placeholder = "Enter a URL to audit (e.g., example.com)",
    buttonText = "Analyze",
    loadingText = "Analyzing...",
    helperText = "Free website audit for SEO, security, performance & technology stack",
    className
}: SearchBarProps) {
    const [url, setUrl] = useState("");
    const [competitorUrl, setCompetitorUrl] = useState("");
    const [showCompetitor, setShowCompetitor] = useState(false);
    const [isFocused, setIsFocused] = useState(false);

    const cleanUrl = (input: string) => {
        return input
            .replace(/^(?:https?:\/\/)?(?:www[./])?/, "")
            .replace(/\/$/, "")
            .trim();
    };

    const handleBlur = () => {
        setIsFocused(false);
        if (url) setUrl(cleanUrl(url));
    };

    const handleCompetitorBlur = () => {
        if (competitorUrl) setCompetitorUrl(cleanUrl(competitorUrl));
    };

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        if (url.trim() && !isLoading) {
            onSearch(cleanUrl(url.trim()), showCompetitor && competitorUrl.trim() ? cleanUrl(competitorUrl.trim()) : undefined);
        }
    };

    return (
        <form onSubmit={handleSubmit} className={cn("w-full max-w-2xl mx-auto", className)}>
            <div
                className={cn(
                    "relative group transition-all duration-500 ease-out",
                    isFocused && "scale-[1.02]"
                )}
            >
                {/* Glow effect */}
                <div
                    className={cn(
                        "absolute -inset-1 bg-gradient-to-r from-violet-600 via-blue-600 to-cyan-500 rounded-2xl blur-lg opacity-0 transition-all duration-500",
                        isFocused && "opacity-40",
                        isLoading && "opacity-60 animate-pulse"
                    )}
                />

                {/* Search container */}
                <div
                    className={cn(
                        "relative flex flex-col gap-3 bg-zinc-900/90 backdrop-blur-xl border border-zinc-800 rounded-xl p-2 transition-all duration-300",
                        isFocused && "border-zinc-700 bg-zinc-900",
                        isLoading && "border-violet-500/50"
                    )}
                >
                    {/* Main URL Input */}
                    <div className="flex items-center gap-3">
                        {/* Globe icon */}
                        <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-zinc-800/50">
                            <Globe className={cn(
                                "w-5 h-5 text-zinc-400 transition-colors duration-300",
                                isFocused && "text-violet-400"
                            )} />
                        </div>

                        {/* Input */}
                        <Input
                            type="text"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            onFocus={() => setIsFocused(true)}
                            onBlur={handleBlur}
                            placeholder={placeholder}
                            disabled={isLoading}
                            className="flex-1 bg-transparent border-none text-lg text-white placeholder:text-zinc-500 focus-visible:ring-0 focus-visible:ring-offset-0 h-12"
                        />

                        {/* Submit button */}
                        <Button
                            type="submit"
                            disabled={!url.trim() || isLoading}
                            className={cn(
                                "h-12 px-6 rounded-lg font-medium transition-all duration-300",
                                "bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500",
                                "disabled:opacity-50 disabled:cursor-not-allowed",
                                "shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40"
                            )}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                    {loadingText}
                                </>
                            ) : (
                                <>
                                    <Search className="w-5 h-5 mr-2" />
                                    {buttonText}
                                </>
                            )}
                        </Button>
                    </div>

                    {/* Competitor Toggle & Input */}
                    <div className="flex items-center gap-3 pl-1">
                        <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowCompetitor(!showCompetitor)}
                            className={cn(
                                "text-xs transition-colors",
                                showCompetitor ? "text-orange-400 hover:text-orange-300" : "text-zinc-500 hover:text-zinc-400"
                            )}
                        >
                            <Swords className="w-4 h-4 mr-1.5" />
                            Mode Versus
                        </Button>

                        {showCompetitor && (
                            <div className="flex-1 flex items-center gap-2">
                                <Input
                                    type="text"
                                    value={competitorUrl}
                                    onChange={(e) => setCompetitorUrl(e.target.value)}
                                    placeholder="URL du concurrent (optionnel)"
                                    disabled={isLoading}
                                    onBlur={handleCompetitorBlur}
                                    className="flex-1 bg-zinc-800/30 border border-zinc-700/50 text-sm text-white placeholder:text-zinc-600 focus-visible:ring-1 focus-visible:ring-orange-500/50 h-10 rounded-lg"
                                />
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Helper text */}
            <p className="text-center text-sm text-zinc-500 mt-4">
                {helperText}
            </p>
        </form>
    );
}
