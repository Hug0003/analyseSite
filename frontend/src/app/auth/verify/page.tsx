"use client"

import { useState, useRef, useEffect } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Shield, Loader2, ArrowRight } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

import { Suspense } from "react"

function VerifyContent() {
    const router = useRouter()
    const searchParams = useSearchParams()
    const email = searchParams.get("email")

    const [code, setCode] = useState(["", "", "", "", "", ""])
    const [loading, setLoading] = useState(false)
    const [resending, setResending] = useState(false)
    const inputs = useRef<(HTMLInputElement | null)[]>([])

    useEffect(() => {
        if (!email) {
            toast.error("Email manquant")
            router.push("/register")
        }
    }, [email, router])

    const handleChange = (index: number, value: string) => {
        // Allow only numbers
        if (value && !/^\d+$/.test(value)) return

        const newCode = [...code]
        newCode[index] = value
        setCode(newCode)

        // Move to next input
        if (value && index < 5) {
            inputs.current[index + 1]?.focus()
        }
    }

    const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
        // Move to previous input on backspace
        if (e.key === "Backspace" && !code[index] && index > 0) {
            inputs.current[index - 1]?.focus()
        }
    }

    const handlePaste = (e: React.ClipboardEvent) => {
        e.preventDefault()
        const pastedData = e.clipboardData.getData("text").slice(0, 6)
        if (!/^\d+$/.test(pastedData)) return

        const newCode = [...code]
        pastedData.split("").forEach((char, index) => {
            if (index < 6) newCode[index] = char
        })
        setCode(newCode)
        inputs.current[Math.min(pastedData.length, 5)]?.focus()
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        const fullCode = code.join("")
        if (fullCode.length !== 6) return

        setLoading(true)
        try {
            const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
            const response = await fetch(`${API_BASE_URL}/api/auth/verify-email`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, code: fullCode }),
            })

            if (!response.ok) {
                const error = await response.json()
                throw new Error(error.detail || "Vérification échouée")
            }

            toast.success("Compte vérifié avec succès !")
            router.push("/login")
        } catch (error: any) {
            toast.error(error.message)
        } finally {
            setLoading(false)
        }
    }

    const handleResendCode = async () => {
        if (!email) return
        setResending(true)
        try {
            const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
            await fetch(`${API_BASE_URL}/api/auth/resend-code`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            })
            toast.success("Nouveau code envoyé")
        } catch (error) {
            toast.error("Erreur lors de l'envoi du code")
        } finally {
            setResending(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-black p-4">
            <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:32px_32px]" />

            <Card className="w-full max-w-md relative z-10 bg-zinc-900 border-zinc-800">
                <CardHeader className="text-center space-y-3">
                    <div className="mx-auto w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center">
                        <Shield className="w-6 h-6 text-blue-500" />
                    </div>
                    <CardTitle className="text-2xl font-bold text-white">Vérifiez votre email</CardTitle>
                    <CardDescription>
                        Nous avons envoyé un code à 6 chiffres à <span className="text-zinc-200 font-medium">{email}</span>
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="flex justify-center gap-2">
                            {code.map((digit, index) => (
                                <Input
                                    key={index}
                                    ref={(el) => { inputs.current[index] = el }}
                                    type="text"
                                    maxLength={1}
                                    value={digit}
                                    onChange={(e) => handleChange(index, e.target.value)}
                                    onKeyDown={(e) => handleKeyDown(index, e)}
                                    onPaste={handlePaste}
                                    className="w-12 h-14 text-center text-2xl font-bold bg-zinc-950 border-zinc-800 text-white focus:border-blue-500 transition-colors"
                                />
                            ))}
                        </div>

                        <Button
                            type="submit"
                            className="w-full h-11 bg-blue-600 hover:bg-blue-700 text-white"
                            disabled={loading || code.some(c => !c)}
                        >
                            {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                            Vérifier mon compte
                        </Button>

                        <div className="text-center">
                            <button
                                type="button"
                                onClick={handleResendCode}
                                disabled={resending}
                                className="text-sm text-zinc-400 hover:text-white transition-colors disabled:opacity-50"
                            >
                                {resending ? "Envoi en cours..." : "Renvoyer le code"}
                            </button>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    )
}

export default function VerifyPage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-black flex items-center justify-center"><Loader2 className="w-8 h-8 text-blue-500 animate-spin" /></div>}>
            <VerifyContent />
        </Suspense>
    )
}
