"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isQuantumDashboard = pathname === "/dashboard";

  if (isQuantumDashboard) {
    return <>{children}</>;
  }
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-[240px] flex-1 transition-all duration-300">
        {children}
      </main>
    </div>
  );
}
