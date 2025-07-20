import { motion } from "framer-motion";
import { FastForward, Play,CornerDownLeft } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { RainbowText } from "~/components/core/rainbow-text";
import { Button } from "~/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";
import { fastForwardReplay } from "~/core/api";
import { useReplayMetadata } from "~/core/api/hooks";
import type { Option, Resource } from "~/core/messages";
import { useReplay } from "~/core/replay";
import { sendMessage, useMessageIds, useStore } from "~/core/store";
import { env } from "~/env";
import { cn } from "~/lib/utils";

import { ConversationStarter } from "./conversation-starter";
import { InputBox } from "./input-box";
import { MessageListView } from "./message-list-view";
import { Welcome } from "./welcome";

interface MessagesBlockProps {
  className?: string;
}

interface MessageSendOptions {
  interruptFeedback?: string;
  resources?: Array<Resource>;
}

interface FeedbackState {
  option: Option;
}

export function MessagesBlock({ className }: MessagesBlockProps) {
  const messageIds = useMessageIds();
  const messageCount = messageIds.length;
  const responding = useStore((state) => state.responding);
  const { isReplay } = useReplay();
  const { title: replayTitle, hasError: replayHasError } = useReplayMetadata();
  const [replayStarted, setReplayStarted] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const [feedback, setFeedback] = useState<FeedbackState | null>(null);
  
  const handleSendMessage = useCallback(
    async (
      message: string,
      options?: MessageSendOptions,
    ) => {
      const abortController = new AbortController();
      abortControllerRef.current = abortController;
      
      try {
        await sendMessage(
          message,
          {
            interruptFeedback:
              options?.interruptFeedback ?? feedback?.option.value,
            resources: options?.resources,
          },
          {
            abortSignal: abortController.signal,
          },
        );
      } catch (error) {
        // Log the error for debugging while maintaining user experience
        console.error('Failed to send message:', error);
        // Consider showing user-friendly error message or retry mechanism
      } finally {
        // Clean up the abort controller reference
        if (abortControllerRef.current === abortController) {
          abortControllerRef.current = null;
        }
      }
    },
    [feedback],
  );
  const handleCancelMessage = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, []);

  const handleSetFeedback = useCallback(
    (feedback: FeedbackState) => {
      setFeedback(feedback);
    },
    [],
  );

  const handleClearFeedback = useCallback(() => {
    setFeedback(null);
  }, []);

  const handleStartReplaySession = useCallback(() => {
    setReplayStarted(true);
    // Handle potential errors in replay initialization
    try {
      void sendMessage();
    } catch (error) {
      console.error('Failed to start replay session:', error);
      setReplayStarted(false);
    }
  }, []);
  const [fastForwarding, setFastForwarding] = useState(false);
  
  // Cleanup effect to abort any pending requests on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, []);
  
  const handleToggleFastForwardReplay = useCallback(() => {
    const newFastForwardState = !fastForwarding;
    setFastForwarding(newFastForwardState);
    
    try {
      fastForwardReplay(newFastForwardState);
    } catch (error) {
      console.error('Failed to toggle fast forward replay:', error);
      // Revert state if the API call fails
      setFastForwarding(fastForwarding);
    }
  }, [fastForwarding]);
  return (
    <div className={cn("flex h-full flex-col", className)}>
      <MessageListView
        className="flex flex-grow"
        onFeedback={handleSetFeedback}
        onSendMessage={handleSendMessage}
      />
      {!isReplay ? (
        <div className="relative flex h-32 shrink-0 pb-4">
          {!responding && messageCount === 0 && (
            <ConversationStarter
              className="absolute top-[-238px] left-0"
              onSend={handleSendMessage}
            />
          )}
          <InputBox
            className="h-full w-full"
            responding={responding}
            feedback={feedback}
            onSend={handleSendMessage}
            onCancel={handleCancelMessage}
            onRemoveFeedback={handleClearFeedback}
          />
        </div>
      ) : (
        <>
          <div
            className={cn(
              "fixed bottom-[calc(50vh+120px)] transition-all duration-500 ease-out",
              replayStarted && "pointer-events-none scale-150 opacity-0",
            )}
          >
            <Welcome className="w-[75%] items-center justify-center" />
          </div>
          <motion.div
            className="mb-4 h-fit w-full items-center justify-center"
            initial={{ opacity: 0, y: "20vh" }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Card
              className={cn(
                "w-full transition-all duration-300",
                !replayStarted && "translate-y-[-40vh]",
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex flex-grow items-center">
                  {responding && (
                    <motion.div
                      className="ml-3"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      transition={{ duration: 0.3 }}
                    >
                      <video
                        // Walking deer animation, designed by @liangzhaojun. Thank you for creating it!
                        src="/images/walking_deer.webm"
                        autoPlay
                        loop
                        muted
                        className="h-[42px] w-[42px] object-contain"
                      />
                    </motion.div>
                  )}
                  <CardHeader className={cn("flex-grow", responding && "pl-3")}>
                    <CardTitle>
                      <RainbowText animated={responding}>
                        {responding ? "Replaying" : `${replayTitle}`}
                      </RainbowText>
                    </CardTitle>
                    <CardDescription>
                      <RainbowText animated={responding}>
                        {responding
                          ? "Deep Research is now replaying the conversation..."
                          : replayStarted
                            ? "The replay has been stopped."
                            : `You're now in DeepResearch's replay mode. Click the "Play" button on the right to start.`}
                      </RainbowText>
                    </CardDescription>
                  </CardHeader>
                </div>
                {!replayHasError && (
                  <div className="pr-4">
                    {responding && (
                      <Button
                        className={cn(fastForwarding && "animate-pulse")}
                        variant={fastForwarding ? "default" : "outline"}
                        onClick={handleToggleFastForwardReplay}
                      >
                        <FastForward size={16} />
                        Fast Forward
                      </Button>
                    )}
                    {!replayStarted && (
                      <Button className="w-24" onClick={handleStartReplaySession}>
                        <Play size={16} />
                        Play
                      </Button>
                    )}
                    { !responding && replayStarted && (
                       
                    <Button className="w-24" onClick={() => {
                      // Handle return to chat logic here
                      console.log("Returning to chat");
                      location.href = "/chat";
                    }}>
                        <CornerDownLeft size={16} />
                        Return
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </Card>
            {!replayStarted && env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY && (
              <div className="text-muted-foreground w-full text-center text-xs">
                * This site is for demo purposes only. If you want to try your
                own question, please{" "}
                <a
                  className="underline"
                  href="https://github.com/bytedance/deer-flow"
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Visit the DeepResearch GitHub repository"
                >
                  click here
                </a>{" "}
                to clone it locally and run it.
              </div>
            )}
          </motion.div>
        </>
      )}
    </div>
  );
}
