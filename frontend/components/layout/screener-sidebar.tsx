"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  TrendingUp,
  Target,
  Activity,
  BarChart3,
  TrendingDown,
  Eye,
  Layers,
  PieChart,
  Building2,
  GitCompare,
  ChevronLeft,
  ChevronRight,
  Menu,
  Gauge,
  GitMerge,
  Expand,
  Compass,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

const screenerLinks = [
  {
    id: "home",
    name: "Home",
    href: "/",
    icon: Home,
    description: "Dashboard overview",
  },
  {
    id: "rrg",
    name: "RRG Charts",
    href: "/screeners/rrg",
    icon: GitCompare,
    description: "Sector rotation",
  },
  {
    id: "rs-leaders",
    name: "RS Leaders",
    href: "/screeners/rs-leaders",
    icon: TrendingUp,
    description: "97 Club stocks",
  },
  {
    id: "breakouts",
    name: "4% Breakouts",
    href: "/screeners/breakouts",
    icon: Target,
    description: "Daily breakouts",
  },
  {
    id: "high-volume",
    name: "High Volume",
    href: "/screeners/high-volume",
    icon: Activity,
    description: "Volume movers",
  },
  {
    id: "ma-stacked",
    name: "MA Stacked",
    href: "/screeners/ma-stacked",
    icon: BarChart3,
    description: "VCP patterns",
  },
  {
    id: "weekly-movers",
    name: "Weekly Movers",
    href: "/screeners/weekly-movers",
    icon: TrendingDown,
    description: "20%+ weekly",
  },
  {
    id: "momentum",
    name: "Momentum",
    href: "/screeners/momentum-watchlist",
    icon: Eye,
    description: "High RS watchlist",
  },
  {
    id: "stage",
    name: "Stage Analysis",
    href: "/screeners/stage-analysis",
    icon: Layers,
    description: "Market stages",
  },
  {
    id: "breadth",
    name: "Breadth",
    href: "/screeners/breadth-metrics",
    icon: PieChart,
    description: "Market health",
  },
  {
    id: "industries",
    name: "Industries",
    href: "/screeners/leading-industries",
    icon: Building2,
    description: "Sector leaders",
  },
  {
    id: "rsi",
    name: "RSI Scanner",
    href: "/screeners/rsi-scanner",
    icon: Gauge,
    description: "Overbought/oversold",
  },
  {
    id: "macd",
    name: "MACD Crossover",
    href: "/screeners/macd-crossover",
    icon: GitMerge,
    description: "Momentum shifts",
  },
  {
    id: "bollinger",
    name: "Bollinger Squeeze",
    href: "/screeners/bollinger-squeeze",
    icon: Expand,
    description: "Volatility setups",
  },
  {
    id: "adx",
    name: "ADX Trend",
    href: "/screeners/adx-trend",
    icon: Compass,
    description: "Trend strength",
  },
];

// Shared navigation component
function NavigationLinks({ isCollapsed = false, onLinkClick }: { isCollapsed?: boolean; onLinkClick?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex-1 overflow-y-auto p-2">
      <ul className="space-y-1">
        {screenerLinks.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;

          return (
            <li key={link.id}>
              <Link
                href={link.href}
                onClick={onLinkClick}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 transition-colors",
                  "hover:bg-accent hover:text-accent-foreground",
                  isActive && "bg-accent text-accent-foreground font-medium",
                  isCollapsed && "justify-center"
                )}
                title={isCollapsed ? link.name : undefined}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                {!isCollapsed && (
                  <div className="flex flex-col">
                    <span className="text-sm">{link.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {link.description}
                    </span>
                  </div>
                )}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

// Desktop sidebar component
function DesktopSidebar() {
  const [isCollapsed, setIsCollapsed] = React.useState(false);

  return (
    <div
      className={cn(
        "hidden md:flex relative flex-col border-r bg-background transition-all duration-300",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header with toggle button */}
      <div className="flex h-16 items-center justify-between border-b px-4">
        {!isCollapsed && (
          <h2 className="text-lg font-semibold">Screeners</h2>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={cn("h-8 w-8", isCollapsed && "mx-auto")}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      <NavigationLinks isCollapsed={isCollapsed} />

      {/* Footer info (only when expanded) */}
      {!isCollapsed && (
        <div className="border-t p-4">
          <div className="text-xs text-muted-foreground">
            <div className="font-medium mb-1">Indian Stock Screener</div>
            <div>NSE data updated daily</div>
          </div>
        </div>
      )}
    </div>
  );
}

// Mobile hamburger menu
export function MobileNav() {
  const [open, setOpen] = React.useState(false);

  return (
    <div className="md:hidden fixed top-4 left-4 z-50">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <button className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 border border-input bg-background shadow-xs hover:bg-accent hover:text-accent-foreground h-9 w-9">
            <Menu className="h-5 w-5" />
          </button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <div className="flex flex-col h-full">
            <div className="flex h-16 items-center border-b px-4">
              <h2 className="text-lg font-semibold">Screeners</h2>
            </div>
            <NavigationLinks onLinkClick={() => setOpen(false)} />
            <div className="border-t p-4">
              <div className="text-xs text-muted-foreground">
                <div className="font-medium mb-1">Indian Stock Screener</div>
                <div>NSE data updated daily</div>
              </div>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}

// Main sidebar export
export function ScreenerSidebar() {
  return <DesktopSidebar />;
}
