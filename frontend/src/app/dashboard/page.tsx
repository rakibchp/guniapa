import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";

const roleRoutes = {
  CUSTOMER: "/dashboard/customer",
  PROVIDER: "/dashboard/provider",
  ADMIN: "/dashboard/admin",
} as const;

export default async function DashboardPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  redirect(roleRoutes[user.role]);
}
