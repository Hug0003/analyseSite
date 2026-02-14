"use client"

import { AuthHeader } from "@/components/auth-header"
import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Check, Shield, Zap, Building, Minus } from "lucide-react"
import { createCheckoutSession, createPortalSession, simulateUpgrade, cancelSubscription } from "@/lib/api"
import { toast } from "sonner"
import { useState } from "react"
import { useEffect } from "react"
import Link from "next/link"
import { FEATURES } from "@/lib/plans"

const PRICE_ID_PRO = "price_pro_monthly"
const PRICE_ID_AGENCY = "price_agency_monthly"

export default function SubscriptionPage() {
    const { user, isAuthenticated, loading: authLoading, refreshUser } = useAuth()
    const [billingLoading, setBillingLoading] = useState(false)

    // Handle success/cancel from Stripe/Mock
    useEffect(() => {
        const query = new URLSearchParams(window.location.search)
        if (query.get("checkout_success")) {
            toast.success("Abonnement mis à jour avec succès !")
            refreshUser() // Refresh user data to see new plan
            // Cleanup URL
            window.history.replaceState({}, "", "/dashboard/subscription")
        }
        if (query.get("checkout_canceled")) {
            toast.info("Paiement annulé.")
        }
    }, [refreshUser])

    // Handle loading or unauthorized
    if (authLoading) return null
    if (!isAuthenticated || !user) return null

    const currentPlan = user.plan_tier || 'free'

    const handleSubscribe = async (priceId: string) => {
        setBillingLoading(true)
        try {
            const token = localStorage.getItem("access_token")
            if (!token) throw new Error("No token found")

            // SIMULATION
            if (priceId === "free") {
                await cancelSubscription(token);
                toast.success("Abonnement annulé. Vous êtes repassé en plan Gratuit.");
            } else {
                let plan: "pro" | "agency" = "pro";
                if (priceId === PRICE_ID_AGENCY) {
                    plan = "agency";
                }
                await simulateUpgrade(plan, token);
                toast.success(`Félicitations ! Vous êtes passé au plan ${plan.toUpperCase()}.`);
            }

            await refreshUser()

        } catch (error: any) {
            toast.error(error.message || "Failed to update subscription")
        } finally {
            setBillingLoading(false)
        }
    }

    const handleManageSubscription = async () => {
        setBillingLoading(true)
        try {
            const token = localStorage.getItem("access_token")
            if (!token) throw new Error("No token found")

            const { url } = await createPortalSession(token)
            if (url) {
                window.location.href = url
            }
        } catch (error: any) {
            toast.error(error.message || "Failed to open billing portal")
        } finally {
            setBillingLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AuthHeader />
            <main className="container mx-auto px-4 py-8 max-w-6xl">
                <div className="mb-10 text-center">
                    <h1 className="text-3xl font-bold tracking-tight mb-2">Abonnements</h1>
                    <p className="text-muted-foreground">
                        Choisissez le plan adapté à vos besoins. Changez d'avis à tout moment.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* STARTER */}
                    <Card className={`relative flex flex-col ${currentPlan === 'free' ? 'border-2 border-primary shadow-md' : 'border-border'}`}>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Shield className="h-5 w-5 text-slate-500" />
                                Starter
                            </CardTitle>
                            <CardDescription>Pour les curieux</CardDescription>
                        </CardHeader>
                        <CardContent className="flex-1">
                            <div className="mb-6">
                                <span className="text-4xl font-bold">0€</span>
                                <span className="text-muted-foreground">/mois</span>
                            </div>
                            <ul className="space-y-3 text-sm">
                                {FEATURES.map((f, i) => {
                                    const val = f.starter;
                                    const unavailable = val === false;
                                    const text = typeof val === 'boolean' ? f.label : `${f.label} : ${val}`;
                                    return <FeatureItem key={i} text={text} unavailable={unavailable} />;
                                })}
                            </ul>
                        </CardContent>
                        <CardFooter>
                            {currentPlan === 'free' ? (
                                <Button className="w-full" variant="outline" disabled>
                                    Plan Actuel
                                </Button>
                            ) : (
                                <Button className="w-full" variant="secondary" onClick={() => handleSubscribe("free")} disabled={billingLoading}>
                                    Passer en Starter
                                </Button>
                            )}
                        </CardFooter>
                    </Card>

                    {/* PRO */}
                    <Card className={`relative flex flex-col ${currentPlan === 'pro' ? 'border-2 border-primary shadow-xl' : 'border-border'}`}>
                        <div className="absolute top-0 right-0 -mr-2 -mt-2 z-10">
                            <Badge className="bg-violet-600 hover:bg-violet-600">Populaire</Badge>
                        </div>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Zap className="h-5 w-5 text-violet-500" />
                                Pro
                            </CardTitle>
                            <CardDescription>Pour les freelances</CardDescription>
                        </CardHeader>
                        <CardContent className="flex-1">
                            <div className="mb-6">
                                <span className="text-4xl font-bold">29€</span>
                                <span className="text-muted-foreground">/mois</span>
                            </div>
                            <ul className="space-y-3 text-sm">
                                {FEATURES.map((f, i) => {
                                    const val = f.pro;
                                    const unavailable = val === false;
                                    const text = typeof val === 'boolean' ? f.label : `${f.label} : ${val}`;
                                    return <FeatureItem key={i} text={text} unavailable={unavailable} />;
                                })}
                            </ul>
                        </CardContent>
                        <CardFooter>
                            {currentPlan === 'pro' ? (
                                <div className="w-full flex flex-col gap-2">
                                    <Button className="w-full bg-green-600 hover:bg-green-700 text-white cursor-default">
                                        <Check className="mr-2 h-4 w-4" /> Plan Actuel
                                    </Button>
                                    <button onClick={handleManageSubscription} className="text-xs text-muted-foreground hover:underline text-center w-full">
                                        Gérer l'abonnement
                                    </button>
                                </div>
                            ) : currentPlan === 'agency' ? (
                                <Button className="w-full" variant="outline" onClick={() => handleSubscribe(PRICE_ID_PRO)} disabled={billingLoading}>
                                    Passer Pro
                                </Button>
                            ) : (
                                <Button className="w-full bg-violet-600 hover:bg-violet-700 text-white" onClick={() => handleSubscribe(PRICE_ID_PRO)} disabled={billingLoading}>
                                    Passer Pro
                                </Button>
                            )}
                        </CardFooter>
                    </Card>

                    {/* AGENCY */}
                    <Card className={`relative flex flex-col ${currentPlan === 'agency' ? 'border-2 border-primary shadow-xl' : 'border-border'}`}>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Building className="h-5 w-5 text-blue-500" />
                                Agency
                            </CardTitle>
                            <CardDescription>Pour les agences web</CardDescription>
                        </CardHeader>
                        <CardContent className="flex-1">
                            <div className="mb-6">
                                <span className="text-4xl font-bold">99€</span>
                                <span className="text-zinc-500">/mois</span>
                            </div>
                            <ul className="space-y-3 text-sm">
                                {FEATURES.map((f, i) => {
                                    const val = f.agency;
                                    const unavailable = val === false;
                                    const text = typeof val === 'boolean' ? f.label : `${f.label} : ${val}`;
                                    return <FeatureItem key={i} text={text} unavailable={unavailable} />;
                                })}
                            </ul>
                        </CardContent>
                        <CardFooter>
                            {currentPlan === 'agency' ? (
                                <div className="w-full flex flex-col gap-2">
                                    <Button className="w-full bg-green-600 hover:bg-green-700 text-white cursor-default">
                                        <Check className="mr-2 h-4 w-4" /> Plan Actuel
                                    </Button>
                                    <button onClick={handleManageSubscription} className="text-xs text-muted-foreground hover:underline text-center w-full">
                                        Gérer l'abonnement
                                    </button>
                                </div>
                            ) : (
                                <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white" onClick={() => handleSubscribe(PRICE_ID_AGENCY)} disabled={billingLoading}>
                                    {currentPlan === 'pro' ? 'Passer Agency' : 'Passer Agency'}
                                </Button>
                            )}
                        </CardFooter>
                    </Card>
                </div>
            </main>
        </div>
    )
}

function FeatureItem({ text, unavailable = false }: { text: string; unavailable?: boolean }) {
    return (
        <li className={`flex items-start gap-2 ${unavailable ? "text-muted-foreground/50" : "text-foreground"}`}>
            {unavailable ? (
                <Minus className="h-4 w-4 mt-0.5" />
            ) : (
                <Check className="h-4 w-4 text-green-500 mt-0.5" />
            )}
            <span>{text}</span>
        </li>
    )
}
