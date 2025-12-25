# Frontend Implementation Plan - Phase 2

## Executive Summary

Building a modern, clean stock screener platform with:
- **Next.js 14+** (React framework with App Router)
- **Shadcn/ui** (beautiful, customizable components)
- **Supabase Auth** (email OTP + Google/GitHub social)
- **TradingView Lightweight Charts** (OHLCV visualization)
- **Plotly.js** (heatmaps, RRG charts, complex visualizations)
- **Deployment**: Vercel (cloud) + Docker support (local dev)
- **Design**: Clean, minimal, desktop-first responsive

### **Repository Strategy: Monorepo (Single Repository)**

**Decision**: Frontend will be added to the existing `/screener` repository as `frontend/` directory.

**Rationale**:
- ✅ Single developer workflow (you + Claude)
- ✅ Shared documentation (.claude/, CLAUDE.md)
- ✅ Type safety across stack (Pydantic → TypeScript)
- ✅ Coordinated deployments (docker-compose.yml)
- ✅ Atomic full-stack changes (single PR for backend + frontend)
- ✅ Easier for Claude to maintain context across stack
- ✅ Vercel supports monorepos natively (path-based builds)

**Structure**:
```
/screener (existing repo)
├── .claude/                    # Shared planning docs
├── backend/                    # Existing FastAPI backend
├── frontend/                   # NEW - Next.js frontend
├── n8n/                        # Existing workflows
├── docker-compose.yml          # ALL services together
└── CLAUDE.md                   # Single source of truth
```

---

## 1. Tech Stack Finalized

### Core Framework
- **Next.js 14.2+** with App Router (React 18+)
- **TypeScript** for type safety
- **Tailwind CSS** for styling

### UI Components
- **Shadcn/ui** - Base component library
- **TanStack Table v8** - Advanced data tables (built into Shadcn DataTable)
- **React Hook Form** - Form state management
- **Zod** - Schema validation

### Data Visualization
- **TradingView Lightweight Charts** - OHLCV candlestick charts
- **Plotly.js** - RRG quadrant charts, heatmaps, complex visualizations
- **Recharts** (optional) - Simple statistical charts if needed

### State Management & Data Fetching
- **React Query (TanStack Query v5)** - Server state management
- **Zustand** (lightweight) - Client state (UI preferences, filters)
- **React Context** - Theme, auth state

### Authentication
- **Supabase Auth** - Email OTP, Google OAuth, GitHub OAuth
- **Supabase Client** - Auth SDK (@supabase/supabase-js)

### Database Integration
- **Backend API**: Existing FastAPI backend (http://localhost:8000/api/v1)
- **User Data Storage**: Supabase PostgreSQL (dashboard layouts, preferences)
- **App Data Storage**: Existing PostgreSQL (securities, OHLCV, screener data)

### Deployment
- **Primary**: Vercel (automatic deployments from GitHub)
- **Local Dev**: Docker container in docker-compose.yml
- **Build Tool**: Next.js built-in (Turbopack for dev, Webpack for prod)

### Developer Tools
- **Shadcn MCP Server** - Component discovery during development
- **ESLint + Prettier** - Code quality
- **Vitest + React Testing Library** - Unit/integration tests

---

## 2. Project Structure

```
/screener
├── frontend/
│   ├── .next/                      # Next.js build output (gitignored)
│   ├── public/                     # Static assets
│   │   ├── images/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── app/                    # Next.js 14 App Router
│   │   │   ├── (auth)/             # Auth route group
│   │   │   │   ├── login/
│   │   │   │   └── signup/
│   │   │   ├── (dashboard)/        # Main app route group
│   │   │   │   ├── dashboard/      # Customizable dashboard
│   │   │   │   ├── screeners/      # All screeners
│   │   │   │   │   ├── rrg-charts/
│   │   │   │   │   ├── breakouts-4percent/
│   │   │   │   │   ├── weekly-movers/
│   │   │   │   │   └── [other 8 screeners]/
│   │   │   │   ├── analysis/       # Future: custom analysis
│   │   │   │   └── settings/       # User preferences
│   │   │   ├── api/                # Next.js API routes (proxy to backend)
│   │   │   ├── layout.tsx          # Root layout (providers)
│   │   │   ├── page.tsx            # Landing page
│   │   │   └── globals.css         # Global Tailwind styles
│   │   ├── components/
│   │   │   ├── ui/                 # Shadcn components (copy-paste)
│   │   │   │   ├── button.tsx
│   │   │   │   ├── data-table.tsx  # TanStack Table wrapper
│   │   │   │   ├── date-picker.tsx
│   │   │   │   └── [30+ components]
│   │   │   ├── charts/             # Reusable chart components
│   │   │   │   ├── ohlcv-chart.tsx         # TradingView wrapper
│   │   │   │   ├── rrg-chart.tsx           # Plotly RRG
│   │   │   │   └── heatmap-chart.tsx       # Plotly heatmap
│   │   │   ├── screeners/          # Screener-specific components
│   │   │   │   ├── rrg-screener.tsx
│   │   │   │   ├── breakout-screener.tsx
│   │   │   │   └── [other screeners]
│   │   │   ├── dashboard/          # Dashboard widgets
│   │   │   │   ├── widget-container.tsx
│   │   │   │   ├── widget-rrg.tsx
│   │   │   │   ├── widget-table.tsx
│   │   │   │   └── widget-metric.tsx
│   │   │   ├── layout/             # App layout components
│   │   │   │   ├── header.tsx
│   │   │   │   ├── sidebar.tsx
│   │   │   │   └── footer.tsx
│   │   │   └── auth/               # Auth components
│   │   │       ├── login-form.tsx
│   │   │       ├── social-auth.tsx
│   │   │       └── protected-route.tsx
│   │   ├── lib/
│   │   │   ├── api/                # API client functions
│   │   │   │   ├── screeners.ts    # Screener endpoints
│   │   │   │   ├── status.ts       # Status endpoints
│   │   │   │   └── health.ts       # Health checks
│   │   │   ├── supabase/           # Supabase integration
│   │   │   │   ├── client.ts       # Browser client
│   │   │   │   ├── server.ts       # Server-side client
│   │   │   │   └── middleware.ts   # Auth middleware
│   │   │   ├── hooks/              # Custom React hooks
│   │   │   │   ├── use-screener.ts
│   │   │   │   ├── use-dashboard.ts
│   │   │   │   └── use-auth.ts
│   │   │   ├── stores/             # Zustand stores
│   │   │   │   ├── filter-store.ts
│   │   │   │   └── ui-store.ts
│   │   │   ├── utils/              # Utility functions
│   │   │   │   ├── cn.ts           # Tailwind class merger
│   │   │   │   ├── format.ts       # Number/date formatters
│   │   │   │   └── validators.ts   # Zod schemas
│   │   │   └── constants.ts        # App constants
│   │   └── types/
│   │       ├── screener.ts         # Screener data types
│   │       ├── security.ts         # Security/stock types
│   │       └── dashboard.ts        # Dashboard types
│   ├── .env.local                  # Environment variables (gitignored)
│   ├── .env.example                # Template for .env.local
│   ├── Dockerfile                  # Production container
│   ├── Dockerfile.dev              # Development container
│   ├── docker-compose.yml          # Local dev stack (optional)
│   ├── next.config.mjs             # Next.js configuration
│   ├── tailwind.config.ts          # Tailwind configuration
│   ├── tsconfig.json               # TypeScript configuration
│   ├── package.json                # Dependencies
│   └── README.md                   # Setup instructions
│
├── docker-compose.yml              # Root compose (postgres, backend, frontend)
└── [existing backend files]
```

---

## 3. Implementation Phases

### **Phase 2.0: Project Setup & Infrastructure (Week 1)**

#### 2.0.1 Initialize Next.js Project
```bash
cd /Users/mayanklavania/projects/screener
npx create-next-app@latest frontend --typescript --tailwind --app --use-npm
cd frontend
```

**Configuration choices:**
- ✅ TypeScript
- ✅ ESLint
- ✅ Tailwind CSS
- ✅ `src/` directory
- ✅ App Router (not Pages Router)
- ❌ Turbopack (use default Webpack for stability)
- ✅ Import alias: `@/*`

#### 2.0.2 Install Core Dependencies
```bash
# Shadcn/ui setup
npx shadcn@latest init

# State management
npm install @tanstack/react-query zustand

# Supabase
npm install @supabase/supabase-js @supabase/auth-helpers-nextjs

# Charts
npm install lightweight-charts plotly.js react-plotly.js
npm install --save-dev @types/plotly.js

# Form handling
npm install react-hook-form zod @hookform/resolvers

# Utilities
npm install date-fns clsx tailwind-merge
npm install --save-dev @types/node
```

#### 2.0.3 Shadcn Component Installation
```bash
# Install core components (via MCP server during dev)
npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add card
npx shadcn@latest add table
npx shadcn@latest add dropdown-menu
npx shadcn@latest add tabs
npx shadcn@latest add dialog
npx shadcn@latest add toast
npx shadcn@latest add skeleton
npx shadcn@latest add calendar
npx shadcn@latest add popover
npx shadcn@latest add select
npx shadcn@latest add badge
npx shadcn@latest add avatar
npx shadcn@latest add separator
npx shadcn@latest add switch
npx shadcn@latest add label
npx shadcn@latest add form
```

#### 2.0.4 Docker Configuration
**File**: `frontend/Dockerfile`
```dockerfile
FROM node:20-alpine AS base

# Dependencies
FROM base AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Runner
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

**File**: `frontend/Dockerfile.dev` (for local development)
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
```

**Update Root**: `/Users/mayanklavania/projects/screener/docker-compose.yml`
```yaml
services:
  postgres:
    # ... existing config

  backend:
    # ... existing config

  n8n:
    # ... existing config

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: screener_frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_API_URL=http://backend:8000/api/v1
      - NEXT_PUBLIC_SUPABASE_URL=${SUPABASE_URL}
      - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    networks:
      - screener_network
    depends_on:
      - backend
    restart: unless-stopped

networks:
  screener_network:
    driver: bridge
```

#### 2.0.5 Environment Configuration
**File**: `frontend/.env.example`
```bash
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Optional: Analytics, monitoring
NEXT_PUBLIC_GA_ID=
```

**File**: `frontend/.env.local` (gitignored, user creates from template)

#### 2.0.6 Next.js Configuration
**File**: `frontend/next.config.mjs`
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // For Docker
  reactStrictMode: true,
  images: {
    domains: ['your-supabase-project.supabase.co'], // For Supabase avatars
  },
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*`,
      },
    ];
  },
  webpack: (config) => {
    // Fix for plotly.js
    config.resolve.alias = {
      ...config.resolve.alias,
      'plotly.js': 'plotly.js/dist/plotly.js',
    };
    return config;
  },
};

export default nextConfig;
```

#### 2.0.7 Tailwind Configuration
**File**: `frontend/tailwind.config.ts`
```typescript
import type { Config } from "tailwindcss"

const config = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        // ... Shadcn default colors
        bull: "#22c55e", // Green for positive movements
        bear: "#ef4444", // Red for negative movements
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config

export default config
```

---

### **Phase 2.1: Authentication Setup (Week 1-2)**

#### 2.1.1 Supabase Client Configuration
**File**: `frontend/src/lib/supabase/client.ts`
```typescript
import { createBrowserClient } from '@supabase/supabase-js'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

**File**: `frontend/src/lib/supabase/server.ts`
```typescript
import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { cookies } from 'next/headers'

export function createClient() {
  const cookieStore = cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          cookieStore.set({ name, value, ...options })
        },
        remove(name: string, options: CookieOptions) {
          cookieStore.set({ name, value: '', ...options })
        },
      },
    }
  )
}
```

#### 2.1.2 Supabase Database Schema (User Data)
```sql
-- Create in Supabase dashboard (via SQL Editor)

-- User profiles (extends auth.users)
CREATE TABLE public.profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Dashboard layouts
CREATE TABLE public.dashboard_layouts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL DEFAULT 'My Dashboard',
  widgets JSONB NOT NULL DEFAULT '[]'::jsonb,
  is_default BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
  CONSTRAINT unique_user_dashboard_name UNIQUE (user_id, name)
);

-- User preferences
CREATE TABLE public.user_preferences (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE,
  theme TEXT DEFAULT 'light' CHECK (theme IN ('light', 'dark')),
  default_screener TEXT,
  notifications_enabled BOOLEAN DEFAULT TRUE,
  preferences JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Saved screener filters
CREATE TABLE public.saved_filters (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  screener_name TEXT NOT NULL,
  filter_name TEXT NOT NULL,
  filters JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
  CONSTRAINT unique_user_screener_filter UNIQUE (user_id, screener_name, filter_name)
);

-- Row Level Security (RLS) policies
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dashboard_layouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_filters ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

-- Dashboard layouts policies
CREATE POLICY "Users can manage own layouts"
  ON public.dashboard_layouts FOR ALL
  USING (auth.uid() = user_id);

-- User preferences policies
CREATE POLICY "Users can manage own preferences"
  ON public.user_preferences FOR ALL
  USING (auth.uid() = user_id);

-- Saved filters policies
CREATE POLICY "Users can manage own filters"
  ON public.saved_filters FOR ALL
  USING (auth.uid() = user_id);

-- Trigger to create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (new.id, new.email, new.raw_user_meta_data->>'full_name');

  INSERT INTO public.user_preferences (user_id)
  VALUES (new.id);

  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

#### 2.1.3 Auth Middleware
**File**: `frontend/src/middleware.ts`
```typescript
import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          request.cookies.set({
            name,
            value,
            ...options,
          })
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          })
          response.cookies.set({
            name,
            value,
            ...options,
          })
        },
        remove(name: string, options: CookieOptions) {
          request.cookies.set({
            name,
            value: '',
            ...options,
          })
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          })
          response.cookies.set({
            name,
            value: '',
            ...options,
          })
        },
      },
    }
  )

  const {
    data: { user },
  } = await supabase.auth.getUser()

  // Protected routes
  if (!user && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Redirect authenticated users away from auth pages
  if (user && (request.nextUrl.pathname === '/login' || request.nextUrl.pathname === '/signup')) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return response
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/screeners/:path*',
    '/analysis/:path*',
    '/settings/:path*',
    '/login',
    '/signup',
  ],
}
```

#### 2.1.4 Auth Components
**File**: `frontend/src/components/auth/login-form.tsx`
```typescript
'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/ui/use-toast'
import { Icons } from '@/components/ui/icons'

export function LoginForm() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()
  const supabase = createClient()

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    })

    if (error) {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      })
    } else {
      toast({
        title: 'Check your email',
        description: 'We sent you a login link. Please check your inbox.',
      })
    }

    setLoading(false)
  }

  const handleSocialLogin = async (provider: 'google' | 'github') => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })

    if (error) {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      })
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleEmailLogin} className="space-y-4">
        <div>
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? 'Sending...' : 'Send Magic Link'}
        </Button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">
            Or continue with
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Button
          variant="outline"
          onClick={() => handleSocialLogin('google')}
        >
          <Icons.google className="mr-2 h-4 w-4" />
          Google
        </Button>
        <Button
          variant="outline"
          onClick={() => handleSocialLogin('github')}
        >
          <Icons.github className="mr-2 h-4 w-4" />
          GitHub
        </Button>
      </div>
    </div>
  )
}
```

**File**: `frontend/src/app/(auth)/login/page.tsx`
```typescript
import { LoginForm } from '@/components/auth/login-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-[400px]">
        <CardHeader>
          <CardTitle>Welcome back</CardTitle>
          <CardDescription>
            Sign in to your account to continue
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm />
        </CardContent>
      </Card>
    </div>
  )
}
```

#### 2.1.5 Auth Callback Route
**File**: `frontend/src/app/auth/callback/route.ts`
```typescript
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')

  if (code) {
    const supabase = createClient()
    await supabase.auth.exchangeCodeForSession(code)
  }

  // URL to redirect to after sign in process completes
  return NextResponse.redirect(`${requestUrl.origin}/dashboard`)
}
```

---

### **Phase 2.2: Core Layout & Navigation (Week 2)**

#### 2.2.1 Root Layout with Providers
**File**: `frontend/src/app/layout.tsx`
```typescript
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'NSE Stock Screener',
  description: 'Advanced stock screening platform for Indian markets',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

**File**: `frontend/src/components/providers.tsx`
```typescript
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from 'next-themes'
import { Toaster } from '@/components/ui/toaster'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000, // 5 minutes (EOD data caching)
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
        {children}
        <Toaster />
      </ThemeProvider>
    </QueryClientProvider>
  )
}
```

#### 2.2.2 Main App Layout (Dashboard Group)
**File**: `frontend/src/app/(dashboard)/layout.tsx`
```typescript
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  )
}
```

#### 2.2.3 Header Component
**File**: `frontend/src/components/layout/header.tsx`
```typescript
'use client'

import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/lib/hooks/use-auth'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'

export function Header() {
  const { user, signOut } = useAuth()
  const { theme, setTheme } = useTheme()

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="mr-4 flex">
          <a className="mr-6 flex items-center space-x-2" href="/dashboard">
            <span className="font-bold">NSE Screener</span>
          </a>
        </div>

        <div className="flex flex-1 items-center justify-end space-x-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          >
            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme</span>
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user?.user_metadata?.avatar_url} />
                  <AvatarFallback>{user?.email?.[0].toUpperCase()}</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>{user?.email}</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <a href="/settings">Settings</a>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={signOut}>
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
```

#### 2.2.4 Sidebar Component (Tab-Based Navigation)
**File**: `frontend/src/components/layout/sidebar.tsx`
```typescript
'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  LayoutDashboard,
  Search,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const tabs = [
  {
    name: 'Dashboard',
    icon: LayoutDashboard,
    value: 'dashboard',
    items: [
      { name: 'My Dashboard', href: '/dashboard' },
      { name: 'Create New', href: '/dashboard/new' },
    ],
  },
  {
    name: 'Screeners',
    icon: Search,
    value: 'screeners',
    items: [
      { name: 'RRG Charts', href: '/screeners/rrg-charts' },
      { name: '4% Breakouts', href: '/screeners/breakouts-4percent' },
      { name: 'Weekly Movers', href: '/screeners/weekly-movers' },
      { name: 'High Volume', href: '/screeners/high-volume' },
      { name: 'RS Leaders (97 Club)', href: '/screeners/rs-leaders' },
      { name: 'MA Stacked Breakouts', href: '/screeners/ma-breakouts' },
      { name: 'ATR Extension', href: '/screeners/atr-extension' },
      { name: 'Leading Industries', href: '/screeners/leading-industries' },
      { name: 'Stage Analysis', href: '/screeners/stage-analysis' },
      { name: 'Momentum Watchlist', href: '/screeners/momentum-watchlist' },
      { name: 'Breadth Metrics', href: '/screeners/breadth-metrics' },
    ],
  },
  {
    name: 'Analysis',
    icon: BarChart3,
    value: 'analysis',
    items: [
      { name: 'Stock Analysis', href: '/analysis/stock' },
      { name: 'Sector Analysis', href: '/analysis/sector' },
    ],
  },
  {
    name: 'Settings',
    icon: Settings,
    value: 'settings',
    items: [
      { name: 'Profile', href: '/settings/profile' },
      { name: 'Preferences', href: '/settings/preferences' },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [activeTab, setActiveTab] = useState('screeners')

  const currentTab = tabs.find((tab) =>
    pathname.startsWith(`/${tab.value}`)
  )

  return (
    <div
      className={cn(
        'relative border-r bg-background transition-all duration-300',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-4 top-6 z-10 rounded-full border bg-background"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        {isCollapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronLeft className="h-4 w-4" />
        )}
      </Button>

      {!isCollapsed && (
        <ScrollArea className="h-[calc(100vh-3.5rem)]">
          <div className="p-4">
            <Tabs value={currentTab?.value || activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-2 mb-4">
                {tabs.slice(0, 2).map((tab) => (
                  <TabsTrigger key={tab.value} value={tab.value}>
                    <tab.icon className="h-4 w-4" />
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>

            <nav className="space-y-1">
              {tabs
                .find((t) => t.value === (currentTab?.value || activeTab))
                ?.items.map((item) => (
                  <Link key={item.href} href={item.href}>
                    <Button
                      variant={pathname === item.href ? 'secondary' : 'ghost'}
                      className="w-full justify-start"
                    >
                      {item.name}
                    </Button>
                  </Link>
                ))}
            </nav>
          </div>
        </ScrollArea>
      )}

      {isCollapsed && (
        <div className="flex flex-col items-center space-y-4 p-2 pt-4">
          {tabs.map((tab) => (
            <Button
              key={tab.value}
              variant="ghost"
              size="icon"
              onClick={() => {
                setActiveTab(tab.value)
                setIsCollapsed(false)
              }}
            >
              <tab.icon className="h-5 w-5" />
            </Button>
          ))}
        </div>
      )}
    </div>
  )
}
```

---

### **Phase 2.3: API Integration Layer (Week 2-3)**

#### 2.3.1 API Client Configuration
**File**: `frontend/src/lib/api/client.ts`
```typescript
import { QueryClient } from '@tanstack/react-query'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `API Error: ${response.status}`)
  }

  return response.json()
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes (EOD data caching)
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})
```

#### 2.3.2 Status API Client
**File**: `frontend/src/lib/api/status.ts`
```typescript
import { apiRequest } from './client'
import { useQuery } from '@tanstack/react-query'

export interface DataQualityResponse {
  ohlcv_coverage: {
    last_date: string
    coverage_percentage: number
    securities_with_data: number
    total_active_securities: number
    missing_symbols: string[]
  }
  market_cap_coverage: {
    last_date: string
    coverage_percentage: number
  }
  industry_coverage: {
    coverage_percentage: number
    securities_with_industry: number
  }
  data_quality_issues: {
    invalid_ohlcv_records: number
    negative_price_records: number
  }
  recommendations: string[]
}

export interface IngestionStatusResponse {
  recent_logs: Array<{
    source: string
    status: string
    records_inserted: number
    timestamp: string
  }>
  latest_by_source: Record<string, {
    status: string
    timestamp: string
    records_inserted: number
  }>
  summary: {
    total_runs: number
    successful: number
    failed: number
  }
}

export interface TradingDayResponse {
  date: string
  is_trading_day: boolean
  reason?: string
}

export function useDataQuality() {
  return useQuery({
    queryKey: ['dataQuality'],
    queryFn: () => apiRequest<DataQualityResponse>('/status/data-quality'),
  })
}

export function useIngestionStatus(hours: number = 24) {
  return useQuery({
    queryKey: ['ingestionStatus', hours],
    queryFn: () => apiRequest<IngestionStatusResponse>(`/status/ingestion?hours=${hours}`),
  })
}

export function useTradingDay(date?: string) {
  return useQuery({
    queryKey: ['tradingDay', date],
    queryFn: () => {
      const endpoint = date ? `/status/is-trading-day?date=${date}` : '/status/is-trading-day'
      return apiRequest<TradingDayResponse>(endpoint)
    },
  })
}
```

#### 2.3.3 Screener API Client (Placeholder for Phase 2 Backend)
**File**: `frontend/src/lib/api/screeners.ts`
```typescript
import { apiRequest } from './client'
import { useQuery } from '@tanstack/react-query'

export interface ScreenerFilters {
  min_price?: number
  max_price?: number
  min_volume?: number
  min_market_cap?: number
  sectors?: string[]
  // Add more filters as needed
}

export interface ScreenerResult {
  symbol: string
  name: string
  price: number
  change_percent: number
  volume: number
  market_cap: number
  sector: string
  industry: string
  // Screener-specific fields
  [key: string]: any
}

export interface ScreenerResponse {
  data: ScreenerResult[]
  total: number
  page: number
  page_size: number
  filters_applied: ScreenerFilters
}

// Example: RRG Screener (backend endpoint to be implemented in Phase 2)
export function useRRGScreener(filters?: ScreenerFilters) {
  return useQuery({
    queryKey: ['screener', 'rrg', filters],
    queryFn: () =>
      apiRequest<ScreenerResponse>('/screeners/rrg', {
        method: 'POST',
        body: JSON.stringify(filters || {}),
      }),
    enabled: false, // Disable until backend endpoint exists
  })
}

// Placeholder for other screeners
export function useBreakoutScreener(filters?: ScreenerFilters) {
  return useQuery({
    queryKey: ['screener', 'breakouts', filters],
    queryFn: () =>
      apiRequest<ScreenerResponse>('/screeners/breakouts-4percent', {
        method: 'POST',
        body: JSON.stringify(filters || {}),
      }),
    enabled: false,
  })
}

// TODO: Add 9 more screener hooks
```

#### 2.3.4 Dashboard API Client
**File**: `frontend/src/lib/api/dashboard.ts`
```typescript
import { createClient } from '@/lib/supabase/client'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export interface Widget {
  id: string
  type: 'chart' | 'table' | 'metric' | 'heatmap'
  title: string
  config: Record<string, any>
  position: {
    x: number
    y: number
    w: number
    h: number
  }
}

export interface DashboardLayout {
  id: string
  user_id: string
  name: string
  widgets: Widget[]
  is_default: boolean
  created_at: string
  updated_at: string
}

export function useDashboardLayouts() {
  const supabase = createClient()

  return useQuery({
    queryKey: ['dashboardLayouts'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('dashboard_layouts')
        .select('*')
        .order('updated_at', { ascending: false })

      if (error) throw error
      return data as DashboardLayout[]
    },
  })
}

export function useSaveDashboard() {
  const supabase = createClient()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (layout: Omit<DashboardLayout, 'id' | 'user_id' | 'created_at' | 'updated_at'>) => {
      const { data, error } = await supabase
        .from('dashboard_layouts')
        .insert(layout)
        .select()
        .single()

      if (error) throw error
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboardLayouts'] })
    },
  })
}

export function useUpdateDashboard() {
  const supabase = createClient()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, ...updates }: Partial<DashboardLayout> & { id: string }) => {
      const { data, error } = await supabase
        .from('dashboard_layouts')
        .update(updates)
        .eq('id', id)
        .select()
        .single()

      if (error) throw error
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboardLayouts'] })
    },
  })
}
```

---

### **Phase 2.4: Chart Components (Week 3-4)**

#### 2.4.1 TradingView OHLCV Chart Component
**File**: `frontend/src/components/charts/ohlcv-chart.tsx`
```typescript
'use client'

import { useEffect, useRef } from 'react'
import { createChart, ColorType, IChartApi } from 'lightweight-charts'

export interface OHLCVData {
  time: string // ISO date string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface OHLCVChartProps {
  data: OHLCVData[]
  symbol: string
  height?: number
}

export function OHLCVChart({ data, symbol, height = 400 }: OHLCVChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)

  useEffect(() => {
    if (!chartContainerRef.current || !data.length) return

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#d1d4dc',
      },
      width: chartContainerRef.current.clientWidth,
      height,
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#363C4E' },
      },
    })

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })

    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    })

    // Transform data
    const candleData = data.map((d) => ({
      time: d.time.split('T')[0], // Convert to YYYY-MM-DD
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }))

    const volumeData = data.map((d) => ({
      time: d.time.split('T')[0],
      value: d.volume,
      color: d.close >= d.open ? '#22c55e' : '#ef4444',
    }))

    candlestickSeries.setData(candleData)
    volumeSeries.setData(volumeData)

    chart.timeScale().fitContent()

    chartRef.current = chart

    // Responsive resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [data, height])

  return (
    <div className="w-full">
      <h3 className="mb-2 text-lg font-semibold">{symbol}</h3>
      <div ref={chartContainerRef} />
    </div>
  )
}
```

#### 2.4.2 Plotly RRG Chart Component
**File**: `frontend/src/components/charts/rrg-chart.tsx`
```typescript
'use client'

import dynamic from 'next/dynamic'
import { useMemo } from 'react'

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })

export interface RRGDataPoint {
  name: string // Sector/stock name
  rs_ratio: number // X-axis (Relative Strength Ratio)
  rs_momentum: number // Y-axis (Relative Strength Momentum)
  tail: Array<{ rs_ratio: number; rs_momentum: number }> // Historical trail
  adr_percent: number // For color coding
}

interface RRGChartProps {
  data: RRGDataPoint[]
  height?: number
}

export function RRGChart({ data, height = 600 }: RRGChartProps) {
  const plotData = useMemo(() => {
    return data.map((point) => ({
      x: [point.rs_ratio],
      y: [point.rs_momentum],
      mode: 'markers+text',
      type: 'scatter',
      name: point.name,
      text: [point.name],
      textposition: 'top center',
      marker: {
        size: 12,
        color: point.adr_percent,
        colorscale: 'RdYlGn',
        showscale: true,
        colorbar: {
          title: 'ADR %',
        },
      },
      hovertemplate:
        `<b>${point.name}</b><br>` +
        `RS-Ratio: %{x:.2f}<br>` +
        `RS-Momentum: %{y:.2f}<br>` +
        `ADR: ${point.adr_percent.toFixed(2)}%<extra></extra>`,
    }))
  }, [data])

  const tailTraces = useMemo(() => {
    return data.map((point) => ({
      x: point.tail.map((t) => t.rs_ratio),
      y: point.tail.map((t) => t.rs_momentum),
      mode: 'lines',
      type: 'scatter',
      showlegend: false,
      line: {
        color: 'rgba(128, 128, 128, 0.3)',
        width: 1,
      },
      hoverinfo: 'skip',
    }))
  }, [data])

  const layout = {
    title: 'Relative Rotation Graph (RRG)',
    xaxis: {
      title: 'RS-Ratio (Relative Strength)',
      zeroline: true,
      showgrid: true,
    },
    yaxis: {
      title: 'RS-Momentum',
      zeroline: true,
      showgrid: true,
    },
    height,
    hovermode: 'closest',
    shapes: [
      // Quadrant dividers
      {
        type: 'line',
        x0: 100,
        y0: -100,
        x1: 100,
        y1: 100,
        line: { color: 'gray', width: 1, dash: 'dash' },
      },
      {
        type: 'line',
        x0: 90,
        y0: 100,
        x1: 110,
        y1: 100,
        line: { color: 'gray', width: 1, dash: 'dash' },
      },
    ],
    annotations: [
      { x: 105, y: 105, text: 'Leading', showarrow: false, font: { size: 14, color: 'green' } },
      { x: 95, y: 105, text: 'Improving', showarrow: false, font: { size: 14, color: 'blue' } },
      { x: 95, y: 95, text: 'Lagging', showarrow: false, font: { size: 14, color: 'red' } },
      { x: 105, y: 95, text: 'Weakening', showarrow: false, font: { size: 14, color: 'orange' } },
    ],
  }

  return (
    <div className="w-full">
      <Plot
        data={[...tailTraces, ...plotData] as any}
        layout={layout as any}
        config={{ responsive: true }}
        className="w-full"
      />
    </div>
  )
}
```

#### 2.4.3 Heatmap Chart Component
**File**: `frontend/src/components/charts/heatmap-chart.tsx`
```typescript
'use client'

import dynamic from 'next/dynamic'

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })

export interface HeatmapData {
  x: string[] // X-axis labels (e.g., dates)
  y: string[] // Y-axis labels (e.g., symbols)
  z: number[][] // 2D array of values
  text?: string[][] // Optional hover text
}

interface HeatmapChartProps {
  data: HeatmapData
  title: string
  colorscale?: string
  height?: number
}

export function HeatmapChart({
  data,
  title,
  colorscale = 'RdYlGn',
  height = 500,
}: HeatmapChartProps) {
  const plotData = [
    {
      x: data.x,
      y: data.y,
      z: data.z,
      text: data.text,
      type: 'heatmap',
      colorscale,
      hovertemplate: '%{y}<br>%{x}<br>Value: %{z:.2f}<extra></extra>',
    },
  ]

  const layout = {
    title,
    xaxis: { title: '', side: 'bottom' },
    yaxis: { title: '', autorange: 'reversed' },
    height,
  }

  return (
    <Plot
      data={plotData as any}
      layout={layout as any}
      config={{ responsive: true }}
      className="w-full"
    />
  )
}
```

---

### **Phase 2.5: Data Table Component (Week 4)**

#### 2.5.1 Reusable DataTable with TanStack Table
**File**: `frontend/src/components/ui/data-table.tsx`
```typescript
'use client'

import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
  ColumnFiltersState,
  getFilteredRowModel,
  getPaginationRowModel,
} from '@tanstack/react-table'
import { useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  searchKey?: string
  pageSize?: number
}

export function DataTable<TData, TValue>({
  columns,
  data,
  searchKey,
  pageSize = 50,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    state: {
      sorting,
      columnFilters,
    },
    initialState: {
      pagination: {
        pageSize,
      },
    },
  })

  return (
    <div className="space-y-4">
      {searchKey && (
        <Input
          placeholder={`Search ${searchKey}...`}
          value={(table.getColumn(searchKey)?.getFilterValue() as string) ?? ''}
          onChange={(event) =>
            table.getColumn(searchKey)?.setFilterValue(event.target.value)
          }
          className="max-w-sm"
        />
      )}

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && 'selected'}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-end space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          Next
        </Button>
      </div>
    </div>
  )
}
```

#### 2.5.2 Example: 4% Breakouts Screener Table
**File**: `frontend/src/components/screeners/breakout-screener.tsx`
```typescript
'use client'

import { ColumnDef } from '@tanstack/react-table'
import { DataTable } from '@/components/ui/data-table'
import { Badge } from '@/components/ui/badge'
import { useBreakoutScreener } from '@/lib/api/screeners'

interface BreakoutStock {
  symbol: string
  name: string
  price: number
  change_percent: number
  volume: number
  rvol: number
  market_cap: number
}

const columns: ColumnDef<BreakoutStock>[] = [
  {
    accessorKey: 'symbol',
    header: 'Symbol',
    cell: ({ row }) => (
      <a href={`/analysis/stock/${row.original.symbol}`} className="font-medium hover:underline">
        {row.original.symbol}
      </a>
    ),
  },
  {
    accessorKey: 'name',
    header: 'Name',
  },
  {
    accessorKey: 'price',
    header: 'Price',
    cell: ({ row }) => `₹${row.original.price.toFixed(2)}`,
  },
  {
    accessorKey: 'change_percent',
    header: '% Change',
    cell: ({ row }) => {
      const value = row.original.change_percent
      return (
        <Badge variant={value >= 0 ? 'default' : 'destructive'}>
          {value >= 0 ? '+' : ''}{value.toFixed(2)}%
        </Badge>
      )
    },
  },
  {
    accessorKey: 'rvol',
    header: 'RVOL',
    cell: ({ row }) => `${row.original.rvol.toFixed(2)}x`,
  },
  {
    accessorKey: 'market_cap',
    header: 'Market Cap (Cr)',
    cell: ({ row }) => `₹${(row.original.market_cap / 10000000).toFixed(2)}`,
  },
]

export function BreakoutScreener() {
  const { data, isLoading, error } = useBreakoutScreener()

  if (isLoading) return <div>Loading screener...</div>
  if (error) return <div>Error loading data: {error.message}</div>

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-3xl font-bold">4% Breakouts</h1>
        <p className="text-muted-foreground">
          Stocks with ≥4% daily gain and volume surge
        </p>
      </div>

      <DataTable
        columns={columns}
        data={data?.data || []}
        searchKey="symbol"
        pageSize={50}
      />
    </div>
  )
}
```

---

### **Phase 2.6: Dashboard System (Week 5)**

#### 2.6.1 React Grid Layout Integration
```bash
npm install react-grid-layout
npm install --save-dev @types/react-grid-layout
```

**File**: `frontend/src/components/dashboard/dashboard-editor.tsx`
```typescript
'use client'

import { useState } from 'react'
import GridLayout, { Layout } from 'react-grid-layout'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { useDashboardLayouts, useSaveDashboard, useUpdateDashboard } from '@/lib/api/dashboard'
import { Widget } from '@/lib/api/dashboard'
import { WidgetRRG } from './widget-rrg'
import { WidgetTable } from './widget-table'
import { WidgetMetric } from './widget-metric'

export function DashboardEditor() {
  const { data: layouts } = useDashboardLayouts()
  const { mutate: saveDashboard } = useSaveDashboard()
  const { mutate: updateDashboard } = useUpdateDashboard()

  const [currentLayout, setCurrentLayout] = useState<Widget[]>([
    {
      id: '1',
      type: 'metric',
      title: 'Market Status',
      config: {},
      position: { x: 0, y: 0, w: 3, h: 2 },
    },
  ])

  const handleLayoutChange = (layout: Layout[]) => {
    const updatedWidgets = currentLayout.map((widget) => {
      const layoutItem = layout.find((l) => l.i === widget.id)
      if (layoutItem) {
        return {
          ...widget,
          position: {
            x: layoutItem.x,
            y: layoutItem.y,
            w: layoutItem.w,
            h: layoutItem.h,
          },
        }
      }
      return widget
    })
    setCurrentLayout(updatedWidgets)
  }

  const handleSave = () => {
    saveDashboard({
      name: 'My Dashboard',
      widgets: currentLayout,
      is_default: true,
    })
  }

  const renderWidget = (widget: Widget) => {
    switch (widget.type) {
      case 'chart':
        return <WidgetRRG config={widget.config} />
      case 'table':
        return <WidgetTable config={widget.config} />
      case 'metric':
        return <WidgetMetric config={widget.config} />
      default:
        return <div>Unknown widget type</div>
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Button onClick={handleSave}>Save Layout</Button>
      </div>

      <GridLayout
        className="layout"
        layout={currentLayout.map((w) => ({
          i: w.id,
          x: w.position.x,
          y: w.position.y,
          w: w.position.w,
          h: w.position.h,
        }))}
        cols={12}
        rowHeight={100}
        width={1200}
        onLayoutChange={handleLayoutChange}
        draggableHandle=".drag-handle"
      >
        {currentLayout.map((widget) => (
          <div key={widget.id}>
            <Card className="h-full">
              <CardHeader className="drag-handle cursor-move">
                <CardTitle>{widget.title}</CardTitle>
              </CardHeader>
              <CardContent>{renderWidget(widget)}</CardContent>
            </Card>
          </div>
        ))}
      </GridLayout>
    </div>
  )
}
```

#### 2.6.2 Dashboard Widget Components
**File**: `frontend/src/components/dashboard/widget-metric.tsx`
```typescript
'use client'

import { useDataQuality } from '@/lib/api/status'
import { Skeleton } from '@/components/ui/skeleton'

interface WidgetMetricProps {
  config: Record<string, any>
}

export function WidgetMetric({ config }: WidgetMetricProps) {
  const { data, isLoading } = useDataQuality()

  if (isLoading) return <Skeleton className="h-20 w-full" />

  return (
    <div className="space-y-2">
      <div className="text-2xl font-bold">
        {data?.ohlcv_coverage.coverage_percentage.toFixed(1)}%
      </div>
      <div className="text-sm text-muted-foreground">
        OHLCV Coverage
      </div>
      <div className="text-xs text-muted-foreground">
        Last updated: {data?.ohlcv_coverage.last_date}
      </div>
    </div>
  )
}
```

---

### **Phase 2.7: Screener Pages (Week 5-6)**

#### 2.7.1 RRG Screener Page
**File**: `frontend/src/app/(dashboard)/screeners/rrg-charts/page.tsx`
```typescript
import { RRGChart } from '@/components/charts/rrg-chart'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

// Placeholder: Replace with API call in Phase 2 backend
const mockRRGData = [
  { name: 'Nifty IT', rs_ratio: 105, rs_momentum: 102, tail: [], adr_percent: 2.5 },
  { name: 'Nifty Bank', rs_ratio: 98, rs_momentum: 101, tail: [], adr_percent: 1.8 },
  { name: 'Nifty Pharma', rs_ratio: 102, rs_momentum: 98, tail: [], adr_percent: 2.1 },
  { name: 'Nifty Auto', rs_ratio: 97, rs_momentum: 97, tail: [], adr_percent: 1.5 },
]

export default function RRGChartsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Relative Rotation Graph (RRG)</h1>
        <p className="text-muted-foreground">
          Sector rotation analysis with RS-Ratio and RS-Momentum
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sector Rotation</CardTitle>
          <CardDescription>
            Leading quadrant = outperformers, Lagging = underperformers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RRGChart data={mockRRGData} />
        </CardContent>
      </Card>
    </div>
  )
}
```

#### 2.7.2 Screener Index Page (Hub)
**File**: `frontend/src/app/(dashboard)/screeners/page.tsx`
```typescript
import Link from 'next/link'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Search, TrendingUp, Activity } from 'lucide-react'

const screeners = [
  {
    name: 'RRG Charts',
    description: 'Sector rotation with RS-Ratio and RS-Momentum',
    href: '/screeners/rrg-charts',
    icon: Activity,
  },
  {
    name: '4% Breakouts',
    description: 'Stocks with ≥4% daily gain and volume surge',
    href: '/screeners/breakouts-4percent',
    icon: TrendingUp,
  },
  // Add remaining 9 screeners
]

export default function ScreenersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Stock Screeners</h1>
        <p className="text-muted-foreground">
          Advanced screening tools for Indian stock markets
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {screeners.map((screener) => (
          <Link key={screener.href} href={screener.href}>
            <Card className="hover:bg-accent transition-colors cursor-pointer">
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <screener.icon className="h-5 w-5" />
                  <CardTitle>{screener.name}</CardTitle>
                </div>
                <CardDescription>{screener.description}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
```

---

### **Phase 2.8: Deployment Configuration (Week 6)**

#### 2.8.1 Vercel Configuration
**File**: `frontend/vercel.json`
```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "outputDirectory": ".next",
  "regions": ["sin1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "@api-url",
    "NEXT_PUBLIC_SUPABASE_URL": "@supabase-url",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "@supabase-anon-key"
  }
}
```

#### 2.8.2 GitHub Actions Deployment (Optional)
**File**: `frontend/.github/workflows/deploy.yml`
```yaml
name: Deploy to Vercel

on:
  push:
    branches:
      - main
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          working-directory: ./frontend
```

#### 2.8.3 Docker Compose Production
**Update**: `/Users/mayanklavania/projects/screener/docker-compose.yml`
Add production frontend service:
```yaml
services:
  # ... existing services

  frontend-prod:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: screener_frontend_prod
    ports:
      - "3001:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
      - NEXT_PUBLIC_SUPABASE_URL=${SUPABASE_URL}
      - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    networks:
      - screener_network
    depends_on:
      - backend
    restart: unless-stopped
    profiles:
      - production
```

---

## 4. Data Flow Architecture

### Frontend → Backend Communication
```
User Interaction (UI)
  ↓
React Component
  ↓
React Query Hook (useScreener, useDataQuality)
  ↓
API Client (apiRequest function)
  ↓
FastAPI Backend (/api/v1/*)
  ↓
PostgreSQL Database
  ↓
Response back to UI
```

### Authentication Flow
```
User clicks "Login with Google"
  ↓
Supabase Auth (OAuth redirect)
  ↓
User authenticates with Google
  ↓
Redirect to /auth/callback
  ↓
Exchange code for session
  ↓
Store session in cookies
  ↓
Middleware checks auth on protected routes
  ↓
Redirect to /dashboard
```

### Dashboard State Management
```
User data (layouts, preferences):
  Supabase PostgreSQL (via Supabase Client SDK)

Screener data (securities, OHLCV):
  Backend PostgreSQL (via FastAPI REST API)

UI state (filters, theme):
  Zustand store (client-side only)

Server cache (API responses):
  React Query (5-minute stale time)
```

---

## 5. Caching Strategy

### Backend Caching Recommendation
**Backend should handle:**
- Database query results (Redis/in-memory for frequently accessed screeners)
- EOD data (cache until next market close)
- Calculated metrics (cache daily after calculation)

**Why backend caching is better:**
- Consistent across all clients
- Reduces database load
- Easier to invalidate (single source of truth)
- Can implement time-based expiry (cache until 3:30 PM IST)

### Frontend Caching (React Query)
```typescript
// frontend/src/lib/api/client.ts
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes in memory
      refetchOnWindowFocus: false, // Don't refetch on tab switch
      retry: 1,
    },
  },
})
```

**Frontend caching approach:**
- React Query handles in-memory caching automatically
- 5-minute stale time (reasonable for EOD data)
- Manual refetch available via refresh button
- No service worker/PWA caching in Phase 2 (add later if needed)

**For premium features (future):**
- Backend can return `Cache-Control` headers with shorter TTL for premium users
- Frontend respects backend caching headers via React Query

---

## 6. Type Safety & Validation

### Shared Types Between Frontend/Backend
**File**: `frontend/src/types/screener.ts`
```typescript
// Mirror backend Pydantic models

export interface Security {
  id: string
  symbol: string
  name: string
  isin: string
  series: string
  is_active: boolean
  listing_date: string
  face_value: number
}

export interface OHLCVDaily {
  id: string
  symbol: string
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  prev_close: number
  value: number
  trades: number
}

// Add 12 more model types matching backend
```

### Zod Validation Schemas
**File**: `frontend/src/lib/utils/validators.ts`
```typescript
import { z } from 'zod'

export const screenerFiltersSchema = z.object({
  min_price: z.number().positive().optional(),
  max_price: z.number().positive().optional(),
  min_volume: z.number().nonnegative().optional(),
  min_market_cap: z.number().nonnegative().optional(),
  sectors: z.array(z.string()).optional(),
})

export type ScreenerFilters = z.infer<typeof screenerFiltersSchema>
```

---

## 7. Testing Strategy

### Unit Tests (Vitest)
```bash
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom
```

**File**: `frontend/vitest.config.ts`
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

**Example Test**: `frontend/src/components/charts/__tests__/ohlcv-chart.test.tsx`
```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OHLCVChart } from '../ohlcv-chart'

describe('OHLCVChart', () => {
  it('renders chart with symbol', () => {
    const mockData = [
      { time: '2024-01-01', open: 100, high: 110, low: 95, close: 105, volume: 1000000 },
    ]
    render(<OHLCVChart data={mockData} symbol="RELIANCE" />)
    expect(screen.getByText('RELIANCE')).toBeInTheDocument()
  })
})
```

### Integration Tests
- Test API client functions with mock responses
- Test authentication flow with Supabase mocks
- Test data table sorting/filtering

### E2E Tests (Optional - Phase 3)
- Playwright for full user flows
- Test login → dashboard → screener navigation

---

## 8. Performance Optimization Checklist

### Bundle Size
- ✅ Use dynamic imports for chart libraries: `next/dynamic`
- ✅ Tree-shake Shadcn components (only import what you use)
- ✅ Lazy load screener pages (automatic with Next.js App Router)
- ✅ Optimize images with Next.js Image component

### Runtime Performance
- ✅ Virtualize tables >50 rows (already using TanStack Table)
- ✅ Memoize expensive chart computations (useMemo)
- ✅ Debounce search inputs (300ms)
- ✅ Paginate screener results (50 rows per page)

### Network Performance
- ✅ React Query caching (5-minute stale time)
- ✅ Backend API response compression (gzip)
- ✅ Incremental Static Regeneration (ISR) for landing page

### Monitoring
- Add Vercel Analytics (free tier)
- Add Sentry for error tracking (optional)
- Monitor Core Web Vitals (LCP, FID, CLS)

---

## 9. Security Considerations

### Authentication
- ✅ Supabase handles OAuth securely
- ✅ Session stored in httpOnly cookies (via middleware)
- ✅ Row Level Security (RLS) on Supabase tables

### API Security
- ✅ No API keys exposed to frontend (Supabase anon key is safe)
- ✅ Backend API uses CORS whitelist for production
- ✅ Input validation with Zod schemas

### Data Privacy
- User dashboard layouts stored in Supabase (private per user)
- No PII stored in frontend localStorage
- GDPR compliance: Users can delete account (triggers CASCADE delete)

---

## 10. Development Workflow

### Local Development Setup
```bash
# 1. Clone repo
git clone https://github.com/yourusername/screener.git
cd screener

# 2. Setup backend (if not already done)
docker-compose up -d postgres backend n8n

# 3. Setup frontend
cd frontend
npm install

# 4. Configure environment
cp .env.example .env.local
# Edit .env.local with Supabase credentials

# 5. Run frontend dev server
npm run dev

# Access:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Backend API docs: http://localhost:8000/docs
```

### Git Branch Strategy
```
main
  ├── feature/frontend-setup
  ├── feature/auth-implementation
  ├── feature/screener-rrg
  └── feature/dashboard-widgets
```

### Code Quality
```bash
# Linting
npm run lint

# Type checking
npm run type-check

# Tests
npm run test
npm run test:coverage

# Build (production)
npm run build
```

---

## 11. Phase 2 Backend Endpoints (TO BE IMPLEMENTED)

The frontend is designed to consume these endpoints. Backend team needs to implement:

### Screener Endpoints
```
POST /api/v1/screeners/rrg
POST /api/v1/screeners/breakouts-4percent
POST /api/v1/screeners/weekly-movers
POST /api/v1/screeners/high-volume
POST /api/v1/screeners/rs-leaders
POST /api/v1/screeners/ma-breakouts
POST /api/v1/screeners/atr-extension
POST /api/v1/screeners/leading-industries
POST /api/v1/screeners/stage-analysis
POST /api/v1/screeners/momentum-watchlist
POST /api/v1/screeners/breadth-metrics

Request body:
{
  "filters": {
    "min_price": 100,
    "max_price": 10000,
    "sectors": ["IT", "Banking"]
  },
  "page": 1,
  "page_size": 50
}

Response:
{
  "data": [...],
  "total": 245,
  "page": 1,
  "page_size": 50,
  "filters_applied": {...}
}
```

### Calculated Metrics Endpoints
```
GET /api/v1/metrics/daily/{symbol}
GET /api/v1/metrics/sector-strength
GET /api/v1/metrics/rrg-data
```

---

## 12. Success Criteria

### Phase 2 Complete When:
- ✅ Authentication working (email OTP + Google/GitHub)
- ✅ Dashboard loads with customizable widgets
- ✅ All 11 screeners have dedicated pages (UI complete, data from mock/backend)
- ✅ RRG Chart renders correctly with Plotly
- ✅ OHLCV Chart renders with TradingView Lightweight Charts
- ✅ Data tables support sorting, filtering, pagination
- ✅ Dark mode working
- ✅ Deployed to Vercel (production)
- ✅ Docker container working for local dev
- ✅ Responsive design tested on mobile/tablet
- ✅ All Shadcn components installed and documented

---

## 13. Timeline Summary

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | 2.0-2.1 | Project setup, auth implementation, Docker config |
| 2 | 2.1-2.2 | Auth completion, layout/navigation, sidebar |
| 2-3 | 2.3 | API integration layer (status, screeners, dashboard) |
| 3-4 | 2.4 | Chart components (TradingView, Plotly, heatmaps) |
| 4 | 2.5 | Data table component with virtualization |
| 5 | 2.6 | Dashboard system with React Grid Layout |
| 5-6 | 2.7 | All 11 screener pages |
| 6 | 2.8 | Deployment to Vercel + production testing |

**Total: 6 weeks** (assuming 1 developer, full-time)

---

## 14. Future Enhancements (Phase 3+)

### Not in Phase 2 Scope:
- Real-time WebSocket updates (stick to polling for now)
- PWA/offline support
- Mobile app (React Native)
- Advanced dashboard templates
- Social features (share dashboards publicly)
- CSV/PDF export
- Alerting system (email/SMS notifications)
- Advanced charting (indicators overlays, drawing tools)
- Multi-language support (i18n infrastructure ready, translations Phase 3)

---

## 15. Critical Files Reference

### Existing Backend Files (DO NOT MODIFY):
- `/Users/mayanklavania/projects/screener/backend/app/api/v1/*.py` - API routes
- `/Users/mayanklavania/projects/screener/backend/app/models/*.py` - Database models
- `/Users/mayanklavania/projects/screener/docker-compose.yml` - Root orchestration

### New Frontend Files (TO BE CREATED):
- `/Users/mayanklavania/projects/screener/frontend/` - Entire frontend directory
- Key files: See Section 2 (Project Structure)

### Documentation Reference:
- `/Users/mayanklavania/projects/screener/.claude/Architecture.md` - Database schema
- `/Users/mayanklavania/projects/screener/.claude/file-formats.md` - Data formats
- `/Users/mayanklavania/projects/screener/documentation/screeners-idea.md` - Screener specs

---

## 16. Questions for User (Before Implementation)

1. **Supabase Project**: Do you have a Supabase project created? Need project URL and anon key.
2. **Domain Name**: Do you have a domain for production deployment? (e.g., screener.yourdomain.com)
3. **Google/GitHub OAuth**: Need OAuth credentials configured in Supabase dashboard.
4. **Vercel Account**: Should we deploy to your Vercel account or create new project?
5. **Backend API URL (Production)**: What will be the production backend URL? (for CORS and API client)

---

## END OF PLAN

This plan provides a complete, production-ready frontend implementation for your NSE stock screener platform. All technology choices align with your requirements:
- ✅ Shadcn/ui for beautiful, clean UI
- ✅ Supabase Auth with social login
- ✅ Vercel deployment (cloud) + Docker (local dev)
- ✅ Desktop-first responsive design
- ✅ EOD data with backend caching
- ✅ Customizable dashboards (Phase 3)
- ✅ 11 screeners with full-screen + widget modes

Ready to implement upon approval!