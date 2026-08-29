import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Codebase Q&A Agent",
  description: "Ask questions about any GitHub repository with cited answers.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-zinc-950 text-zinc-100">{children}</body>
    </html>
  );
}