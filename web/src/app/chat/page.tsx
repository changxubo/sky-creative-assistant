

"use client";

//import { GithubOutlined } from "@ant-design/icons";

import dynamic from "next/dynamic";
import Link from "next/link";
import { Suspense } from "react";

import { Button } from "~/components/ui/button";

import { Logo } from "../../components/deer-flow/logo";
import { ThemeToggle } from "../../components/deer-flow/theme-toggle";
import { Tooltip } from "../../components/deer-flow/tooltip";
import { SettingsDialog } from "../settings/dialogs/settings-dialog";
import { NewChat } from "../../components/deer-flow/icons/new-chat";
const Main = dynamic(() => import("./main"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center">
      Loading Deep Research Agent...
    </div>
  ),
});

export default function HomePage() {
  return (
    <div className="flex h-screen w-screen justify-center overscroll-none">
      <header className="fixed top-0 left-0 flex h-12 w-full items-center justify-between px-4">
        <Logo />
        <div className="flex items-center">
          
          <Tooltip title="New Chat">
            <Button variant="ghost" size="icon" asChild>
              <Link href="/" target="_self">
                <NewChat /> 
              </Link>
            </Button>
          </Tooltip>
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
