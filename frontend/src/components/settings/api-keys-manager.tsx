"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { Trash2, Copy, Plus, Terminal, Key, Lock } from "lucide-react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"

interface ApiKey {
    id: number
    name: string
    prefix: string
    created_at: string
    last_used_at: string | null
    is_active: boolean
}

interface NewKeyResponse {
    id: number
    name: string
    prefix: string
    key: string
    created_at: string
}

export function ApiKeysManager() {
    const [keys, setKeys] = useState<ApiKey[]>([])
    const [loading, setLoading] = useState(true)
    const [newKeyName, setNewKeyName] = useState("")
    const [createdKey, setCreatedKey] = useState<NewKeyResponse | null>(null)
    const [isDialogOpen, setIsDialogOpen] = useState(false)
    const { user } = useAuth()

    const fetchKeys = async () => {
        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ''}/api/api-keys/`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (response.ok) {
                const data = await response.json()
                setKeys(data)
            }
        } catch (error) {
            console.error("Failed to fetch keys", error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (user) fetchKeys()
    }, [user])

    const handleCreateKey = async () => {
        if (!newKeyName.trim()) return

        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ''}/api/api-keys/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ name: newKeyName })
            })

            if (!response.ok) throw new Error("Failed to create key")

            const data = await response.json()
            setCreatedKey(data)
            setNewKeyName("")
            fetchKeys()
            toast.success("Clé API créée !")
        } catch (error) {
            toast.error("Erreur lors de la création de la clé")
        }
    }

    const handleDeleteKey = async (id: number) => {
        if (!confirm("Êtes-vous sûr de vouloir révoquer cette clé ? Cette action est irréversible.")) return

        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ''}/api/api-keys/${id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            })

            if (response.ok) {
                setKeys(keys.filter(k => k.id !== id))
                toast.success("Clé révoquée")
            }
        } catch (error) {
            toast.error("Erreur lors de la suppression")
        }
    }

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text)
        toast.success("Copié dans le presse-papier")
    }

    return (
        <Card className="bg-background/60 backdrop-blur-sm border-zinc-800">
            <CardHeader>
                <div className="flex justify-between items-center">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <Key className="w-5 h-5 text-yellow-500" />
                            Clés d'API
                        </CardTitle>
                        <CardDescription>
                            Gérez les clés pour l'intégration CI/CD et l'API
                        </CardDescription>
                    </div>
                    {user?.plan_tier === "agency" ? (
                        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                            <DialogTrigger asChild>
                                <Button size="sm" className="gap-2">
                                    <Plus className="w-4 h-4" />
                                    Nouvelle Clé
                                </Button>
                            </DialogTrigger>
                            <DialogContent className="sm:max-w-md bg-zinc-950 border-zinc-800">
                                <DialogHeader>
                                    <DialogTitle>Créer une nouvelle clé d'API</DialogTitle>
                                    <DialogDescription>
                                        Donnez un nom à cette clé pour l'identifier (ex: "GitHub Actions", "Laptop Pro").
                                    </DialogDescription>
                                </DialogHeader>
                                {!createdKey ? (
                                    <div className="space-y-4 py-4">
                                        <div className="space-y-2">
                                            <Input
                                                placeholder="Nom de la clé..."
                                                value={newKeyName}
                                                onChange={(e) => setNewKeyName(e.target.value)}
                                            />
                                        </div>
                                        <Button onClick={handleCreateKey} disabled={!newKeyName.trim()} className="w-full">
                                            Générer la clé
                                        </Button>
                                    </div>
                                ) : (
                                    <div className="space-y-4 py-4">
                                        <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-md">
                                            <p className="text-sm text-yellow-500 mb-2 font-semibold">
                                                ATTENTION : Copiez cette clé maintenant. Vous ne pourrez plus la voir par la suite !
                                            </p>
                                            <div className="flex items-center gap-2 bg-black/50 p-2 rounded border border-zinc-800">
                                                <code className="flex-1 text-sm font-mono text-zinc-300 break-all">
                                                    {createdKey.key}
                                                </code>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    className="h-8 w-8 p-0"
                                                    onClick={() => copyToClipboard(createdKey.key)}
                                                >
                                                    <Copy className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </div>
                                        <DialogFooter>
                                            <Button onClick={() => { setIsDialogOpen(false); setCreatedKey(null); }}>
                                                J'ai copié la clé
                                            </Button>
                                        </DialogFooter>
                                    </div>
                                )}
                            </DialogContent>
                        </Dialog>
                    ) : (
                        <Button variant="outline" size="sm" className="gap-2 opacity-50 cursor-not-allowed" onClick={() => window.location.href = '/pricing'}>
                            <Lock className="w-4 h-4" />
                            Agency Plan Required
                        </Button>
                    )}
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {loading ? (
                        <div className="text-center py-4 text-zinc-500">Chargement...</div>
                    ) : keys.length === 0 ? (
                        <div className="text-center py-8 border border-dashed border-zinc-800 rounded-lg">
                            <Terminal className="w-8 h-8 mx-auto text-zinc-600 mb-2" />
                            <p className="text-zinc-500">Aucune clé d'API active.</p>
                            <p className="text-xs text-zinc-600">Créez-en une pour automatiser vos tests de sécurité.</p>
                        </div>
                    ) : (
                        <div className="grid gap-3">
                            {keys.map((key) => (
                                <div key={key.id} className="flex items-center justify-between p-3 rounded-lg border border-zinc-800 bg-zinc-900/50 hover:bg-zinc-900 transition-colors">
                                    <div className="flex flex-col gap-1">
                                        <div className="flex items-center gap-2">
                                            <span className="font-medium text-zinc-200">{key.name}</span>
                                            <Badge variant="outline" className="text-[10px] text-zinc-500 border-zinc-700 h-5">
                                                {key.prefix}...
                                            </Badge>
                                        </div>
                                        <div className="text-xs text-zinc-500 flex gap-3">
                                            <span>Créée le {new Date(key.created_at).toLocaleDateString()}</span>
                                            {key.last_used_at && (
                                                <span className="text-emerald-500/80">
                                                    • Dernière utilisation : {new Date(key.last_used_at).toLocaleDateString()}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="text-zinc-500 hover:text-red-400 hover:bg-red-500/10"
                                        onClick={() => handleDeleteKey(key.id)}
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Integration Hints */}
                    {keys.length > 0 && (
                        <div className="mt-6 p-4 bg-zinc-950 rounded-lg border border-zinc-800">
                            <h4 className="text-sm font-semibold text-zinc-300 mb-2 flex items-center gap-2">
                                <Terminal className="w-4 h-4" />
                                Exemple d'intégration CI/CD
                            </h4>
                            <div className="relative group">
                                <pre className="bg-black p-3 rounded text-xs text-zinc-400 overflow-x-auto font-mono">
                                    {`# .github/workflows/security.yml
steps:
  - name: SiteAuditor Scan
    run: |
      curl -X POST "${process.env.NEXT_PUBLIC_API_URL || 'https://api.siteauditor.com'}/api/v1/scan" \\
        -H "X-API-Key: \${{ secrets.SITE_AUDITOR_KEY }}" \\
        -H "Content-Type: application/json" \\
        -d '{"url": "https://staging.example.com", "threshold": 80}'`}
                                </pre>
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity h-6 text-xs"
                                    onClick={() => copyToClipboard(`curl -X POST "${process.env.NEXT_PUBLIC_API_URL}/api/v1/scan" ...`)}
                                >
                                    Copier
                                </Button>
                            </div>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    )
}
