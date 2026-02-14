"use client";

import { useState, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Upload, Save, Loader2, Palette, Building, Image as ImageIcon } from "lucide-react";
import { toast } from "sonner"; // Assuming sonner is installed, or use basic alert

import { AuthHeader } from "@/components/auth-header";

export default function BrandingSettingsPage() {
    const { user, refreshUser } = useAuth();
    // ... (rest of hook usage)
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);

    // Local state for immediate feedback before save
    const [agencyName, setAgencyName] = useState(user?.agency_name || "");
    const [brandColor, setBrandColor] = useState(user?.brand_color || "#7c3aed");

    // File input ref
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleSaveSettings = async () => {
        // ... (existing implementation)
        setIsLoading(true);
        const token = localStorage.getItem('access_token');

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ''}/api/users/me`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    agency_name: agencyName,
                    brand_color: brandColor
                })
            });

            if (!response.ok) throw new Error("Erreur lors de la sauvegarde");

            await refreshUser();
            // Show success toast (simulated if no library)
            alert("Paramètres de marque sauvegardés !");
        } catch (error) {
            console.error(error);
            alert("Erreur lors de la sauvegarde.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        // ... (existing implementation)
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        const token = localStorage.getItem('access_token');
        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ''}/api/users/me/logo`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) throw new Error("Erreur lors de l'upload");

            await refreshUser();
            alert("Logo mis à jour !");
        } catch (error) {
            console.error(error);
            alert("Impossible d'uploader le logo.");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="min-h-screen bg-zinc-950">
            <AuthHeader />
            <div className="space-y-8 p-6 max-w-7xl mx-auto">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-white">Marque Blanche</h2>
                    <p className="text-zinc-400 mt-2">
                        Personnalisez l'apparence de vos rapports PDF avec votre identité visuelle.
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 relative">
                    {/* Gating Overlay */}
                    {user?.plan_tier !== "agency" && (
                        <div className="absolute inset-0 z-50 backdrop-blur-md bg-zinc-950/50 flex flex-col items-center justify-center text-center p-8 border border-zinc-800 rounded-xl">
                            <div className="p-4 rounded-full bg-violet-500/10 mb-4">
                                <Building className="w-12 h-12 text-violet-400" />
                            </div>
                            <h3 className="text-2xl font-bold text-white mb-2">Marque Blanche</h3>
                            <p className="text-zinc-400 max-w-md mb-6">
                                La personnalisation avancée et la suppression de la mention SiteAuditor nécessitent un plan Agency.
                            </p>
                            <Button
                                className="bg-violet-600 hover:bg-violet-500 text-white"
                                onClick={() => window.location.href = '/pricing'}
                            >
                                Passer au plan Agency
                            </Button>
                        </div>
                    )}
                    {/* Configuration Form */}
                    <Card className="border-zinc-800 bg-black/40 backdrop-blur-xl">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Palette className="w-5 h-5 text-violet-400" />
                                Identité Visuelle
                            </CardTitle>
                            <CardDescription>
                                Configurez les couleurs et informations de votre agence.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">

                            {/* Agency Name */}
                            <div className="space-y-2">
                                <Label htmlFor="agencyName" className="text-zinc-300">Nom de l'Agence</Label>
                                <div className="relative">
                                    <Building className="absolute left-3 top-2.5 h-5 w-5 text-zinc-500" />
                                    <Input
                                        id="agencyName"
                                        placeholder="Ex: My SEO Agency"
                                        className="pl-10 bg-zinc-900/50 border-zinc-700 text-white"
                                        value={agencyName}
                                        onChange={(e) => setAgencyName(e.target.value)}
                                    />
                                </div>
                                <p className="text-xs text-zinc-500">Apparaîtra dans le pied de page des rapports.</p>
                            </div>

                            {/* Brand Color */}
                            <div className="space-y-2">
                                <Label htmlFor="brandColor" className="text-zinc-300">Couleur Principale</Label>
                                <div className="flex items-center gap-4">
                                    <div className="relative overflow-hidden w-12 h-12 rounded-lg border border-zinc-700 shadow-lg">
                                        <input
                                            type="color"
                                            id="brandColor"
                                            value={brandColor}
                                            onChange={(e) => setBrandColor(e.target.value)}
                                            className="absolute top-0 left-0 w-[150%] h-[150%] -translate-x-1/4 -translate-y-1/4 cursor-pointer p-0 border-0"
                                        />
                                    </div>
                                    <Input
                                        value={brandColor}
                                        onChange={(e) => setBrandColor(e.target.value)}
                                        className="flex-1 bg-zinc-900/50 border-zinc-700 text-white font-mono uppercase"
                                        pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
                                    />
                                </div>
                            </div>

                            {/* Logo Upload */}
                            <div className="space-y-2">
                                <Label className="text-zinc-300">Logo Agence</Label>
                                <div className="mt-2 flex items-center justify-center w-full">
                                    <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-zinc-700 border-dashed rounded-lg cursor-pointer bg-zinc-900/30 hover:bg-zinc-900/50 transition-colors">
                                        <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                            {isUploading ? (
                                                <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
                                            ) : (
                                                <Upload className="w-8 h-8 text-zinc-500 mb-2" />
                                            )}
                                            <p className="mb-2 text-sm text-zinc-400">
                                                <span className="font-semibold">Cliquez pour uploader</span> ou glissez-déposez
                                            </p>
                                            <p className="text-xs text-zinc-500">PNG, JPG (MAX. 800x400px)</p>
                                        </div>
                                        <input
                                            type="file"
                                            className="hidden"
                                            accept="image/png, image/jpeg, image/webp"
                                            onChange={handleLogoUpload}
                                            disabled={isUploading}
                                        />
                                    </label>
                                </div>
                            </div>

                            <Button
                                onClick={handleSaveSettings}
                                disabled={isLoading}
                                className="w-full bg-violet-600 hover:bg-violet-700 text-white"
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Sauvegarde...
                                    </>
                                ) : (
                                    <>
                                        <Save className="mr-2 h-4 w-4" />
                                        Sauvegarder les modifications
                                    </>
                                )}
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Live Preview */}
                    <Card className="border-zinc-800 bg-white text-slate-800 overflow-hidden">
                        <CardHeader className="bg-slate-50 border-b border-slate-200">
                            <CardTitle className="text-slate-800 flex items-center gap-2">
                                <ImageIcon className="w-5 h-5 text-slate-500" />
                                Aperçu du Rapport
                            </CardTitle>
                            <CardDescription className="text-slate-500">
                                Simulation du rendu PDF final.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="p-8 space-y-8 bg-white min-h-[500px]">

                            {/* Fake PDF Header */}
                            <div className="flex items-center justify-between border-b pb-6" style={{ borderColor: '#e2e8f0' }}>
                                <div className="flex items-center gap-4">
                                    {user?.logo_url ? (
                                        <img src={user.logo_url} alt="Logo" className="h-20 object-contain max-w-[200px]" />
                                    ) : (
                                        <div className="w-10 h-10 rounded-md flex items-center justify-center text-white font-bold text-xl" style={{ backgroundColor: brandColor }}>
                                            S
                                        </div>
                                    )}
                                    {!user?.logo_url && (
                                        <span className="text-xl font-bold text-slate-600">SiteAuditor</span>
                                    )}
                                </div>
                            </div>

                            {/* Fake Content */}
                            <div className="space-y-6">
                                <div>
                                    <h3 className="text-sm font-semibold text-slate-400 mb-1">AUDIT TECHNIQUE</h3>
                                    <h1 className="text-3xl font-bold text-slate-900">example.com</h1>
                                    <p className="text-sm mt-1" style={{ color: brandColor }}>https://www.example.com</p>
                                </div>

                                <div className="flex justify-center py-8">
                                    <div className="w-40 h-40 rounded-full border-[12px] flex flex-col items-center justify-center bg-slate-50" style={{ borderColor: '#22c55e' }}>
                                        <span className="text-5xl font-bold" style={{ color: '#22c55e' }}>92</span>
                                        <span className="text-xs font-bold text-slate-400 mt-1">SCORE GLOBAL</span>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    {[
                                        { l: 'Sécurité', s: 85 },
                                        { l: 'Performance', s: 92 },
                                        { l: 'SEO', s: 78 },
                                        { l: 'Eco-Index', s: 64 }
                                    ].map((item, i) => (
                                        <div key={i} className="p-3 border rounded-md flex justify-between items-center bg-slate-50 border-slate-200">
                                            <span className="font-bold text-slate-700 text-sm">{item.l}</span>
                                            <span className="px-2 py-1 rounded text-xs font-bold text-white bg-green-600">
                                                {item.s}/100
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Fake Footer */}
                            <div className="mt-12 pt-4 border-t border-slate-200 flex justify-between text-xs text-slate-400">
                                {agencyName ? (
                                    <span>Rapport généré par {agencyName}</span>
                                ) : (
                                    <span>SiteAuditor Confidential</span>
                                )}
                                <span>Page 1 / 6</span>
                            </div>

                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
