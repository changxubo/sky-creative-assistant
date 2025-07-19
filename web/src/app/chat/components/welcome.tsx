import { motion } from "framer-motion";

import { cn } from "~/lib/utils";

/**
 * Props interface for the Welcome component
 */
interface WelcomeProps {
  /** Optional CSS class name for custom styling */
  className?: string;
}

/**
 * Welcome component that displays an animated greeting message
 * for the Sky Creative Assistant application
 */
export function Welcome({ className }: WelcomeProps) {
  return (
    <motion.div
      className={cn("flex flex-col", className)}
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <h3 className="mb-2 text-center text-3xl font-medium">
        👋 Hello, sky walker!
      </h3>
      <div className="px-4 text-center text-lg text-muted-foreground">
        欢迎使用Sky Creative Assistant，一个深度创作助手，使用Qwen3,Deepseek,Phi-4模型和Multi-Agent协同，帮助您在联网搜索、浏览信息、生成图表和图片处理复杂创作任务。
      </div>
    </motion.div>
  );
}
