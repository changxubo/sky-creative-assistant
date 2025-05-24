// Copyright (c) 2025 Rednote Creative Assistant
// SPDX-License-Identifier: MIT
"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";

import { SiteHeader } from "./chat/components/site-header";
import { Jumbotron } from "./landing/components/jumbotron";
import { Ray } from "./landing/components/ray";
import { CaseStudySection } from "./landing/sections/case-study-section";
import { CoreFeatureSection } from "./landing/sections/core-features-section";
import { JoinCommunitySection } from "./landing/sections/join-community-section";
import { MultiAgentSection } from "./landing/sections/multi-agent-section";
import { Suspense } from "react";
import { ThemeToggle } from "../components/deer-flow/theme-toggle";
import { SettingsDialog } from "./settings/dialogs/settings-dialog";
import { Logo } from "../components/deer-flow/logo";

const Main = dynamic(() => import("./chat/main"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center">
      Loading Assistant...
    </div>
  ),
});
export default function HomePage() {
  return (
     <div className="flex h-screen w-screen justify-center overscroll-none">
          <header className="fixed top-0 left-0 flex h-12 w-full items-center justify-between px-4">
             <Logo />
            <div className="flex items-center">
              <ThemeToggle />
              <Suspense>
                <SettingsDialog />
              </Suspense>
            </div>
          </header>
          <Main />
        </div>
  )
}
export  function DefaultHomePage() {
  return (
    <div className="flex flex-col items-center hidden">
      <SiteHeader />
      <main className="container flex flex-col items-center justify-center gap-56">
        <Jumbotron />
        <CaseStudySection />
        <MultiAgentSection />
        <CoreFeatureSection />
        <JoinCommunitySection />
      </main>
      <Footer />
      <Ray />
    </div>
  );
}

function Footer() {
  const year = useMemo(() => new Date().getFullYear(), []);
  return (
    <footer className="container mt-32 flex flex-col items-center justify-center">
      <hr className="from-border/0 via-border/70 to-border/0 m-0 h-px w-full border-none bg-gradient-to-r" />
      <div className="text-muted-foreground container flex h-20 flex-col items-center justify-center text-sm">
        <p className="text-center font-serif text-lg md:text-xl">
          &quot;Originated from Open Source, give back to Open Source.&quot;
        </p>
      </div>
      <div className="text-muted-foreground container mb-8 flex flex-col items-center justify-center text-xs">
        <p>Licensed under MIT License</p>
        <p>&copy; {year} DeerFlow</p>
      </div>
    </footer>
  );
}
