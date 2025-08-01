import { motion } from "framer-motion";

import { cn } from "~/lib/utils";

import { Welcome } from "./welcome";

// Predefined conversation starter questions with diverse topics
const CONVERSATION_STARTER_QUESTIONS = [
  "机器人如何改变农业生产方式?",
  //"如何通过颜色、绿植、香氛提升幸福感？",
  "特斯拉电池的平均使用寿命与汽油发动机相比是几年？",
  //"自然语言处理领域有哪些进展?",
  "机器学习如何改变金融行业?",
  "量子计算对密码学的影响是什么?",
  "气候变化如何影响全球农业?",
  "具身智能机器人的未来发展方向是什么?",
] as const;

/**
 * Handles the selection of a conversation starter question
 * @param question - The selected question text
 * @param onSend - Optional callback function to handle the selected question
 */
const handleQuestionSelect = (
  question: string,
  onSend?: (message: string) => void
): void => {
  try {
    if (onSend && typeof onSend === 'function') {
      onSend(question);
    }
  } catch (error) {
    console.error('Error handling question selection:', error);
    // Optionally, you could add user-facing error handling here
  }
};

interface ConversationStarterProps {
  className?: string;
  onSend?: (message: string) => void;
}

export function ConversationStarter({
  className,
  onSend,
}: ConversationStarterProps) {
  return (
    <div className={cn("flex flex-col items-center", className)}>
      <div className="pointer-events-none fixed inset-0 flex items-center justify-center">
        <Welcome className="pointer-events-auto mb-15 w-[75%] -translate-y-24" />
      </div>

      <ul className="flex flex-wrap" role="list" aria-label="Conversation starter questions">
        {CONVERSATION_STARTER_QUESTIONS.map((question: string, index: number) => (
          <motion.li
            key={question}
            className="flex w-1/2 shrink-1 p-1 active:scale-105"
            style={{ transition: "all 0.2s ease-out" }}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{
              duration: 0.2,
              delay: index * 0.1 + 0.5,
              ease: "easeOut",
            }}
          >
            <button
              type="button"
              className="bg-card text-muted-foreground w-full cursor-pointer rounded-2xl border px-4 py-4 text-center opacity-75 transition-all duration-300 hover:opacity-100 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              onClick={() => handleQuestionSelect(question, onSend)}
              aria-label={`Ask question: ${question}`}
            >
              {question}
            </button>
          </motion.li>
        ))}
      </ul>

    </div>
  );
}
