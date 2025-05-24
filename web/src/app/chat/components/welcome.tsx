// Copyright (c) 2025 Rednote Creative Assistant
// SPDX-License-Identifier: MIT

import { motion } from "framer-motion";

import { cn } from "~/lib/utils";

export function Welcome({ className }: { className?: string }) {
  return (
    <motion.div
      className={cn("flex flex-col", className)}
      style={{ transition: "all 0.2s ease-out" }}
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
    >
      <h3 className="mb-2 text-center text-3xl font-medium">
        👋 Hello, there!
      </h3>
      <div className="text-muted-foreground px-4 text-center text-lg">
        Welcome to{" "}
        <a
          href="https://github.com/changxubo/rednote-creative-assistant"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:underline"
        >
         {/*🦌 Rednote Creative Assistant*/}
      Rednote Creative Assistant
        </a>
        , a super agent built on NVIDIA NIM models using Multi-agent collaboration (MAC) and MCP tools, helps
        you handle complex content generation tasks.
      </div>
    </motion.div>
  );
}
