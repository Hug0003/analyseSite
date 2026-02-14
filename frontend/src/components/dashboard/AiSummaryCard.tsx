import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { Sparkles, ArrowRight, Clock, Target, AlertTriangle, Lock } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { AnalyzeResponse } from "@/types/api"
import { useAuth } from "@/contexts/AuthContext"

interface AiSummaryCardProps {
    data: AnalyzeResponse
}

interface AiSummaryResponse {
    summary: string
    top_priorities: string[]
    estimated_time: string
}

export function AiSummaryCard({ data }: AiSummaryCardProps) {
    const { user } = useAuth()
    const [summary, setSummary] = useState<AiSummaryResponse | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [displayedSummary, setDisplayedSummary] = useState("")
    const [isTyping, setIsTyping] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const canUseAI = user?.plan_tier === "pro" || user?.plan_tier === "agency"

    // Trigger AI analysis when data is available
    useEffect(() => {
        const fetchSummary = async () => {
            if (!data || !canUseAI) return

            setIsLoading(true)
            setError(null)
            try {
                const token = localStorage.getItem('access_token')
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ''}/api/ai/summary`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(token && { 'Authorization': `Bearer ${token}` })
                    },
                    body: JSON.stringify({ scan_results: data })
                })

                if (res.ok) {
                    const json = await res.json()
                    setSummary(json)
                } else {
                    const errText = await res.text() // Try to get error detail
                    setError(`Erreur API (${res.status}): ${errText.substring(0, 50)}...`)
                    console.error("Failed to fetch AI summary", res.status, errText)
                }
            } catch (err) {
                console.error(err)
                setError("Impossible de contacter le serveur IA.")
            } finally {
                setIsLoading(false)
            }
        }

        fetchSummary()
    }, [data.url]) // Trigger when URL changes (new scan)

    // Typewriter effect logic
    useEffect(() => {
        if (summary?.summary) {
            setIsTyping(true)
            let i = 0
            const text = summary.summary.trim() // Trim to avoid invisible first chars
            setDisplayedSummary("")

            const interval = setInterval(() => {
                i++
                setDisplayedSummary(text.substring(0, i))
                if (i >= text.length) {
                    clearInterval(interval)
                    setIsTyping(false)
                }
            }, 10) // Fast speed

            return () => clearInterval(interval)
        }
    }, [summary])

    if (!canUseAI) {
        return (
            <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
                <Card className="bg-gradient-to-br from-zinc-900 to-zinc-800 border-zinc-700/50">
                    <CardContent className="p-6 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-violet-500/10">
                                <Lock className="w-6 h-6 text-violet-400" />
                            </div>
                            <div>
                                <h3 className="text-white font-semibold flex items-center gap-2">
                                    Résumé IA
                                    <Badge className="bg-violet-500/20 text-violet-300 text-[10px]">PRO</Badge>
                                </h3>
                                <p className="text-zinc-400 text-sm">Passez au plan Pro pour obtenir un résumé IA de votre audit.</p>
                            </div>
                        </div>
                        <a href="/pricing" className="px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors">
                            Upgrade
                        </a>
                    </CardContent>
                </Card>
            </motion.div>
        )
    }

    if (!summary && !isLoading && !error) return null

    return (
        <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
        >
            <Card className="border p-[1px] bg-gradient-to-r from-violet-500/50 via-blue-500/50 to-emerald-500/50 overflow-hidden">
                <div className="bg-black/90 h-full w-full rounded-xl">
                    <CardContent className="p-6">
                        <div className="flex items-start gap-4">
                            <div className="p-3 rounded-xl bg-violet-500/20 text-violet-400 shrink-0">
                                <Sparkles className="w-6 h-6" />
                            </div>

                            <div className="space-y-4 w-full">
                                <div>
                                    <h3 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-blue-400 mb-1 flex items-center gap-2">
                                        Analyse du Copilote IA
                                        {isLoading && (
                                            <span className="text-xs font-normal text-zinc-500 animate-pulse ml-2">
                                                Génération en cours...
                                            </span>
                                        )}
                                    </h3>

                                    {/* Summary Paragraph with Typewriter */}
                                    <div className="min-h-[60px] text-zinc-300 leading-relaxed">
                                        {error ? (
                                            <div className="text-red-400 text-sm bg-red-500/10 p-3 rounded border border-red-500/20 flex items-center gap-2">
                                                <AlertTriangle className="w-4 h-4" />
                                                Erreur IA: {error}
                                                <button onClick={() => window.location.reload()} className="underline ml-2 hover:text-red-300">Réessayer</button>
                                            </div>
                                        ) : (
                                            <>
                                                {displayedSummary}
                                                {isTyping && <motion.span animate={{ opacity: [0, 1, 0] }} className="inline-block w-2 h-4 bg-violet-400 ml-1 translate-y-1" />}
                                                {isLoading && !summary && (
                                                    <div className="space-y-2 animate-pulse mt-2">
                                                        <div className="h-4 bg-zinc-800 rounded w-full"></div>
                                                        <div className="h-4 bg-zinc-800 rounded w-5/6"></div>
                                                        <div className="h-4 bg-zinc-800 rounded w-4/6"></div>
                                                    </div>
                                                )}
                                            </>
                                        )}
                                    </div>
                                </div>

                                {/* Priorities & Time */}
                                {!isLoading && summary && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: 1 }} // Appear after typing fits roughly
                                        className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-zinc-800/50"
                                    >
                                        <div className="space-y-3">
                                            <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                                <Target className="w-4 h-4" />
                                                Top 3 Priorités Stratégiques
                                            </h4>
                                            <ul className="space-y-2">
                                                {summary.top_priorities.map((item, i) => (
                                                    <li key={i} className="flex items-start gap-2 text-sm text-zinc-300">
                                                        <ArrowRight className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                                                        {item}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>

                                        <div className="flex flex-col justify-start">
                                            <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2 mb-3">
                                                <Clock className="w-4 h-4" />
                                                Temps de correction estimé
                                            </h4>
                                            <div>
                                                <Badge variant="outline" className="text-lg py-1 px-4 border-blue-500/30 text-blue-400 bg-blue-500/10">
                                                    {summary.estimated_time}
                                                </Badge>
                                                <p className="text-xs text-zinc-500 mt-2">
                                                    Estimation basée sur la complexité des tâches techniques détectées (SEO, Sécurité, Performance).
                                                </p>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </div>
                        </div>
                    </CardContent>
                </div>
            </Card>
        </motion.div>
    )
}
