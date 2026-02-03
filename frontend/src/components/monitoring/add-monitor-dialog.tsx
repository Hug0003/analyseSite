"use client"

import { useState } from "react"
import { useForm, SubmitHandler } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { MonitorCreate } from "@/types/monitor"
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

const formSchema = z.object({
    url: z.string().transform((val) => {
        // Remove protocol and www (dot or slash)
        const cleaned = val.replace(/^(?:https?:\/\/)?(?:www[./])?/, "").replace(/\/$/, "").trim();
        return `https://${cleaned}`;
    }).pipe(z.string().url("Please enter a valid URL")),
    frequency: z.enum(["daily", "weekly"]),
    threshold: z.coerce.number().min(0).max(100),
})

type FormValues = z.infer<typeof formSchema>

interface AddMonitorDialogProps {
    onSuccess: () => void
}

export function AddMonitorDialog({ onSuccess }: AddMonitorDialogProps) {
    const [open, setOpen] = useState(false)
    const { isAuthenticated } = useAuth()

    const form = useForm<FormValues>({
        resolver: zodResolver(formSchema) as any,
        defaultValues: {
            url: "",
            frequency: "daily" as const,
            threshold: 80,
        },
    })

    const onSubmit: SubmitHandler<FormValues> = async (values) => {
        console.log("Submitting form with values:", values)

        if (!isAuthenticated) {
            toast.error("You must be logged in to create a monitor")
            return
        }

        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/monitors/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(values),
            })

            if (!response.ok) {
                const error = await response.json()
                throw new Error(error.detail || "Failed to create monitor")
            }

            toast.success("Watchdog activated for " + values.url)
            setOpen(false)
            form.reset()
            onSuccess()
        } catch (error) {
            console.error(error)
            toast.error("Error creating monitor")
        }
    }

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button className="gap-2 bg-gradient-to-r from-blue-600 to-indigo-600">
                    <Plus className="h-4 w-4" />
                    New Monitor
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Add Watchdog Monitor</DialogTitle>
                    <DialogDescription>
                        We will scan this URL automatically and alert you if the score drops.
                    </DialogDescription>
                </DialogHeader>
                <Form {...form}>
                    <form
                        onSubmit={form.handleSubmit(onSubmit, (errors) => {
                            console.error("Form validation errors:", errors)
                            toast.error("Please fix the errors in the form")
                        })}
                        className="space-y-4"
                    >
                        <FormField
                            control={form.control}
                            name="url"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Website URL</FormLabel>
                                    <FormControl>
                                        <Input
                                            placeholder="example.com"
                                            {...field}
                                            onBlur={(e) => {
                                                const cleaned = e.target.value
                                                    .replace(/^(?:https?:\/\/)?(?:www[./])?/, "")
                                                    .replace(/\/$/, "")
                                                    .trim();
                                                field.onChange(cleaned);
                                                field.onBlur();
                                            }}
                                        />
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
                            <FormField
                                control={form.control}
                                name="threshold"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Score Threshold</FormLabel>
                                        <FormControl>
                                            <Input type="number" {...field} />
                                        </FormControl>
                                        <FormDescription>Alert if below {field.value}</FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>
                        <DialogFooter>
                            <Button
                                type="submit"
                                disabled={form.formState.isSubmitting}
                            >
                                {form.formState.isSubmitting ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Creating...
                                    </>
                                ) : (
                                    "Start Monitoring"
                                )}
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    )
}
