import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Memora",
  description: "Personal AI agent with long-term memory",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
