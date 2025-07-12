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
        👋 Hello, Creator!
      </h3>
      <div className="text-muted-foreground px-4 text-center text-lg">
        欢迎使用Sky Creative Assistant，这是一个基于NVIDIA NIM深度研究助手，多Agent协同Qwen3,Deepseek,Phi-4模型推理，帮助您在网络上搜索、浏览信息、生成图表和图片处理复杂创作任务。
      </div>
      
    </motion.div>
  );
}
