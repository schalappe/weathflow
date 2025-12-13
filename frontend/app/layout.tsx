import type { Metadata } from "next";
import { Space_Grotesk, IBM_Plex_Mono } from "next/font/google";
import Link from "next/link";
import { Toaster } from "sonner";
import { ThemeProvider } from "@/components/ui/theme-provider";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Separator } from "@/components/ui/separator";
import { LayoutDashboard, Upload, TrendingUp, Wallet } from "lucide-react";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Money Map Manager",
  description: "Personal finance with the 50/30/20 framework",
};

function NavBar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        {/* Logo and Brand */}
        <Link href="/" className="group flex items-center gap-3">
          <div className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-violet-500 via-purple-500 to-indigo-600 shadow-lg shadow-violet-500/20 transition-all duration-300 group-hover:shadow-violet-500/30 group-hover:scale-105">
            <Wallet className="h-4.5 w-4.5 text-white" strokeWidth={2.5} />
            <div className="absolute inset-0 bg-gradient-to-t from-black/10 to-transparent" />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-semibold tracking-tight text-foreground">
              Money Map
            </span>
            <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
              50 / 30 / 20
            </span>
          </div>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center">
          <div className="flex items-center gap-1 rounded-full bg-muted/50 p-1">
            <NavLink href="/" icon={<LayoutDashboard className="h-4 w-4" />}>
              Dashboard
            </NavLink>
            <NavLink href="/import" icon={<Upload className="h-4 w-4" />}>
              Import
            </NavLink>
            <NavLink href="/history" icon={<TrendingUp className="h-4 w-4" />}>
              History
            </NavLink>
          </div>
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

function NavLink({
  href,
  icon,
  children,
}: {
  href: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium text-muted-foreground transition-all duration-200 hover:bg-background hover:text-foreground hover:shadow-sm"
    >
      {icon}
      <span className="hidden sm:inline">{children}</span>
    </Link>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('theme');if(t==='dark'){document.documentElement.classList.add('dark')}}catch(e){}})()`,
          }}
        />
      </head>
      <body
        className={`${spaceGrotesk.variable} ${ibmPlexMono.variable} antialiased min-h-screen bg-background`}
      >
        <ThemeProvider>
          <div className="relative flex min-h-screen flex-col">
            <NavBar />
            <main className="flex-1">
              <div className="mx-auto max-w-7xl px-6 py-8">{children}</div>
            </main>
            {/* Subtle footer */}
            <footer className="border-t border-border/50 py-6">
              <div className="mx-auto max-w-7xl px-6">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Money Map Manager</span>
                  <span>Built for the 50/30/20 framework</span>
                </div>
              </div>
            </footer>
          </div>
          <Toaster richColors position="bottom-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
