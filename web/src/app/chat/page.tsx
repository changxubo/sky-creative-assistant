// Copyright (c) 2025 Rednote Creative Assistant
// SPDX-License-Identifier: MIT

"use client";

import dynamic from "next/dynamic";
import { Suspense } from "react";
import { ThemeToggle } from "../../components/deer-flow/theme-toggle";
import { SettingsDialog } from "../settings/dialogs/settings-dialog";

const Main = dynamic(() => import("./main"), {
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
        <div className="flex items-center" style={{ paddingRight: "30px" }}>
          <ThemeToggle />
          <Suspense>
            <SettingsDialog />
          </Suspense>
        </div>
      </header>
      <Main />
    </div>


  );
}
