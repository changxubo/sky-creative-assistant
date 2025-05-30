// Copyright (c) 2025 Rednote Creative Assistant
// SPDX-License-Identifier: MIT

import { motion } from "framer-motion";

import { cn } from "~/lib/utils";

import { Welcome } from "./welcome";

const questions = [
  "调研智能家居与AI融合话题,发布小红书笔记谈谈如何实现家电的个性化升级?",
  "特斯拉电池的平均使用寿命与汽油发动机相比是几年？",
  "研究家居与情绪管理爆款小红书笔记，创作笔记：如何通过颜色、绿植、香氛提升幸福感？",
  "查找小红书小户型家具收纳和家具推荐信息，写一篇关于小户型空间利用技巧的笔记。",
];
export function ConversationStarter({
  className,
  onSend,
}: {
  className?: string;
  onSend?: (message: string) => void;
}) {
  return (
    <div className={cn("flex flex-col items-center", className)}>
      <div className="pointer-events-none fixed inset-0 flex items-center justify-center">
        <Welcome className="pointer-events-auto mb-15 w-[75%] -translate-y-24" />
      </div>
      <ul className="flex flex-wrap">
        {questions.map((question, index) => (
          <motion.li
            key={question}
            className="flex w-1/2 shrink-0 p-2 active:scale-105"
            style={{ transition: "all 0.2s ease-out" }}
            initial={{ opacity: 0, y: 34 }}
            animate={{ opacity: 1, y: 20 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{
              duration: 0.2,
              delay: index * 0.1 + 0.5,
              ease: "easeOut",
            }}
          >
            <div
              className="bg-card text-muted-foreground cursor-pointer rounded-2xl border px-4 py-4 opacity-75 transition-all duration-300 hover:opacity-100 hover:shadow-md"
              onClick={() => {
                onSend?.(question);
              }}
            >
              {question}
            </div>
          </motion.li>
        ))}
      </ul>
    </div>
  );
}
