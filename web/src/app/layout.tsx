import "~/styles/globals.css";

import { type Metadata } from "next";
import { Geist } from "next/font/google";
import Script from "next/script";
import { type ReactNode } from "react";

import { ThemeProviderWrapper } from "~/components/core/theme-provider-wrapper";
import { Toaster } from "~/components/core/toaster";
import { env } from "~/env";

export const metadata: Metadata = {
  title: "Amway Creative Assistant",
  description:"Multi-agent system and MCP tools using NVIDIA NIM and Langchain.",
  icons: [{ rel: "icon", url: "/favicon.ico" }],
};

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

interface RootLayoutProps {
  readonly children: ReactNode;
}

export default async function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" className={`${geist.variable}`} suppressHydrationWarning>
      <head>
        {/* Define isSpace function globally to fix markdown-it issues with Next.js + Turbopack
          https://github.com/markdown-it/markdown-it/issues/1082#issuecomment-2749656365 */}
        <Script id="markdown-it-fix" strategy="beforeInteractive">
          {`
            try {
              if (typeof window !== 'undefined' && typeof window.isSpace === 'undefined') {
                window.isSpace = function(code) {
                  return code === 0x20 || code === 0x09 || code === 0x0A || code === 0x0B || code === 0x0C || code === 0x0D;
                };
              }
            } catch (error) {
              console.warn('Failed to initialize markdown-it fix:', error);
            }
          `}
        </Script>
      </head>
      <body className="bg-app">
        <ThemeProviderWrapper>{children}</ThemeProviderWrapper>
        <Toaster />
        {
          // NO USER BEHAVIOR TRACKING OR PRIVATE DATA COLLECTION BY DEFAULT
          //
          // When `NEXT_PUBLIC_STATIC_WEBSITE_ONLY` is `true`, the script will be injected
          // into the page only when `AMPLITUDE_API_KEY` is provided in `.env`
        }
        {env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY && env.AMPLITUDE_API_KEY && (
          <>
            <Script
              src="https://cdn.amplitude.com/script/d2197dd1df3f2959f26295bb0e7e849f.js"
              strategy="lazyOnload"
            />
            <Script id="amplitude-init" strategy="lazyOnload">
              {`
                window.amplitude.init('${env.AMPLITUDE_API_KEY.replace(/'/g, "\\'")}', {
                  "fetchRemoteConfig": true,
                  "autocapture": true
                });
              `}
            </Script>
          </>
        )}
      </body>
    </html>
  );
}
