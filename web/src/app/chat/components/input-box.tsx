// React imports
import { useCallback, useRef, useState, Suspense } from "react";

import Link from "next/link";

// Third-party library imports
import { MagicWandIcon } from "@radix-ui/react-icons";
import { AnimatePresence, motion } from "framer-motion";
import { Lightbulb, X } from "lucide-react";

// Local component imports
import { Search } from "~/components/core/icons/search";
import { SendMessage } from "~/components/core/icons/send-message";
import MessageInput, {
  type MessageInputRef,
} from "~/components/core/message-input";
import { ReportStyleDialog } from "~/components/core/report-style-dialog";
import { Tooltip } from "~/components/core/tooltip";
import { NewChat } from "~/components/core/icons/new-chat";
import { ThemeToggle } from "~/components/core/theme-toggle";
import { BorderBeam } from "~/components/magicui/border-beam";
import { Button } from "~/components/ui/button";

import { SettingsDialog } from "../../settings/dialogs/settings-dialog";

// API and core imports
import { enhancePrompt } from "~/core/api";
import { useConfig } from "~/core/api/hooks";
import type { Option, Resource } from "~/core/messages";
import {
  setEnableBackgroundInvestigation,
  setEnableDeepThinking,
  useSettingsStore,
} from "~/core/store";

// Utility imports
import { cn } from "~/lib/utils";

interface InputBoxProps {
  className?: string;
  size?: "large" | "normal";
  responding?: boolean;
  feedback?: { option: Option } | null;
  onSend?: (
    message: string,
    options?: {
      interruptFeedback?: string;
      resources?: Array<Resource>;
    },
  ) => void;
  onCancel?: () => void;
  onRemoveFeedback?: () => void;
}

export function InputBox({
  className,
  responding,
  feedback,
  onSend,
  onCancel,
  onRemoveFeedback,
}: InputBoxProps) {
  const enableDeepThinking = useSettingsStore(
    (state) => state.general.enableDeepThinking,
  );
  const backgroundInvestigation = useSettingsStore(
    (state) => state.general.enableBackgroundInvestigation,
  );
  const { config, loading } = useConfig();
  const reportStyle = useSettingsStore((state) => state.general.reportStyle);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<MessageInputRef>(null);
  const feedbackRef = useRef<HTMLDivElement>(null);

  // Enhancement state
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [isEnhanceAnimating, setIsEnhanceAnimating] = useState(false);
  const [currentPrompt, setCurrentPrompt] = useState("");
  const [enhanceError, setEnhanceError] = useState<string | null>(null);

  const handleSendMessage = useCallback(
    (message: string, resources: Array<Resource>) => {
      if (responding) {
        onCancel?.();
      } else {
        if (message.trim() === "") {
          return;
        }
        if (onSend) {
          onSend(message, {
            interruptFeedback: feedback?.option.value,
            resources,
          });
          onRemoveFeedback?.();
          // Clear enhancement animation and errors after sending
          setIsEnhanceAnimating(false);
          setEnhanceError(null);
        }
      }
    },
    [responding, onCancel, onSend, feedback, onRemoveFeedback],
  );

  const handlePromptEnhancement = useCallback(async () => {
    if (currentPrompt.trim() === "" || isEnhancing) {
      return;
    }

    setIsEnhancing(true);
    setIsEnhanceAnimating(true);
    setEnhanceError(null);

    try {
      const enhancedPrompt = await enhancePrompt({
        prompt: currentPrompt,
        report_style: reportStyle.toUpperCase(),
      });

      // Validate the enhanced prompt
      if (!enhancedPrompt || typeof enhancedPrompt !== 'string') {
        throw new Error('Invalid response from enhancement service');
      }

      // Add a small delay for better UX
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Update the input with the enhanced prompt with animation
      if (inputRef.current) {
        inputRef.current.setContent(enhancedPrompt);
        setCurrentPrompt(enhancedPrompt);
      }

      // Keep animation for a bit longer to show the effect
      setTimeout(() => {
        setIsEnhanceAnimating(false);
      }, 1000);
    } catch (error) {
      console.error("Failed to enhance prompt:", error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to enhance prompt';
      setEnhanceError(errorMessage);
      setIsEnhanceAnimating(false);
    } finally {
      setIsEnhancing(false);
    }
  }, [currentPrompt, isEnhancing, reportStyle]);

  const handleCancelOperation = useCallback(() => {
    if (responding && onCancel) {
      onCancel();
    }
  }, [responding, onCancel]);

  const handleToggleDeepThinking = useCallback(() => {
    setEnableDeepThinking(!enableDeepThinking);
  }, [enableDeepThinking]);

  const handleToggleBackgroundInvestigation = useCallback(() => {
    setEnableBackgroundInvestigation(!backgroundInvestigation);
  }, [backgroundInvestigation]);

  const handleRemoveFeedback = useCallback(() => {
    onRemoveFeedback?.();
  }, [onRemoveFeedback]);

  const handleSubmitInput = useCallback(() => {
    inputRef.current?.submit();
  }, []);

  return (
    <div
      className={cn(
        "bg-card relative flex h-full w-full flex-col rounded-[24px] border",
        className,
      )}
      ref={containerRef}
    >
      <div className="w-full">
        <AnimatePresence>
          {feedback && (
            <motion.div
              ref={feedbackRef}
              className="bg-background border-brand absolute top-0 left-0 mt-2 ml-4 flex items-center justify-center gap-1 rounded-2xl border px-2 py-0.5"
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0 }}
              transition={{ duration: 0.2, ease: "easeInOut" }}
            >
              <div className="text-brand flex h-full w-full items-center justify-center text-sm opacity-90">
                {feedback.option.text}
              </div>
              <X
                className="cursor-pointer opacity-60 hover:opacity-100 transition-opacity"
                size={16}
                onClick={handleRemoveFeedback}
                aria-label="Remove feedback"
              />
            </motion.div>
          )}
          {isEnhanceAnimating && (
            <motion.div
              className="pointer-events-none absolute inset-0 z-20"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="relative h-full w-full">
                {/* Sparkle effect overlay */}
                <motion.div
                  className="absolute inset-0 rounded-[24px] bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-blue-500/10"
                  animate={{
                    background: [
                      "linear-gradient(45deg, rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.1), rgba(59, 130, 246, 0.1))",
                      "linear-gradient(225deg, rgba(147, 51, 234, 0.1), rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.1))",
                      "linear-gradient(45deg, rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.1), rgba(59, 130, 246, 0.1))",
                    ],
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
                {/* Floating sparkles */}
                {[...Array(6)].map((_, i) => (
                  <motion.div
                    key={i}
                    className="absolute h-2 w-2 rounded-full bg-blue-400"
                    style={{
                      left: `${20 + i * 12}%`,
                      top: `${30 + (i % 2) * 40}%`,
                    }}
                    animate={{
                      y: [-10, -20, -10],
                      opacity: [0, 1, 0],
                      scale: [0.5, 1, 0.5],
                    }}
                    transition={{
                      duration: 1.5,
                      repeat: Infinity,
                      delay: i * 0.2,
                    }}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <MessageInput
          className={cn(
            "h-12 px-4 pt-5",
            feedback && "pt-9",
            isEnhanceAnimating && "transition-all duration-500",
            enhanceError && "border-red-500/50",
          )}
          ref={inputRef}
          loading={loading}
          config={config}
          onEnter={handleSendMessage}
          onChange={setCurrentPrompt}
        />
        {enhanceError && (
          <div className="px-4 py-1">
            <div className="text-red-500 text-xs bg-red-50 dark:bg-red-950/20 px-2 py-1 rounded">
              {enhanceError}
            </div>
          </div>
        )}
      </div>
      <div className="flex items-center px-4 py-2">
        <div className="flex grow gap-2">
          {config?.models.reasoning?.[0] && (
            <Tooltip
              className="max-w-60"
              title={
                <div>
                  <h3 className="mb-2 font-bold">
                    Deep Thinking Mode: {enableDeepThinking ? "On" : "Off"}
                  </h3>
                  <p>
                    When enabled, Agent will use reasoning model (
                    {config.models.reasoning?.[0]}) to generate more thoughtful
                    plans.
                  </p>
                </div>
              }
            >
              <Button
                className={cn(
                  "rounded-2xl",
                  enableDeepThinking && "!border-brand !text-brand",
                )}
                variant="outline"
                size="sm"
                onClick={handleToggleDeepThinking}
                aria-label={`Toggle deep thinking mode ${enableDeepThinking ? 'off' : 'on'}`}
              >
                <Lightbulb /> 深度思考
              </Button>
            </Tooltip>
          )}

          <Tooltip
            className="max-w-60"
            title={
              <div>
                <h3 className="mb-2 font-bold">
                  Investigation Mode: {backgroundInvestigation ? "On" : "Off"}
                </h3>
                <p>
                  When enabled, Agent will perform a quick search before
                  planning. This is useful for researches related to ongoing
                  events and news.
                </p>
              </div>
            }
          >
            <Button
              className={cn(
                "rounded-2xl",
                backgroundInvestigation && "!border-brand !text-brand",
              )}
              variant="outline"
              size="sm"
              onClick={handleToggleBackgroundInvestigation}
              aria-label={`Toggle investigation mode ${backgroundInvestigation ? 'off' : 'on'}`}
            >
              <Search /> 联网搜索
            </Button>
          </Tooltip>
          <ReportStyleDialog />
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Tooltip title="Start New Chat">
            <Button
              variant="ghost"
              size="icon"
              asChild
              aria-label="Start a new chat conversation"
            >
              <Link href="/" target="_self">
                <NewChat />
              </Link>
            </Button>
          </Tooltip>
          <Tooltip title="Themes">
            <ThemeToggle />
          </Tooltip>
          <Tooltip title="Settings">
            <Suspense fallback={<div className="w-10 h-10" />}>
              <SettingsDialog />
            </Suspense>
          </Tooltip>
          <Tooltip title="Enhance prompt with AI">
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "hover:bg-accent h-10 w-10",
                isEnhancing && "animate-pulse",
                enhanceError && "border-red-500/50",
              )}
              onClick={handlePromptEnhancement}
              disabled={isEnhancing || currentPrompt.trim() === ""}
              aria-label="Enhance prompt with AI"
            >
              {isEnhancing ? (
                <div className="flex h-10 w-10 items-center justify-center">
                  <div className="bg-foreground h-3 w-3 animate-bounce rounded-full opacity-70" />
                </div>
              ) : (
                <MagicWandIcon className="text-brand" />
              )}
            </Button>
          </Tooltip>
          <Tooltip title={responding ? "Stop" : "Send"}>
            <Button
              variant="outline"
              size="icon"
              className={cn("h-10 w-10 rounded-full")}
              onClick={handleSubmitInput}
              aria-label={responding ? "Stop generation" : "Send message"}
            >
              {responding ? (
                <div className="flex h-10 w-10 items-center justify-center">
                  <div className="bg-foreground h-4 w-4 rounded-sm opacity-70" />
                </div>
              ) : (
                <SendMessage />
              )}
            </Button>
          </Tooltip>
        </div>
      </div>
      {isEnhancing && (
        <>
          <BorderBeam
            duration={5}
            size={250}
            className="from-transparent via-red-500 to-transparent"
          />
          <BorderBeam
            duration={5}
            delay={3}
            size={250}
            className="from-transparent via-blue-500 to-transparent"
          />
        </>
      )}
    </div>
  );
}
