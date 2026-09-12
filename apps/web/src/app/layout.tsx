import type { Metadata } from "next";
import { Syne, Source_Serif_4 } from "next/font/google";
import "./globals.css";

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-display",
});

const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "NEXUS — NovaCart Decision Intelligence",
  description: "Simulate decisions. Discover better strategies. Act with confidence.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${syne.variable} ${sourceSerif.variable}`}>{children}</body>
    </html>
  );
}
