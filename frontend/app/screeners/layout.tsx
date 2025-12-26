import { ScreenerSidebar, MobileNav } from "@/components/layout/screener-sidebar";

export default function ScreenersLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden">
      <ScreenerSidebar />
      <MobileNav />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
