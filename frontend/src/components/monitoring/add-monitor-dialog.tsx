"use client"

import { useState, useEffect } from "react"
import { useForm, SubmitHandler } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { useAuth } from "@/contexts/AuthContext"
import { toast } from "sonner"
import { Plus, Loader2 } from "lucide-react"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? ""

const formSchema = z.object({
    url: z.string()
        .min(3, "URL is required")
        .transform((val) => {
            // Auto-add https:// if missing
            if (!/^https?:\/\//i.test(val)) {
                return `https://${val}`
            }
            return val
        })
        .pipe(z.string().url("Please enter a valid URL (e.g. example.com)")),
    frequency: z.enum(["daily", "weekly"]),
    alert_threshold: z.coerce.number().min(1).max(100),
    check_hour: z.coerce.number().min(0).max(23),
    check_day: z.coerce.number().min(0).max(6).optional(),
})

type FormValues = z.infer<typeof formSchema>

interface AddMonitorDialogProps {
    onSuccess: () => void
}

export function AddMonitorDialog({ onSuccess }: AddMonitorDialogProps) {
    const [open, setOpen] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const { user } = useAuth()
    const [monitorCount, setMonitorCount] = useState<number | null>(null)

    const form = useForm<FormValues>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            url: "",
            frequency: "daily",
            alert_threshold: 80,
            check_hour: 9,
        },
    })

    // Calculate limit based on plan
    const getLimit = () => {
        switch (user?.plan_tier) {
            case "agency": return 9999;
            case "pro": return 10;
            default: return 1; // starter
        }
    }
    const limit = getLimit()

    // Fetch count logic
    const fetchCount = async () => {
        try {
            const token = localStorage.getItem('access_token')
            if (!token) return
            const res = await fetch(`${API_BASE}/api/monitors`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) {
                const data = await res.json()
                setMonitorCount(data.length)
            }
        } catch (e) {
            console.error(e)
        }
    }

    // Refresh count when user changes
    useEffect(() => {
        if (user) fetchCount()
    }, [user])

    const onSubmit: SubmitHandler<FormValues> = async (data) => {
        setIsLoading(true)
        if (!user) {
            toast.error("You must be logged in to create a monitor")
            setIsLoading(false)
            return
        }

        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch(`${API_BASE}/api/monitors`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(data),
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                if (response.status === 403) {
                    toast.error("Plan Limit Reached", {
                        description: errorData.detail || "Upgrade your plan to add more monitors."
                    })
                    return
                }
                const msg = Array.isArray(errorData.detail) ? errorData.detail.map((e: any) => e.msg || e).join(", ") : (errorData.detail || "Failed to create monitor")
                throw new Error(msg)
            }

            toast.success("Watchdog activated for " + data.url)
            setOpen(false)
            form.reset()
            onSuccess()
            fetchCount() // Refresh local count
        } catch (error) {
            console.error("Error creating monitor:", error)
            toast.error(error instanceof Error ? error.message : "Error creating monitor", {
                description: "Please try again later."
            })
        } finally {
            setIsLoading(false)
        }
    }

    const isLimitReached = monitorCount !== null && monitorCount >= limit

    return (
        <Dialog open={open} onOpenChange={(val) => {
            if (val) fetchCount()
            setOpen(val)
        }}>
            <DialogTrigger asChild>
                <Button className="gap-2 bg-gradient-to-r from-blue-600 to-indigo-600" variant={isLimitReached ? "outline" : "default"}>
                    <Plus className="h-4 w-4" />
                    {isLimitReached ? "Limit Reached" : "Add Monitor"}
                    {monitorCount !== null && (
                        <span className="ml-1 text-xs opacity-80 bg-black/20 px-1.5 py-0.5 rounded-full">
                            {monitorCount}/{limit}
                        </span>
                    )}
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Add New Monitor</DialogTitle>
                    <DialogDescription>
                        Configure a new URL to be monitored automatically.
                    </DialogDescription>
                </DialogHeader>

                {isLimitReached ? (
                    <div className="py-6 text-center space-y-4">
                        <div className="p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg inline-block">
                            <span className="text-orange-500 font-semibold">
                                {monitorCount}/{limit} Monitors Used
                            </span>
                        </div>
                        <p className="text-muted-foreground text-sm">
                            You have reached the maximum number of monitors for your <strong>{user?.plan_tier || 'Starter'}</strong> plan.
                        </p>
                        <Button className="w-full bg-violet-600 hover:bg-violet-500" onClick={() => window.location.href = '/pricing'}>
                            Upgrade Plan
                        </Button>
                    </div>
                ) : (
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                            <FormField
                                control={form.control}
                                name="url"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>URL to Monitor</FormLabel>
                                        <FormControl>
                                            <Input placeholder="https://example.com" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="check_hour"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Preferred Check Hour (UTC)</FormLabel>
                                        <FormControl>
                                            <Input type="number" min={0} max={23} {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <div className="grid grid-cols-2 gap-4">
                                <FormField
                                    control={form.control}
                                    name="frequency"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Frequency</FormLabel>
                                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                                                <FormControl>
                                                    <SelectTrigger>
                                                        <SelectValue placeholder="Select frequency" />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent>
                                                    <SelectItem value="daily">Daily</SelectItem>
                                                    <SelectItem value="weekly">Weekly</SelectItem>
                                                </SelectContent>
                                            </Select>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                                {form.watch("frequency") === "weekly" && (
                                    <FormField
                                        control={form.control}
                                        name="check_day"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>On which day?</FormLabel>
                                                <Select onValueChange={(val) => field.onChange(parseInt(val))} defaultValue={field.value?.toString() || "0"}>
                                                    <FormControl>
                                                        <SelectTrigger>
                                                            <SelectValue placeholder="Select day" />
                                                        </SelectTrigger>
                                                    </FormControl>
                                                    <SelectContent>
                                                        <SelectItem value="0">Monday</SelectItem>
                                                        <SelectItem value="1">Tuesday</SelectItem>
                                                        <SelectItem value="2">Wednesday</SelectItem>
                                                        <SelectItem value="3">Thursday</SelectItem>
                                                        <SelectItem value="4">Friday</SelectItem>
                                                        <SelectItem value="5">Saturday</SelectItem>
                                                        <SelectItem value="6">Sunday</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                )}
                            </div>

                            <FormField
                                control={form.control}
                                name="alert_threshold"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Alert Sensitivity (Score Drop)</FormLabel>
                                        <FormControl>
                                            <div className="relative">
                                                <Input type="number" {...field} className="pr-8" />
                                                <span className="absolute right-3 top-2.5 text-sm text-muted-foreground">%</span>
                                            </div>
                                        </FormControl>
                                        <FormDescription>Alert if score drops below</FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <DialogFooter>
                                <Button type="submit" disabled={isLoading}>
                                    {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    Create Monitor
                                </Button>
                            </DialogFooter>
                        </form>
                    </Form>
                )}
            </DialogContent>
        </Dialog>
    )
}
