"use client";

import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
    ShieldAlert,
    AlertTriangle,
    FileCode,
    Lightbulb,
    ExternalLink,
    Copy,
    Check,
    Lock,
    CheckCircle2,
    Sparkles,
    Loader2
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useLanguage } from "@/lib/i18n";
import { SeverityLevel } from "@/types";
import { useAuth } from "@/contexts/AuthContext";

interface SecurityDetailDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    type: "header" | "file";
    data: {
        name: string;
        severity: SeverityLevel;
        value?: string | null;
        present?: boolean;
        description?: string | null;
        recommendation?: string | null;
        path?: string;
    };
}

const severityColors: Record<SeverityLevel, { bg: string; text: string; border: string }> = {
    critical: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/30" },
    high: { bg: "bg-orange-500/10", text: "text-orange-400", border: "border-orange-500/30" },
    medium: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
    low: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30" },
    info: { bg: "bg-zinc-500/10", text: "text-zinc-400", border: "border-zinc-500/30" },
    ok: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30" },
};

export function SecurityDetailDialog({ open, onOpenChange, type, data }: SecurityDetailDialogProps) {
    const { t } = useLanguage();
    const { user } = useAuth();
    const [copied, setCopied] = useState(false);
    const canUseAI = user?.plan_tier === "pro" || user?.plan_tier === "agency";

    // Get detailed info from translations
    const detailedInfo = type === "header"
        ? t.security.securityHeaders[data.name]
        : (data.path ? t.security.exposedFilesDetail[data.path] : undefined);

    const colors = severityColors[data.severity];

    // AI Fix State - now expecting structured JSON
    const [generatedGuide, setGeneratedGuide] = useState<{
        why?: string;
        environment?: string;
        file_path?: string;
        code?: string;
        steps?: string[];
        commands?: string[];
        validation?: string[];
    } | null>(null);
    const [isFixing, setIsFixing] = useState(false);
    const [fixError, setFixError] = useState<string | null>(null);

    const handleGenerateFix = async () => {
        setIsFixing(true);
        setFixError(null);
        try {
            const token = localStorage.getItem('access_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ''}/api/ai/fix`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify({
                    issue_type: "missing_security_header",
                    context: {
                        header_name: data.name,
                        description: detailedInfo?.description || data.description
                    }
                })
            });

            if (!res.ok) throw new Error("API Error");
            const json = await res.json();
            setGeneratedGuide(json);
        } catch (err) {
            setFixError("Impossible de générer le correctif.");
        } finally {
            setIsFixing(false);
        }
    };

    const handleCopyCode = async (code: string) => {
        await navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl bg-zinc-900 border-zinc-800 max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <div className="flex items-center gap-3">
                        <div className={cn("p-2 rounded-lg", colors.bg)}>
                            <ShieldAlert className={cn("w-5 h-5", colors.text)} />
                        </div>
                        <div>
                            <DialogTitle className="text-xl text-zinc-100">
                                {type === "header" ? data.name : data.path}
                            </DialogTitle>
                            <DialogDescription className="flex items-center gap-2 mt-1">
                                <Badge variant="outline" className={cn("text-xs", colors.text, colors.border)}>
                                    {data.severity.toUpperCase()}
                                </Badge>
                                <span className="text-zinc-500">
                                    {type === "header"
                                        ? (data.present ? t.security.headerPresent : t.security.headerMissing)
                                        : t.security.exposedFile
                                    }
                                </span>
                            </DialogDescription>
                        </div>
                    </div>
                </DialogHeader>

                <div className="space-y-6 mt-4">
                    {/* Current Value (if header is present) */}
                    {type === "header" && data.present && data.value && (
                        <div>
                            <h4 className="text-sm font-medium text-zinc-400 mb-2 flex items-center gap-2">
                                <FileCode className="w-4 h-4" />
                                Current Value
                            </h4>
                            <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700/50 font-mono text-sm text-zinc-300 break-all">
                                {data.value}
                            </div>
                        </div>
                    )}

                    {/* Evidence (for missing headers) */}
                    {type === "header" && !data.present && (
                        <div>
                            <h4 className="text-sm font-medium text-zinc-400 mb-2 flex items-center gap-2">
                                <AlertTriangle className="w-4 h-4" />
                                Evidence
                            </h4>
                            <div className={cn("p-3 rounded-lg border", colors.bg, colors.border)}>
                                <p className="text-sm text-zinc-300">
                                    The <code className="px-1.5 py-0.5 rounded bg-zinc-800 text-violet-400">{data.name}</code> header
                                    was not found in the HTTP response headers.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Description */}
                    <div>
                        <h4 className="text-sm font-medium text-zinc-400 mb-2">Description</h4>
                        <p className="text-sm text-zinc-300 leading-relaxed">
                            {detailedInfo?.description || data.description || "No detailed description available."}
                        </p>
                    </div>

                    {/* Impact */}
                    {detailedInfo?.impact && (
                        <div>
                            <h4 className="text-sm font-medium text-red-400 mb-2 flex items-center gap-2">
                                <AlertTriangle className="w-4 h-4" />
                                Security Impact
                            </h4>
                            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                <p className="text-sm text-zinc-300 leading-relaxed">
                                    {detailedInfo.impact}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* AI Fix Section */}
                    {type === "header" && !data.present && (
                        <div className="mb-6">
                            <div className="flex items-center justify-between mb-2">
                                <h4 className="text-sm font-medium text-violet-400 flex items-center gap-2">
                                    <Sparkles className="w-4 h-4" />
                                    AI Auto-Fix
                                </h4>
                            </div>

                            {!generatedGuide ? (
                                canUseAI ? (
                                    <Button
                                        onClick={handleGenerateFix}
                                        disabled={isFixing}
                                        className="w-full bg-violet-600 hover:bg-violet-700 text-white border-none"
                                    >
                                        {isFixing ? (
                                            <>
                                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                                Génération du guide de déploiement...
                                            </>
                                        ) : (
                                            <>
                                                <Sparkles className="w-4 h-4 mr-2" />
                                                ✨ Générer le guide de correction
                                            </>
                                        )}
                                    </Button>
                                ) : (
                                    <a href="/pricing" className="flex items-center justify-center gap-2 w-full px-4 py-2 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-400 hover:bg-zinc-700 transition-colors text-sm">
                                        <Lock className="w-4 h-4" />
                                        Fix IA — <span className="text-violet-400 font-medium">Plan Pro requis</span>
                                    </a>
                                )
                            ) : (
                                <div className="space-y-4 animate-in fade-in zoom-in-95 duration-300">
                                    {/* Business Impact */}
                                    {generatedGuide.why && (
                                        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                                            <h5 className="text-sm font-semibold text-red-400 mb-2 flex items-center gap-2">
                                                <AlertTriangle className="w-4 h-4" />
                                                Pourquoi c'est critique
                                            </h5>
                                            <p className="text-sm text-zinc-300 leading-relaxed">{generatedGuide.why}</p>
                                        </div>
                                    )}

                                    {/* Environment & File Info */}
                                    <div className="grid grid-cols-2 gap-3">
                                        {generatedGuide.environment && (
                                            <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                                                <p className="text-xs text-blue-400 font-medium mb-1">Environnement détecté</p>
                                                <p className="text-sm text-white font-mono">{generatedGuide.environment}</p>
                                            </div>
                                        )}
                                        {generatedGuide.file_path && (
                                            <div className="p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
                                                <p className="text-xs text-violet-400 font-medium mb-1">Fichier à modifier</p>
                                                <p className="text-sm text-white font-mono truncate" title={generatedGuide.file_path}>
                                                    {generatedGuide.file_path}
                                                </p>
                                            </div>
                                        )}
                                    </div>

                                    {/* Code Snippet */}
                                    {generatedGuide.code && (
                                        <div>
                                            <div className="flex items-center justify-between mb-2">
                                                <h5 className="text-sm font-semibold text-emerald-400 flex items-center gap-2">
                                                    <FileCode className="w-4 h-4" />
                                                    Code à ajouter
                                                </h5>
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    className="h-7 text-xs text-zinc-500 hover:text-white"
                                                    onClick={() => handleCopyCode(generatedGuide.code!)}
                                                >
                                                    {copied ? (
                                                        <><Check className="w-3 h-3 mr-1" /> Copié</>
                                                    ) : (
                                                        <><Copy className="w-3 h-3 mr-1" /> Copier</>
                                                    )}
                                                </Button>
                                            </div>
                                            <div className="p-3 rounded-lg bg-zinc-950 border border-emerald-500/30 font-mono text-sm text-emerald-100 whitespace-pre-wrap overflow-x-auto">
                                                {generatedGuide.code}
                                            </div>
                                        </div>
                                    )}

                                    {/* Deployment Steps */}
                                    {generatedGuide.steps && generatedGuide.steps.length > 0 && (
                                        <div>
                                            <h5 className="text-sm font-semibold text-blue-400 mb-3 flex items-center gap-2">
                                                <Lightbulb className="w-4 h-4" />
                                                Étapes de déploiement
                                            </h5>
                                            <ol className="space-y-2">
                                                {generatedGuide.steps.map((step, i) => (
                                                    <li key={i} className="flex gap-3 text-sm text-zinc-300">
                                                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-bold">
                                                            {i + 1}
                                                        </span>
                                                        <span className="pt-0.5">{step}</span>
                                                    </li>
                                                ))}
                                            </ol>
                                        </div>
                                    )}

                                    {/* Terminal Commands */}
                                    {generatedGuide.commands && generatedGuide.commands.length > 0 && (
                                        <div>
                                            <h5 className="text-sm font-semibold text-amber-400 mb-2 flex items-center gap-2">
                                                <FileCode className="w-4 h-4" />
                                                Commandes à exécuter
                                            </h5>
                                            <div className="space-y-2">
                                                {generatedGuide.commands.map((cmd, i) => (
                                                    <div key={i} className="flex items-center gap-2 p-2 rounded bg-zinc-950 border border-zinc-700 font-mono text-xs text-amber-100">
                                                        <span className="text-amber-500">$</span>
                                                        <code className="flex-1">{cmd}</code>
                                                        <Button
                                                            size="sm"
                                                            variant="ghost"
                                                            className="h-6 w-6 p-0 text-zinc-500 hover:text-white"
                                                            onClick={() => handleCopyCode(cmd)}
                                                        >
                                                            <Copy className="w-3 h-3" />
                                                        </Button>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Validation Checklist */}
                                    {generatedGuide.validation && generatedGuide.validation.length > 0 && (
                                        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                                            <h5 className="text-sm font-semibold text-emerald-400 mb-3 flex items-center gap-2">
                                                <CheckCircle2 className="w-4 h-4" />
                                                Checklist de validation
                                            </h5>
                                            <ul className="space-y-2">
                                                {generatedGuide.validation.map((check, i) => (
                                                    <li key={i} className="flex items-start gap-2 text-sm text-zinc-300">
                                                        <div className="flex-shrink-0 w-4 h-4 rounded border-2 border-emerald-500/50 mt-0.5" />
                                                        <span>{check}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    <Badge variant="outline" className="bg-violet-500/10 text-violet-400 border-violet-500/20">
                                        ✨ Généré par IA - Veuillez vérifier avant application
                                    </Badge>
                                </div>
                            )}
                            {fixError && (
                                <p className="text-xs text-red-400 mt-2 flex items-center gap-1">
                                    <AlertTriangle className="w-3 h-3" />
                                    {fixError}
                                </p>
                            )}
                        </div>
                    )}

                    <Separator className="bg-zinc-800" />

                    {/* Remediation */}
                    {(detailedInfo?.remediation || data.recommendation) && (
                        <div>
                            <h4 className="text-sm font-medium text-emerald-400 mb-2 flex items-center gap-2">
                                <Lightbulb className="w-4 h-4" />
                                How to Fix
                            </h4>
                            <div className="relative">
                                <div className="p-4 rounded-lg bg-zinc-800/80 border border-zinc-700/50 font-mono text-sm text-zinc-300 whitespace-pre-wrap overflow-x-auto">
                                    {detailedInfo?.remediation || data.recommendation}
                                </div>
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    className="absolute top-2 right-2 h-8 w-8 p-0 text-zinc-500 hover:text-white"
                                    onClick={() => handleCopyCode(detailedInfo?.remediation || data.recommendation || "")}
                                >
                                    {copied ? (
                                        <Check className="w-4 h-4 text-emerald-400" />
                                    ) : (
                                        <Copy className="w-4 h-4" />
                                    )}
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* References (only for headers) */}
                    {type === "header" && detailedInfo && "references" in detailedInfo && (detailedInfo as { references?: string[] }).references && (detailedInfo as { references: string[] }).references.length > 0 && (
                        <div>
                            <h4 className="text-sm font-medium text-zinc-400 mb-2">References</h4>
                            <div className="space-y-2">
                                {(detailedInfo as { references: string[] }).references.map((ref, i) => (
                                    <a
                                        key={i}
                                        href={ref}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                                    >
                                        <ExternalLink className="w-4 h-4" />
                                        {new URL(ref).hostname}
                                    </a>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}
