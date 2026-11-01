import type { Metadata } from "next";
import { RoleDashboard } from "@/features/dashboard/role-dashboard";

export const metadata: Metadata = { title: "Administrator account" };

export default function AdminDashboardPage() {
  return <RoleDashboard role="ADMIN" />;
}
