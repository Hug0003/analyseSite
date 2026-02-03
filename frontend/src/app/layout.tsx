import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "@/lib/i18n";
import { AuthProvider } from "@/contexts/AuthContext";
import { QueryProvider } from "@/providers/QueryProvider";
import { Toaster } from "sonner";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "SiteAuditor - Free Website Audit Tool | SEO, Security & Performance",
  description: "Analyze any website for SEO, security vulnerabilities, performance metrics, and technology stack. Get a comprehensive audit report in seconds.",
  keywords: ["website audit", "SEO analysis", "security scan", "performance test", "lighthouse", "web audit"],
  authors: [{ name: "SiteAuditor" }],
  openGraph: {
    title: "SiteAuditor - Free Website Audit Tool",
    description: "Analyze any website for SEO, security, performance, and technology stack.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased bg-zinc-950 text-zinc-100`}>
        <AuthProvider>
          <QueryProvider>
            <LanguageProvider>
              {children}
              <Toaster richColors position="top-right" />
            </LanguageProvider>
          </QueryProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
