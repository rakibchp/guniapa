import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Guniapa — Local skills. Trusted help.",
    template: "%s | Guniapa",
  },
  description:
    "Find skilled local service providers or grow your work with Guniapa, a community marketplace built around people.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
