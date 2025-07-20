"use client";
// Next.js imports
import dynamic from "next/dynamic";

import { Logo } from "~/components/core/logo";

const ChatMainComponent = dynamic(() => import("./main"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center">
      Loading Deep Research Agent...
    </div>
  ),
});

export default function ChatPage() {
  return (
    <div className="flex h-screen w-screen justify-center overscroll-none">
      <header className="fixed z-10 flex h-[15vh] w-full items-center justify-center px-4 ">
        <Logo />
      </header>
      <ChatMainComponent />
    </div>
  );
}
