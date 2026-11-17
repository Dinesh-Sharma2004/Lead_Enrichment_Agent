import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lead Enrichment Agent | Corporate Intelligence Engine",
  description:
    "Turn company websites into structured, evidence-backed B2B corporate intelligence using autonomous link discovery, content cleaning, and Groq LLMs.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0b0f19] text-slate-100 antialiased selection:bg-sky-500/20 selection:text-sky-300">
        {children}
      </body>
    </html>
  );
}

