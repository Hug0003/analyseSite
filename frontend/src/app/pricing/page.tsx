"use client";

import { useState } from "react";
import { AuthHeader } from "@/components/auth-header";
import { useAuth } from "@/contexts/AuthContext";
import { Check, Shield, Zap, Building, ArrowRight } from "lucide-react";
import { createCheckoutSession, createPortalSession, simulateUpgrade } from "@/lib/api";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { FEATURES } from "@/lib/plans";

export default function PricingPage() {
    const { user, isAuthenticated, loading, refreshUser } = useAuth();
    const router = useRouter();
    const [billingLoading, setBillingLoading] = useState(false);

    // Price IDs - In production, use Environment Variables
    const PRICE_ID_PRO = "price_pro_monthly"; // Replace with real Stripe Price ID
    const PRICE_ID_AGENCY = "price_agency_monthly"; // Replace with real Stripe Price ID

    const handleSubscribe = async (priceId: string) => {
        if (!isAuthenticated) {
            router.push("/login?redirect=/pricing");
            return;
        }

        setBillingLoading(true);
        try {
            const token = localStorage.getItem("access_token");
            if (!token) throw new Error("No token found");

            // SIMULATION: Direct upgrade without Stripe
            let plan: "pro" | "agency" = "pro";
            if (priceId === PRICE_ID_AGENCY) {
                plan = "agency";
            }

            await simulateUpgrade(plan, token);

            // Refresh local user state to reflect changes immediately
            await refreshUser();

            toast.success(`Félicitations ! Vous êtes passé au plan ${plan.toUpperCase()}.`);
            router.push("/dashboard");

        } catch (error: any) {
            toast.error(error.message || "Failed to upgrade");
        } finally {
            setBillingLoading(false);
        }
    };

    const handleManageSubscription = async () => {
        setBillingLoading(true);
        try {
            const token = localStorage.getItem("access_token");
            if (!token) throw new Error("No token found");

            const { url } = await createPortalSession(token);
            if (url) {
                window.location.href = url;
            }
        } catch (error: any) {
            toast.error(error.message || "Failed to open portal");
        } finally {
            setBillingLoading(false);
        }
    };

    const currentPlan = user?.plan_tier || "starter";

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col">
            <AuthHeader />

            <main className="flex-1 max-w-7xl mx-auto px-4 py-16 w-full">
                <div className="text-center mb-16 space-y-4">
                    <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent">
                        Simple, Transparent Pricing
                    </h1>
                    <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
                        Choose the plan that best fits your needs. Upgrade or cancel at any time.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* STARTER PLAN */}
                    <div className="relative p-8 rounded-2xl border border-zinc-800 bg-zinc-900/50 flex flex-col">
                        <div className="mb-4">
                            <h3 className="text-xl font-semibold text-white">Starter</h3>
                            <p className="text-zinc-400 text-sm mt-1">Pour les curieux</p>
                        </div>
                        <div className="mb-6">
                            <span className="text-4xl font-bold text-white">0€</span>
                            <span className="text-zinc-500">/mois</span>
                        </div>

                        <ul className="space-y-3 mb-8 flex-1">
                            {FEATURES.map((f, i) => {
                                const val = f.starter;
                                const unavailable = val === false;
                                const text = typeof val === 'boolean' ? f.label : `${f.label} : ${val}`;
                                return <FeatureItem key={i} text={text} unavailable={unavailable} />;
                            })}
                        </ul>

                        <button
                            disabled
                            className="w-full py-2.5 rounded-lg font-medium text-sm transition-colors border border-zinc-700 bg-zinc-800 text-zinc-400 cursor-not-allowed"
                        >
                            Plan Actuel
                        </button>
                    </div>

                    {/* PRO PLAN */}
                    <div className="relative p-8 rounded-2xl border border-violet-500/20 bg-zinc-900/80 flex flex-col shadow-2xl shadow-violet-900/10 transform scale-105 z-10">
                        <div className="absolute top-0 right-0 -mr-2 -mt-2">
                            <span className="bg-violet-600 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">
                                Populaire
                            </span>
                        </div>
                        <div className="mb-4">
                            <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                                <Zap className="w-5 h-5 text-violet-400" />
                                Pro
                            </h3>
                            <p className="text-zinc-400 text-sm mt-1">Pour les freelances</p>
                        </div>
                        <div className="mb-6">
                            <span className="text-4xl font-bold text-white">29€</span>
                            <span className="text-zinc-500">/mois</span>
                        </div>

                        <ul className="space-y-3 mb-8 flex-1">
                            {FEATURES.map((f, i) => {
                                const val = f.pro;
                                const unavailable = val === false;
                                const text = typeof val === 'boolean' ? f.label : `${f.label} : ${val}`;
                                return <FeatureItem key={i} text={text} unavailable={unavailable} />;
                            })}
                        </ul>

                        {isAuthenticated ? (
                            currentPlan === "pro" ? (
                                <button
                                    onClick={handleManageSubscription}
                                    disabled={billingLoading}
                                    className="w-full py-2.5 rounded-lg font-medium text-sm transition-colors bg-zinc-800 hover:bg-zinc-700 text-white"
                                >
                                    Gérer mon abonnement
                                </button>
                            ) : currentPlan === "agency" ? (
                                <button
                                    disabled
                                    className="w-full py-2.5 rounded-lg font-medium text-sm transition-colors border border-green-900/50 bg-green-900/10 text-green-500"
                                >
                                    Inclus dans Agency
                                </button>
                            ) : (
                                <button
                                    onClick={() => handleSubscribe(PRICE_ID_PRO)}
                                    disabled={billingLoading}
                                    className="w-full py-2.5 rounded-lg font-bold text-sm transition-colors bg-violet-600 hover:bg-violet-700 text-white"
                                >
                                    {billingLoading ? "Activation..." : "Simuler Upgrade Pro"}
                                </button>
                            )
                        ) : (
                            <button
                                onClick={() => router.push("/login?redirect=/pricing")}
                                className="w-full py-2.5 rounded-lg font-bold text-sm transition-colors bg-violet-600 hover:bg-violet-700 text-white"
                            >
                                Commencer avec Pro
                            </button>
                        )}
                    </div>

                    {/* AGENCY PLAN */}
                    <div className="relative p-8 rounded-2xl border border-zinc-800 bg-zinc-900/50 flex flex-col">
                        <div className="mb-4">
                            <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                                <Building className="w-5 h-5 text-blue-400" />
                                Agency
                            </h3>
                            <p className="text-zinc-400 text-sm mt-1">Pour les agences web</p>
                        </div>
                        <div className="mb-6">
                            <span className="text-4xl font-bold text-white">99€</span>
                            <span className="text-zinc-500">/mois</span>
                        </div>

                        <ul className="space-y-3 mb-8 flex-1">
                            {FEATURES.map((f, i) => {
                                const val = f.agency;
                                const unavailable = val === false;
                                const text = typeof val === 'boolean' ? f.label : `${f.label} : ${val}`;
                                return <FeatureItem key={i} text={text} unavailable={unavailable} />;
                            })}
                        </ul>

                        {isAuthenticated ? (
                            currentPlan === "agency" ? (
                                <button
                                    onClick={handleManageSubscription}
                                    disabled={billingLoading}
                                    className="w-full py-2.5 rounded-lg font-medium text-sm transition-colors bg-zinc-800 hover:bg-zinc-700 text-white"
                                >
                                    Gérer mon abonnement
                                </button>
                            ) : (
                                <button
                                    onClick={() => handleSubscribe(PRICE_ID_AGENCY)}
                                    disabled={billingLoading}
                                    className="w-full py-2.5 rounded-lg font-bold text-sm transition-colors bg-blue-600 hover:bg-blue-700 text-white"
                                >
                                    {billingLoading ? "Activation..." : (currentPlan === "pro" ? "Simuler Upgrade Agency" : "Simuler Upgrade Agency")}
                                </button>
                            )
                        ) : (
                            <button
                                onClick={() => router.push("/login?redirect=/pricing")}
                                className="w-full py-2.5 rounded-lg font-bold text-sm transition-colors bg-blue-600 hover:bg-blue-700 text-white"
                            >
                                Commencer avec Agency
                            </button>
                        )}
                    </div>
                </div>

                <div className="mt-20 text-center">
                    <h3 className="text-xl font-semibold mb-6">Frequently Asked Questions</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-left max-w-4xl mx-auto">
                        <FaqItem q="Can I cancel anytime?" a="Yes, you can cancel your subscription at any time. You will continue to have access until the end of your billing period." />
                        <FaqItem q="Do you offer refunds?" a="We offer a 14-day money-back guarantee if you are not satisfied with the product." />
                        <FaqItem q="What is White-label?" a="White-label allows you to generate reports with your own agency branding, logo, and colors, removing all mentions of SiteAuditor." />
                        <FaqItem q="Is the payment secure?" a="Yes, all payments are processed securely by Stripe. We do not store your credit card details." />
                    </div>
                </div>
            </main>

            <footer className="py-8 text-center text-zinc-600 text-sm border-t border-zinc-900">
                <p>© 2026 SiteAuditor. All rights reserved.</p>
            </footer>
        </div>
    );
}

function FeatureItem({ text, unavailable = false }: { text: string; unavailable?: boolean }) {
    return (
        <li className={`flex items-start gap-3 ${unavailable ? "text-zinc-600" : "text-zinc-300"}`}>
            {unavailable ? (
                <span className="mt-1 w-4 h-4 rounded-full border border-zinc-700 flex items-center justify-center opacity-50" />
            ) : (
                <Check className="w-4 h-4 text-green-400 mt-1 shrink-0" />
            )}
            <span className="text-sm">{text}</span>
        </li>
    );
}

function FaqItem({ q, a }: { q: string; a: string }) {
    return (
        <div>
            <h4 className="font-medium text-white mb-2">{q}</h4>
            <p className="text-zinc-400 text-sm leading-relaxed">{a}</p>
        </div>
    )
}
