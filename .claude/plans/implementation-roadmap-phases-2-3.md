# Frontend Implementation Plan - Execution Roadmap

## Quick Reference

**Repository**: Monorepo at `/Users/mayanklavania/projects/screener`
**New Directory**: `frontend/` (to be created)
**Timeline**: 6 weeks (1 developer, full-time)
**Deployment**: Vercel (primary) + Docker (local dev)

**Detailed Technical Plan**: See [wise-yawning-candle.md](wise-yawning-candle.md) for complete specs.

---

## Move Plans to Project Directory

**IMPORTANT**: The frontend plans were created in `/Users/mayanklavania/.claude/plans/` but should be moved to the project's `.claude/` directory.

**Commands to run**:
```bash
cd /Users/mayanklavania/projects/screener

# Create plans directory if it doesn't exist
mkdir -p .claude/plans

# Move the plans
mv /Users/mayanklavania/.claude/plans/starry-jingling-phoenix.md .claude/plans/
mv /Users/mayanklavania/.claude/plans/wise-yawning-candle.md .claude/plans/

# Verify
ls -la .claude/plans/
```

**Expected structure**:
```
/screener/.claude/
├── plans/
│   ├── starry-jingling-phoenix.md   # Frontend execution roadmap (this file)
│   └── wise-yawning-candle.md       # Frontend technical specs
├── Architecture.md
├── Implementation-Plan.md
├── PRD.md
├── file-formats.md
└── UPDATES.md
```

---

## Update CLAUDE.md Reference

After moving plans to project directory, update `/Users/mayanklavania/projects/screener/CLAUDE.md`:

### Section: "Related Documentation"
Add new entry:
```markdown
- **[.claude/plans/starry-jingling-phoenix.md](.claude/plans/starry-jingling-phoenix.md)** - Frontend implementation roadmap (day-by-day execution plan)
- **[.claude/plans/wise-yawning-candle.md](.claude/plans/wise-yawning-candle.md)** - Frontend technical specifications (complete architecture, code examples)
```

### Section: "Current Development Status"
Update:
```markdown
**Current Phase:** Phase 2 - Frontend Development (In Progress)

**Next Steps - Phase 2:**
- ✅ Phase 1 Complete (Backend, n8n, OHLCV ingestion, monitoring)
- 🚧 Phase 2: Frontend implementation (Week 1-6)
  - Next.js + Shadcn/ui setup
  - Supabase authentication
  - 11 screener pages
  - Customizable dashboards
  - Vercel deployment
- 📋 Phase 3: Backend screener calculations (30+ metrics)
```

### Section: "Commands" - Add Frontend Commands
Add new subsection:
```markdown
### Frontend Development

**Local development:**
```bash
cd frontend
npm install
npm run dev
```

**Access points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Supabase: https://[project-id].supabase.co

**Build for production:**
```bash
npm run build
npm run start  # Production server
```

**Docker development:**
```bash
docker-compose up frontend  # Dev mode with hot reload
```
```

### Section: "Project Structure"
Update to show frontend directory:
```markdown
├── frontend/                   # Next.js + Shadcn/ui dashboard
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   ├── app/               # Next.js App Router
│   │   ├── components/        # React components
│   │   ├── lib/               # API clients, utilities
│   │   └── types/             # TypeScript definitions
│   └── public/                # Static assets
```

---

## Phase 0: Prerequisites (Before Starting)

### Setup Supabase Project
1. Create Supabase project at https://supabase.com/dashboard
2. Enable authentication providers:
   - Email (Magic Link OTP)
   - Google OAuth
   - GitHub OAuth
3. Copy credentials:
   - Project URL: `https://[project-id].supabase.co`
   - Anon Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
4. Run SQL schema (see Phase 2.1.2 in detailed plan)

### Vercel Account Setup
1. Sign up at https://vercel.com
2. Connect GitHub account
3. Ready to import `/screener` repository

---

## Week 1: Foundation & Authentication

### Day 1-2: Project Initialization

**Actions**:
```bash
cd /Users/mayanklavania/projects/screener
npx create-next-app@latest frontend --typescript --tailwind --app --use-npm

cd frontend
npx shadcn@latest init
```

**Install Dependencies**:
```bash
npm install @tanstack/react-query zustand
npm install @supabase/supabase-js @supabase/auth-helpers-nextjs
npm install lightweight-charts plotly.js react-plotly.js
npm install react-hook-form zod @hookform/resolvers
npm install date-fns clsx tailwind-merge react-grid-layout

npm install --save-dev @types/plotly.js @types/react-grid-layout
```

**Shadcn Components (Initial Set)**:
```bash
npx shadcn@latest add button input card table dropdown-menu tabs
npx shadcn@latest add dialog toast skeleton calendar popover
npx shadcn@latest add select badge avatar separator switch label form
```

**Files to Create**:
- [ ] `frontend/.env.local` (from .env.example template)
- [ ] `frontend/Dockerfile` (production build)
- [ ] `frontend/Dockerfile.dev` (development with hot reload)
- [ ] `frontend/next.config.mjs` (standalone output for Docker)
- [ ] `frontend/tailwind.config.ts` (custom colors: bull/bear)

**Files to Update**:
- [ ] Root `docker-compose.yml` (add frontend service)
- [ ] Root `.env` (add SUPABASE_URL, SUPABASE_ANON_KEY)

**Deliverable**: Frontend scaffold running at http://localhost:3000

---

### Day 3-4: Supabase Authentication

**Database Setup (Supabase SQL Editor)**:
Run the SQL schema from detailed plan (Phase 2.1.2):
- [ ] `profiles` table
- [ ] `dashboard_layouts` table
- [ ] `user_preferences` table
- [ ] `saved_filters` table
- [ ] Row Level Security (RLS) policies
- [ ] Trigger for auto-profile creation

**Files to Create**:
```
frontend/src/
├── lib/
│   ├── supabase/
│   │   ├── client.ts           # Browser client
│   │   ├── server.ts           # Server-side client
│   │   └── middleware.ts       # Auth middleware
│   └── hooks/
│       └── use-auth.ts         # useAuth hook
├── components/
│   ├── auth/
│   │   ├── login-form.tsx      # Email OTP + social login
│   │   └── protected-route.tsx
│   └── ui/
│       └── icons.tsx           # Google/GitHub icons
├── app/
│   ├── (auth)/
│   │   └── login/
│   │       └── page.tsx        # Login page
│   └── auth/
│       └── callback/
│           └── route.ts        # OAuth callback handler
└── middleware.ts               # Next.js middleware (protected routes)
```

**Testing Checklist**:
- [ ] Email magic link login works
- [ ] Google OAuth login works
- [ ] GitHub OAuth login works
- [ ] Profile auto-created in `profiles` table
- [ ] Protected routes redirect to login
- [ ] Logout clears session

**Deliverable**: Working authentication flow

---

### Day 5: Layout & Navigation

**Files to Create**:
```
frontend/src/
├── components/
│   ├── providers.tsx           # React Query + Theme providers
│   ├── layout/
│   │   ├── header.tsx          # Top nav with user menu
│   │   ├── sidebar.tsx         # Tab-based sidebar (Dashboard/Screeners)
│   │   └── footer.tsx
│   └── ui/
│       └── scroll-area.tsx     # Shadcn scroll area
└── app/
    ├── layout.tsx              # Root layout
    ├── globals.css             # Tailwind globals + custom CSS
    └── (dashboard)/
        ├── layout.tsx          # Dashboard layout (header + sidebar)
        ├── dashboard/
        │   └── page.tsx        # Dashboard home
        └── screeners/
            └── page.tsx        # Screeners index
```

**Sidebar Navigation Structure**:
```typescript
Tabs: [Dashboard, Screeners, Analysis, Settings]

When "Screeners" tab active, show:
  - RRG Charts
  - 4% Breakouts
  - Weekly Movers
  - High Volume
  - RS Leaders (97 Club)
  - MA Stacked Breakouts
  - ATR Extension Matrix
  - Leading Industries
  - Stage Analysis
  - Momentum Watchlist
  - Breadth Metrics
```

**Features**:
- [ ] Collapsible sidebar (icon-only mode)
- [ ] Dark mode toggle in header
- [ ] User avatar dropdown (profile, settings, logout)
- [ ] Active route highlighting
- [ ] Responsive (mobile drawer, desktop sidebar)

**Deliverable**: Complete app shell with navigation

---

## Week 2: API Integration & Data Layer

### Day 6-7: API Client Setup

**Files to Create**:
```
frontend/src/lib/
├── api/
│   ├── client.ts               # Base API request wrapper
│   ├── status.ts               # Status API (data quality, ingestion)
│   ├── health.ts               # Health check API
│   ├── screeners.ts            # Screener API (placeholder hooks)
│   └── dashboard.ts            # Dashboard API (Supabase)
└── constants.ts                # API base URL, constants
```

**Status API Integration (Existing Backend Endpoints)**:
Implement React Query hooks for:
- [ ] `useDataQuality()` → `GET /api/v1/status/data-quality`
- [ ] `useIngestionStatus(hours)` → `GET /api/v1/status/ingestion?hours=24`
- [ ] `useTradingDay(date)` → `GET /api/v1/status/is-trading-day`
- [ ] `useMarketStatus()` → `GET /api/v1/health/market-status`

**Dashboard API (Supabase)**:
- [ ] `useDashboardLayouts()` → Fetch user's dashboard layouts
- [ ] `useSaveDashboard()` → Save new layout
- [ ] `useUpdateDashboard()` → Update existing layout
- [ ] `useDeleteDashboard()` → Delete layout

**Testing**:
- [ ] Test with existing backend at http://localhost:8000
- [ ] Verify React Query caching (5-minute stale time)
- [ ] Test error handling (backend offline scenario)

**Deliverable**: Full API layer ready for UI consumption

---

### Day 8-9: Type Definitions

**Files to Create**:
```
frontend/src/types/
├── security.ts                 # Mirror backend Security model
├── screener.ts                 # Screener filter/result types
├── ohlcv.ts                    # OHLCV data types
├── dashboard.ts                # Dashboard layout/widget types
└── api-responses.ts            # API response envelopes
```

**Key Types to Define** (matching backend Pydantic models):
```typescript
// security.ts
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

// ohlcv.ts
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
}

// screener.ts
export interface ScreenerFilters {
  min_price?: number
  max_price?: number
  min_volume?: number
  sectors?: string[]
}

export interface ScreenerResult {
  symbol: string
  name: string
  price: number
  change_percent: number
  volume: number
  market_cap: number
  // Screener-specific fields added dynamically
  [key: string]: any
}
```

**Zod Validation Schemas**:
```
frontend/src/lib/utils/
└── validators.ts               # Zod schemas for forms
```

**Deliverable**: Complete type safety across frontend

---

### Day 10: State Management

**Zustand Stores (Client State)**:
```
frontend/src/lib/stores/
├── filter-store.ts             # Screener filter state
├── ui-store.ts                 # Sidebar collapsed, theme, etc.
└── dashboard-store.ts          # Current dashboard layout (temp state)
```

**Example: Filter Store**:
```typescript
interface FilterState {
  filters: ScreenerFilters
  setFilters: (filters: ScreenerFilters) => void
  resetFilters: () => void
}

export const useFilterStore = create<FilterState>((set) => ({
  filters: {},
  setFilters: (filters) => set({ filters }),
  resetFilters: () => set({ filters: {} }),
}))
```

**Deliverable**: Clean state management pattern

---

## Week 3: Chart Components

### Day 11-12: TradingView Lightweight Charts

**File**: `frontend/src/components/charts/ohlcv-chart.tsx`

**Features**:
- [ ] Candlestick series (green/red)
- [ ] Volume histogram (separate pane)
- [ ] Responsive resizing
- [ ] Dark mode support
- [ ] Tooltips on hover
- [ ] Time scale with date formatting

**Props Interface**:
```typescript
interface OHLCVChartProps {
  data: OHLCVData[]
  symbol: string
  height?: number
}
```

**Testing**:
- [ ] Test with mock OHLCV data
- [ ] Test with real data from `GET /api/v1/ingest/historical-ohlcv/{symbol}`

**Deliverable**: Reusable OHLCV chart component

---

### Day 13-14: Plotly Charts

**Files**:
```
frontend/src/components/charts/
├── rrg-chart.tsx               # RRG quadrant chart
├── heatmap-chart.tsx           # Sector heatmap
└── breadth-chart.tsx           # Market breadth bars
```

**RRG Chart Features**:
- [ ] Scatter plot with 4 quadrants
- [ ] Color-coded by ADR% (volatility)
- [ ] Historical tails (line traces)
- [ ] Quadrant labels (Leading, Improving, Lagging, Weakening)
- [ ] Interactive hover (symbol, RS-Ratio, RS-Momentum)

**Heatmap Features**:
- [ ] 2D grid (X=dates, Y=symbols)
- [ ] Color scale (RdYlGn for performance)
- [ ] Hover text with values

**Deliverable**: Production-ready chart library

---

## Week 4: Data Tables & Screener UI

### Day 15-16: DataTable Component

**File**: `frontend/src/components/ui/data-table.tsx`

**Features** (TanStack Table):
- [ ] Column sorting (click header to sort)
- [ ] Global search filter
- [ ] Column-specific filters
- [ ] Pagination (50 rows per page)
- [ ] Row selection (optional)
- [ ] Sticky header
- [ ] Loading skeleton
- [ ] Empty state

**Virtualization** (if needed for 2000+ rows):
- Add `react-window` for virtual scrolling
- Only render visible rows + buffer

**Deliverable**: Reusable, performant data table

---

### Day 17-18: First Screener (RRG Charts)

**Files**:
```
frontend/src/app/(dashboard)/screeners/rrg-charts/
├── page.tsx                    # Main RRG screener page
└── components/
    ├── rrg-filters.tsx         # Filter sidebar
    └── sector-table.tsx        # Sector details table
```

**Page Structure**:
```
┌─────────────────────────────────────────┐
│  RRG Charts - Sector Rotation Analysis  │
├─────────────────────────────────────────┤
│  [Filters: Benchmark, Time Period]      │
├─────────────────────────────────────────┤
│                                         │
│        RRG Quadrant Chart               │
│        (Plotly Scatter Plot)            │
│                                         │
├─────────────────────────────────────────┤
│  Sector Details Table                   │
│  (DataTable with RS-Ratio, Momentum)    │
└─────────────────────────────────────────┘
```

**Data Source** (Phase 2 - placeholder for now):
- Mock RRG data (hardcoded sample)
- Backend endpoint to be implemented: `POST /api/v1/screeners/rrg`

**Deliverable**: First complete screener page

---

### Day 19-20: Second Screener (4% Breakouts)

**File**: `frontend/src/app/(dashboard)/screeners/breakouts-4percent/page.tsx`

**Features**:
- [ ] DataTable with columns: Symbol, Name, Price, % Change, RVOL, Market Cap
- [ ] Color-coded badges (green for +4%, red for -4%)
- [ ] Search by symbol
- [ ] Sort by % change (default)
- [ ] Click row → Navigate to stock analysis page

**Column Definitions**:
```typescript
const columns: ColumnDef<BreakoutStock>[] = [
  { accessorKey: 'symbol', header: 'Symbol' },
  { accessorKey: 'name', header: 'Name' },
  {
    accessorKey: 'change_percent',
    header: '% Change',
    cell: ({ row }) => <Badge variant={row.original.change_percent >= 0 ? 'default' : 'destructive'}>
      {row.original.change_percent.toFixed(2)}%
    </Badge>
  },
  // ... more columns
]
```

**Deliverable**: Second screener complete

---

## Week 5: Dashboard System & Remaining Screeners

### Day 21-22: Dashboard Grid Layout

**Install**:
```bash
npm install react-grid-layout
npm install --save-dev @types/react-grid-layout
```

**Files**:
```
frontend/src/components/dashboard/
├── dashboard-editor.tsx        # Main dashboard with React Grid Layout
├── widget-container.tsx        # Wrapper for all widgets
├── widget-rrg.tsx              # RRG widget (mini version)
├── widget-table.tsx            # Table widget (top movers, etc.)
├── widget-metric.tsx           # Single metric (coverage %, market status)
└── widget-selector.tsx         # Add widget dialog
```

**Dashboard Features**:
- [ ] Drag-and-drop widgets
- [ ] Resize widgets
- [ ] Add/remove widgets
- [ ] Save layout to Supabase (`dashboard_layouts` table)
- [ ] Load saved layouts
- [ ] Default layout for new users
- [ ] Responsive grid (12 cols desktop, 4 cols mobile)

**Widget Types**:
1. **Metric Widget**: Single number (e.g., "OHLCV Coverage: 98.5%")
2. **Table Widget**: Mini table (e.g., "Top 10 Gainers Today")
3. **Chart Widget**: Mini RRG chart or heatmap
4. **Status Widget**: Ingestion logs, market status

**Deliverable**: Fully functional customizable dashboard

---

### Day 23-25: Remaining 9 Screeners

Implement pages for:
- [ ] `/screeners/weekly-movers` (20% weekly change table)
- [ ] `/screeners/high-volume` (High RVOL table)
- [ ] `/screeners/rs-leaders` (97 Club table)
- [ ] `/screeners/ma-breakouts` (MA stacked table)
- [ ] `/screeners/atr-extension` (ATR extension matrix/heatmap)
- [ ] `/screeners/leading-industries` (Top 20% industries table)
- [ ] `/screeners/stage-analysis` (Stage distribution bar chart + table)
- [ ] `/screeners/momentum-watchlist` (RS + MA holds table)
- [ ] `/screeners/breadth-metrics` (Breadth dashboard with charts)

**Approach** (copy pattern from RRG/Breakouts):
1. Create `page.tsx` in screener directory
2. Add filters component (if needed)
3. Use DataTable or Chart component
4. Mock data for now (backend endpoints Phase 2)

**Deliverable**: All 11 screeners with UI complete

---

## Week 6: Polish, Testing & Deployment

### Day 26-27: Settings & Preferences

**Files**:
```
frontend/src/app/(dashboard)/settings/
├── profile/
│   └── page.tsx                # Edit profile, avatar
├── preferences/
│   └── page.tsx                # Theme, default screener, notifications
└── components/
    └── settings-form.tsx       # Reusable settings form
```

**Features**:
- [ ] Edit profile (name, avatar upload to Supabase Storage)
- [ ] Change theme preference (light/dark)
- [ ] Set default screener on login
- [ ] Notification preferences (email alerts - Phase 3)

**Deliverable**: Complete settings section

---

### Day 28: Testing & Bug Fixes

**Testing Checklist**:
- [ ] Authentication flow (all 3 methods)
- [ ] Protected routes redirect correctly
- [ ] All screeners load without errors
- [ ] Charts render correctly (light/dark mode)
- [ ] Data tables sort/filter/paginate
- [ ] Dashboard save/load works
- [ ] Mobile responsive (test on 375px width)
- [ ] Dark mode works across all pages
- [ ] No console errors

**Bug Fixes**:
- [ ] Fix any layout issues on mobile
- [ ] Fix chart responsiveness
- [ ] Fix TypeScript errors
- [ ] Fix Supabase RLS policy issues

**Deliverable**: Production-ready frontend

---

### Day 29-30: Deployment

#### **Vercel Deployment**

**Step 1: Push to GitHub**
```bash
cd /Users/mayanklavania/projects/screener
git add frontend/
git commit -m "feat: Complete Phase 2 frontend implementation"
git push origin main
```

**Step 2: Import Project to Vercel**
1. Go to https://vercel.com/new
2. Import Git Repository: `screener`
3. Configure project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

**Step 3: Environment Variables (Vercel Dashboard)**
```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
NEXT_PUBLIC_SUPABASE_URL=https://[project-id].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
```

**Step 4: Deploy**
- Click "Deploy"
- Wait ~2-3 minutes
- Get URL: `https://screener-[random].vercel.app`

**Step 5: Custom Domain (Optional)**
- Add domain in Vercel settings
- Point DNS to Vercel's servers
- Example: `screener.yourdomain.com`

#### **Docker Deployment (Self-Hosted)**

**Build Production Image**:
```bash
cd frontend
docker build -t screener-frontend:latest .
```

**Run with Docker Compose**:
```bash
cd /Users/mayanklavania/projects/screener
docker-compose --profile production up -d
```

**Access**:
- Production frontend: http://localhost:3001
- Backend API: http://localhost:8000

**Deliverable**: Live production deployment

---

## Post-Deployment Checklist

### **Phase 2 Complete When**:
- [x] Authentication working (email OTP, Google, GitHub)
- [x] All 11 screeners have dedicated pages
- [x] Dashboard customization working
- [x] Charts rendering correctly (TradingView + Plotly)
- [x] Data tables performant (sorting, filtering, pagination)
- [x] Dark mode working
- [x] Deployed to Vercel (or self-hosted)
- [x] Docker container working for local dev
- [x] Responsive on mobile/tablet
- [x] No TypeScript errors
- [x] All Shadcn components installed

---

## Critical Files Created (Summary)

### **Configuration Files**
```
frontend/
├── .env.local                  # Environment variables
├── .env.example                # Template
├── Dockerfile                  # Production build
├── Dockerfile.dev              # Development
├── next.config.mjs             # Next.js config
├── tailwind.config.ts          # Tailwind config
├── tsconfig.json               # TypeScript config
└── package.json                # Dependencies
```

### **Core Application Files**
```
frontend/src/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── (auth)/login/page.tsx   # Login page
│   ├── (dashboard)/
│   │   ├── layout.tsx          # Dashboard layout
│   │   ├── dashboard/page.tsx  # Dashboard home
│   │   └── screeners/          # 11 screener pages
│   └── auth/callback/route.ts  # OAuth callback
├── components/
│   ├── ui/                     # 30+ Shadcn components
│   ├── charts/                 # 4 chart components
│   ├── layout/                 # Header, sidebar, footer
│   ├── auth/                   # Auth components
│   └── dashboard/              # Dashboard widgets
├── lib/
│   ├── api/                    # 4 API clients
│   ├── supabase/               # 3 Supabase clients
│   ├── hooks/                  # Custom hooks
│   ├── stores/                 # Zustand stores
│   └── utils/                  # Utilities, validators
└── types/                      # TypeScript definitions
```

### **Root Files Updated**
```
/screener/
├── docker-compose.yml          # Added frontend service
└── .env                        # Added Supabase credentials
```

---

## Troubleshooting Guide

### **Issue: "Module not found" errors**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### **Issue: Supabase auth not working**
1. Check `.env.local` has correct `NEXT_PUBLIC_SUPABASE_URL`
2. Verify OAuth providers enabled in Supabase dashboard
3. Check redirect URLs configured (http://localhost:3000/auth/callback)

### **Issue: Docker build fails**
```bash
# Clear Docker cache
docker builder prune -a

# Rebuild
cd frontend
docker build --no-cache -t screener-frontend .
```

### **Issue: Charts not rendering**
1. Check browser console for errors
2. Verify `plotly.js` and `lightweight-charts` installed
3. Test with static mock data first

### **Issue: Vercel deployment fails**
1. Check build logs in Vercel dashboard
2. Verify `next.config.mjs` has `output: 'standalone'`
3. Check environment variables set correctly

---

## Next Steps After Phase 2

### **Phase 3: Backend Screener Endpoints**
Implement the 11 screener calculation endpoints:
- `POST /api/v1/screeners/rrg`
- `POST /api/v1/screeners/breakouts-4percent`
- `POST /api/v1/screeners/weekly-movers`
- ... (9 more)

### **Phase 4: Real-Time Features**
- WebSocket for live quotes
- Real-time dashboard updates
- Price alerts

### **Phase 5: Advanced Features**
- CSV/PDF export
- Saved screener configurations
- Email alerts
- Multi-language support (i18n)
- Mobile app (React Native)

---

## Resources

**Official Documentation**:
- Next.js: https://nextjs.org/docs
- Shadcn/ui: https://ui.shadcn.com
- Supabase: https://supabase.com/docs
- TanStack Table: https://tanstack.com/table/latest
- TradingView Charts: https://tradingview.github.io/lightweight-charts/
- Plotly: https://plotly.com/javascript/

**Community**:
- Next.js Discord: https://discord.gg/nextjs
- Supabase Discord: https://discord.supabase.com

**Deployment**:
- Vercel: https://vercel.com/docs
- Docker Compose: https://docs.docker.com/compose/

---

## Contact & Support

**Questions During Implementation**:
- Ask Claude (me!) for specific file implementations
- Share screenshots of UI for visual feedback
- Use Loom to record workflow issues

**Development Workflow**:
1. Implement feature
2. Test locally (`npm run dev`)
3. Commit to feature branch
4. Push to GitHub
5. Vercel auto-deploys preview
6. Review preview URL
7. Merge to main → Production deploy

---

**END OF IMPLEMENTATION PLAN**

This plan provides a day-by-day execution roadmap for building the frontend. Each day has clear deliverables and testing checkpoints. Follow sequentially for best results.

Ready to start implementation!