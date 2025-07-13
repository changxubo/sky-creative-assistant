

import { LoadingOutlined } from "@ant-design/icons";
import { motion } from "framer-motion";
import {
  Download,
  Headphones,
  ChevronDown,
  ChevronRight,
  Lightbulb,
  ListTodo,
  NotebookPen,
} from "lucide-react";
import React, { useCallback, useMemo, useRef, useState } from "react";

import { LoadingAnimation } from "~/components/core/loading-animation";
import { Markdown } from "~/components/core/markdown";
import { RainbowText } from "~/components/core/rainbow-text";
import { RollingText } from "~/components/core/rolling-text";
import {
  ScrollContainer,
  type ScrollContainerRef,
} from "~/components/core/scroll-container";
import { Tooltip } from "~/components/core/tooltip";
import { Button } from "~/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "~/components/ui/collapsible";
import type { Message, Option } from "~/core/messages";
import {
  closeResearch,
  openResearch,
  useLastFeedbackMessageId,
  useLastInterruptMessage,
  useMessage,
  useMessageIds,
  useResearchMessage,
  useStore,
} from "~/core/store";
import { parseJSON } from "~/core/utils";
import { cn } from "~/lib/utils";

export function MessageListView({
  className,
  onFeedback,
  onSendMessage,
}: {
  className?: string;
  onFeedback?: (feedback: { option: Option }) => void;
  onSendMessage?: (
    message: string,
    options?: { interruptFeedback?: string },
  ) => void;
}) {
  const scrollContainerRef = useRef<ScrollContainerRef>(null);
  const messageIds = useMessageIds();
  const interruptMessage = useLastInterruptMessage();
  const waitingForFeedbackMessageId = useLastFeedbackMessageId();
  const responding = useStore((state) => state.responding);
  const noOngoingResearch = useStore(
    (state) => state.ongoingResearchId === null,
  );
  const ongoingResearchIsOpen = useStore(
    (state) => state.ongoingResearchId === state.openResearchId,
  );

  const handleToggleResearch = useCallback(() => {
    // Fix the issue where auto-scrolling to the bottom
    // occasionally fails when toggling research.
    const timer = setTimeout(() => {
      if (scrollContainerRef.current) {
        scrollContainerRef.current.scrollToBottom();
      }
    }, 500);
    return () => {
      clearTimeout(timer);
    };
  }, []);

  return (
    <ScrollContainer
      className={cn("flex h-full w-full flex-col overflow-hidden", className)}
      scrollShadowColor="var(--app-background)"
      autoScrollToBottom
      ref={scrollContainerRef}
    >
      <ul className="flex flex-col">
        {messageIds.map((messageId) => (
          <MessageListItem
            key={messageId}
            messageId={messageId}
            waitForFeedback={waitingForFeedbackMessageId === messageId}
            interruptMessage={interruptMessage}
            onFeedback={onFeedback}
            onSendMessage={onSendMessage}
            onToggleResearch={handleToggleResearch}
          />
        ))}
        <div className="flex h-8 w-full shrink-0"></div>
      </ul>
      {responding && (noOngoingResearch || !ongoingResearchIsOpen) && (
        <LoadingAnimation className="ml-4" />
      )}
    </ScrollContainer>
  );
}

function MessageListItem({
  className,
  messageId,
  waitForFeedback,
  interruptMessage,
  onFeedback,
  onSendMessage,
  onToggleResearch,
}: {
  className?: string;
  messageId: string;
  waitForFeedback?: boolean;
  onFeedback?: (feedback: { option: Option }) => void;
  interruptMessage?: Message | null;
  onSendMessage?: (
    message: string,
    options?: { interruptFeedback?: string },
  ) => void;
  onToggleResearch?: () => void;
}) {
  const message = useMessage(messageId);
  const background = message?.content ?? "";
  const hasMainContent = Boolean(
    message?.content && message?.content.trim() !== "",
  );
  const isStreaming = message?.isStreaming;

  const researchIds = useStore((state) => state.researchIds);
  const startOfResearch = useMemo(() => {
    return researchIds.includes(messageId);
  }, [researchIds, messageId]);
  if (message) {
    if (
      message.role === "user" ||
      message.agent === "coordinator" ||
      message.agent === "planner" ||
      message.agent === "podcast" ||
      message.agent === "background_investigator" ||
      startOfResearch
    ) {
      let content: React.ReactNode;
      if (message.agent === "background_investigator") {
        content = (
          <BackgroundBlock
            content={background}
            isStreaming={isStreaming}
            hasMainContent={hasMainContent}
          />
        );
      } else if (message.agent === "planner") {
        content = (
          <div className="w-full px-4">
            <PlanCard
              message={message}
              waitForFeedback={waitForFeedback}
              interruptMessage={interruptMessage}
              onFeedback={onFeedback}
              onSendMessage={onSendMessage}
            />
          </div>
        );
      } else if (message.agent === "podcast") {
        content = (
          <div className="w-full px-4">
            <PodcastCard message={message} />
          </div>
        );
      } else if (startOfResearch) {
        content = (
          <div className="w-full px-4">
            <ResearchCard
              researchId={message.id}
              onToggleResearch={onToggleResearch}
            />
          </div>
        );
      } else {
        content = message.content ? (
          <div
            className={cn(
              "flex w-full px-4",
              //message.role === "user" && "justify-end",
              className,
            )}
          >

            <MessageBubble message={message}>
              <div className="flex w-full flex-col text-wrap break-words">

                <Markdown
                  className={cn(
                    message.role === "user" &&
                    "prose-invert not-dark:text-secondary dark:text-inherit",
                  )}
                >
                  {message?.content}
                </Markdown>
              </div>
            </MessageBubble>
          </div>
        ) : null;
      }
      if (content) {
        return (
          <motion.li
            className="mt-10"
            key={messageId}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ transition: "all 0.2s ease-out" }}
            transition={{
              duration: 0.2,
              ease: "easeOut",
            }}
          >
            {content}
          </motion.li>
        );
      }
    }
    return null;
  }
}

function MessageBubble({
  className,
  message,
  children,
}: {
  className?: string;
  message: Message;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        `group flex w-fit max-w-[85%] flex-col rounded-2xl px-4 py-3 text-nowrap shadow`,
        message.role === "user" && "bg-brand rounded-es-none shadow-none",
        message.role === "assistant" && "bg-card rounded-es-none shadow-none",
        className,
      )}
    >
      {children}
    </div>
  );
}

function ResearchCard({
  className,
  researchId,
  onToggleResearch,
}: {
  className?: string;
  researchId: string;
  onToggleResearch?: () => void;
}) {
  const reportId = useStore((state) => state.researchReportIds.get(researchId));
  const hasReport = reportId !== undefined;
  const reportGenerating = useStore(
    (state) => hasReport && state.messages.get(reportId)!.isStreaming,
  );
  const openResearchId = useStore((state) => state.openResearchId);
  const state = useMemo(() => {
    if (hasReport) {
      return reportGenerating ? "正在生成报告..." : "报告已生成";
    }
    return "正在执行任务...";
  }, [hasReport, reportGenerating]);
  const msg = useResearchMessage(researchId);
  const title = useMemo(() => {
    if (msg) {
      return parseJSON(msg.content ?? "", { title: "" }).title;
    }
    return undefined;
  }, [msg]);
  const handleOpen = useCallback(() => {
    if (openResearchId === researchId) {
      closeResearch();
    } else {
      openResearch(researchId);
    }
    onToggleResearch?.();
  }, [openResearchId, researchId, onToggleResearch]);

  const [isOpen, setIsOpen] = useState(true);

  const [hasAutoCollapsed, setHasAutoCollapsed] = useState(false);

  const hasMainContent = true;
  const isStreaming = true;

  React.useEffect(() => {
    if (hasMainContent && !hasAutoCollapsed) {
      setIsOpen(false);
      setHasAutoCollapsed(true);
    }
  }, [hasMainContent, hasAutoCollapsed]);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          className={cn(
            "h-auto w-full justify-start rounded-es-none border px-6 py-4 text-left transition-all duration-200",
            "hover:bg-accent hover:text-accent-foreground",
            "border-0 bg-card",
          )}
        >
          <div className="flex w-full items-center gap-3">
            <NotebookPen
              size={18}
              className={cn(
                "shrink-0 transition-colors duration-200",
                "text-muted-foreground",
              )}
            />
            <span
              className={cn(
                "leading-none transition-colors duration-200 text-base",
                "text-foreground",
              )}
            >
              使用工具生成报告
            </span>
            {isStreaming && <LoadingAnimation className="ml-2 scale-75" />}
            <div className="flex-grow" />
            {isOpen ? (
              <ChevronDown
                size={16}
                className="text-muted-foreground transition-transform duration-200"
              />
            ) : (
              <ChevronRight
                size={16}
                className="text-muted-foreground transition-transform duration-200"
              />
            )}
          </div>
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:slide-up-2 data-[state=open]:slide-down-2 mt-0">
        <Card className={cn("w-full rounded-es-none shadow-none border-0", className)}>
          <CardHeader className="hidden">
            <CardTitle>
              <RainbowText animated={state !== "报告已生成"}>
                {title !== undefined && title !== "" ? title : "研究报告"}
              </RainbowText>
            </CardTitle>
          </CardHeader>
          <CardFooter>
            <div className="flex w-full">
              <RollingText className="text-muted-foreground flex-grow text-sm">
                {state}
              </RollingText>
              <Button
                variant={!openResearchId ? "default" : "outline"}
                onClick={handleOpen}
              >
                {researchId !== openResearchId ? "显示任务" : "隐藏任务"}
              </Button>
            </div>
          </CardFooter>
        </Card>
      </CollapsibleContent>
    </Collapsible>
  );
}

function BackgroundBlock({
  className,
  content,
  isStreaming,
  hasMainContent,
}: {
  className?: string;
  content: string;
  isStreaming?: boolean;
  hasMainContent?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(true);

  const [hasAutoCollapsed, setHasAutoCollapsed] = useState(false);

  React.useEffect(() => {
    if (hasMainContent && !hasAutoCollapsed) {
      setIsOpen(false);
      setHasAutoCollapsed(true);
    }
  }, [hasMainContent, hasAutoCollapsed]);

  if (!content || content.trim() === "") {
    return null;
  }

  return (
    <div className={cn("mb-0 w-full px-4", className)}>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>

          <Button
            variant="ghost"
            className={cn(
              "h-auto w-full justify-start rounded-2xl rounded-es-none border px-6 py-4 text-left transition-all duration-200",
              "hover:bg-accent hover:text-accent-foreground",
              "border-0 bg-card",
            )}
          >
            <div className="flex w-full items-center gap-3">
              <Headphones
                size={18}
                className={cn(
                  "shrink-0 transition-colors duration-200",
                  "text-muted-foreground",
                )}
              />
              <span
                className={cn(
                  "leading-none transition-colors duration-200 text-base",
                  "text-foreground",
                )}
              >
                调查问题相关背景
              </span>
              {isStreaming && <LoadingAnimation className="ml-2 scale-75" />}
              <div className="flex-grow" />
              {isOpen ? (
                <ChevronDown
                  size={16}
                  className="text-muted-foreground transition-transform duration-200"
                />
              ) : (
                <ChevronRight
                  size={16}
                  className="text-muted-foreground transition-transform duration-200"
                />
              )}
            </div>
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:slide-up-2 data-[state=open]:slide-down-2 mt-0">
          <Card
            className={cn(
              "transition-all duration-200 rounded-none shadow-none border-0",
            )}
          >
            <CardContent>
              <div className="flex h-auto w-full">
                <ScrollContainer
                  className={cn(
                    "flex h-full w-full flex-col overflow-hidden",
                    className,
                  )}
                  scrollShadow={false}
                  autoScrollToBottom
                >
                  <Markdown
                    className={cn(
                      "prose dark:prose-invert max-w-none transition-colors duration-200",
                      isStreaming ? "prose-primary" : "opacity-80",
                    )}
                    animated={isStreaming}
                  >
                    {content}
                  </Markdown>
                </ScrollContainer>
              </div>
            </CardContent>
          </Card>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}
function ThoughtBlock({
  className,
  content,
  isStreaming,
  hasMainContent,
}: {
  className?: string;
  content: string;
  isStreaming?: boolean;
  hasMainContent?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(true);

  const [hasAutoCollapsed, setHasAutoCollapsed] = useState(false);

  React.useEffect(() => {
    if (hasMainContent && !hasAutoCollapsed) {
      setIsOpen(false);
      setHasAutoCollapsed(true);
    }
  }, [hasMainContent, hasAutoCollapsed]);

  if (!content || content.trim() === "") {
    return null;
  }

  return (
    <div className={cn("mb-6 w-full", className)}>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>

          <Button
            variant="ghost"
            className={cn(
              "h-auto w-full justify-start rounded-2xl rounded-es-none border px-6 py-4 text-left transition-all duration-200",
              "hover:bg-accent hover:text-accent-foreground",
              "border-0 bg-card",
            )}
          >
            <div className="flex w-full items-center gap-3">
              <Lightbulb
                size={18}
                className={cn(
                  "shrink-0 transition-colors duration-200",
                  "text-muted-foreground",
                )}
              />
              <span
                className={cn(
                  "leading-none transition-colors duration-200 text-base",
                  "text-foreground",
                )}
              >
                深入分析课题
              </span>
              {isStreaming && <LoadingAnimation className="ml-2 scale-75" />}
              <div className="flex-grow" />
              {isOpen ? (
                <ChevronDown
                  size={16}
                  className="text-muted-foreground transition-transform duration-200"
                />
              ) : (
                <ChevronRight
                  size={16}
                  className="text-muted-foreground transition-transform duration-200"
                />
              )}
            </div>
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:slide-up-2 data-[state=open]:slide-down-2 mt-0">
          <Card
            className={cn(
              "transition-all duration-200 rounded-none shadow-none border-0",
            )}
          >
            <CardContent>
              <div className="flex h-auto w-full">
                <ScrollContainer
                  className={cn(
                    "flex h-full w-full flex-col overflow-hidden",
                    className,
                  )}
                  scrollShadow={false}
                  autoScrollToBottom
                >
                  <Markdown
                    className={cn(
                      "prose dark:prose-invert max-w-none transition-colors duration-200",
                      isStreaming ? "prose-primary" : "opacity-80",
                    )}
                    animated={isStreaming}
                  >
                    {content}
                  </Markdown>
                </ScrollContainer>
              </div>
            </CardContent>
          </Card>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

const GREETINGS = ["很酷", "听起来很厉害", "看上去不错", "非常棒", "欢迎"];
function PlanCard({
  className,
  message,
  interruptMessage,
  onFeedback,
  waitForFeedback,
  onSendMessage,
}: {
  className?: string;
  message: Message;
  interruptMessage?: Message | null;
  onFeedback?: (feedback: { option: Option }) => void;
  onSendMessage?: (
    message: string,
    options?: { interruptFeedback?: string },
  ) => void;
  waitForFeedback?: boolean;
}) {
  const plan = useMemo<{
    title?: string;
    thought?: string;
    steps?: { title?: string; description?: string }[];
  }>(() => {
    return parseJSON(message.content ?? "", {});
  }, [message.content]);

  const reasoningContent = message.reasoningContent;
  const hasMainContent = Boolean(
    message.content && message.content.trim() !== "",
  );

  // 判断是否正在思考：有推理内容但还没有主要内容
  const isThinking = Boolean(reasoningContent && !hasMainContent);
  const isStreaming = message.isStreaming;

  // 判断是否应该显示计划：有主要内容就显示（无论是否还在流式传输）
  const shouldShowPlan = hasMainContent;
  const handleAccept = useCallback(async () => {
    if (onSendMessage) {
      onSendMessage(
        `${GREETINGS[Math.floor(Math.random() * GREETINGS.length)]}! ${Math.random() > 0.5 ? "让我们开始执行吧." : "开始执行."}`,
        {
          interruptFeedback: "accepted",
        },
      );
    }
  }, [onSendMessage]);

  const [isOpen, setIsOpen] = useState(true);

  const [hasAutoCollapsed, setHasAutoCollapsed] = useState(false);

  React.useEffect(() => {
    if (hasMainContent && !hasAutoCollapsed) {
      setIsOpen(false);
      setHasAutoCollapsed(true);
    }
  }, [hasMainContent, hasAutoCollapsed]);

  return (
    <div className={cn("w-full", className)}>
      {reasoningContent && (
        <ThoughtBlock
          content={reasoningContent}
          isStreaming={isThinking}
          hasMainContent={hasMainContent}
        />
      )}
      {shouldShowPlan && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
        >
          <Collapsible open={isOpen} onOpenChange={setIsOpen} >
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                className={cn(
                  "h-auto w-full justify-start rounded-2xl rounded-es-none border px-6 py-4 text-left transition-all duration-200",
                  "hover:bg-accent hover:text-accent-foreground",
                  "border-0 bg-card",
                )}
              >
                <div className="flex w-full items-center gap-3">
                  <ListTodo
                    size={18}
                    className={cn(
                      "shrink-0 transition-colors duration-200",
                      "text-muted-foreground",
                    )}
                  />
                  <span
                    className={cn(
                      "leading-none transition-colors duration-200 text-base",
                      "text-foreground",
                    )}
                  >
                    制定详细计划
                  </span>
                  {isStreaming && <LoadingAnimation className="ml-2 scale-75" />}
                  <div className="flex-grow" />
                  {isOpen ? (
                    <ChevronDown
                      size={16}
                      className="text-muted-foreground transition-transform duration-200"
                    />
                  ) : (
                    <ChevronRight
                      size={16}
                      className="text-muted-foreground transition-transform duration-200"
                    />
                  )}
                </div>
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:slide-up-2 data-[state=open]:slide-down-2 mt-0">
              <Card className="w-full rounded-es-none border-0 shadow-none">
                <CardHeader className="hidden">
                  <CardTitle>
                    <Markdown animated={message.isStreaming}>
                      {`#### ${plan.title !== undefined && plan.title !== ""
                        ? plan.title
                        : "深度调研计划"
                        }`}
                    </Markdown>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Markdown className="opacity-80" animated={message.isStreaming}>
                    {plan.thought}
                  </Markdown>
                  {plan.steps && (
                    <ul className="my-2 flex list-decimal flex-col gap-4 border-l-[2px] pl-8">
                      {plan.steps.map((step, i) => (
                        <li key={`step-${i}`}>
                          <h5 className="mb text-lg font-medium">
                            <Markdown animated={message.isStreaming}>
                              {step.title}
                            </Markdown>
                          </h5>
                          <div className="text-muted-foreground text-sm">
                            <Markdown animated={message.isStreaming}>
                              {step.description}
                            </Markdown>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
                <CardFooter className="flex justify-end">
                  {!message.isStreaming && interruptMessage?.options?.length && (
                    <motion.div
                      className="flex gap-2"
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: 0.3 }}
                    >
                      {interruptMessage?.options.map((option) => (
                        <Button
                          key={option.value}
                          variant={
                            option.value === "accepted" ? "default" : "outline"
                          }
                          disabled={!waitForFeedback}
                          onClick={() => {
                            if (option.value === "accepted") {
                              void handleAccept();
                            } else {
                              onFeedback?.({
                                option,
                              });
                            }
                          }}
                        >
                          {option.text}
                        </Button>
                      ))}
                    </motion.div>
                  )}
                </CardFooter>
              </Card></CollapsibleContent>
          </Collapsible>
        </motion.div>
      )}
    </div>
  );
}

function PodcastCard({
  className,
  message,
}: {
  className?: string;
  message: Message;
}) {
  const data = useMemo(() => {
    return JSON.parse(message.content ?? "");
  }, [message.content]);
  const title = useMemo<string | undefined>(() => data?.title, [data]);
  const audioUrl = useMemo<string | undefined>(() => data?.audioUrl, [data]);
  const isGenerating = useMemo(() => {
    return message.isStreaming;
  }, [message.isStreaming]);
  const hasError = useMemo(() => {
    return data?.error !== undefined;
  }, [data]);
  const [isPlaying, setIsPlaying] = useState(false);
  return (
    <Card className={cn("w-[508px]", className)}>
      <CardHeader>
        <div className="text-muted-foreground flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            {isGenerating ? <LoadingOutlined /> : <Headphones size={16} />}
            {!hasError ? (
              <RainbowText animated={isGenerating}>
                {isGenerating
                  ? "Generating podcast..."
                  : isPlaying
                    ? "Now playing podcast..."
                    : "Podcast"}
              </RainbowText>
            ) : (
              <div className="text-red-500">
                Error when generating podcast. Please try again.
              </div>
            )}
          </div>
          {!hasError && !isGenerating && (
            <div className="flex">
              <Tooltip title="Download podcast">
                <Button variant="ghost" size="icon" asChild>
                  <a
                    href={audioUrl}
                    download={`${(title ?? "podcast").replaceAll(" ", "-")}.mp3`}
                  >
                    <Download size={16} />
                  </a>
                </Button>
              </Tooltip>
            </div>
          )}
        </div>
        <CardTitle>
          <div className="text-lg font-medium">
            <RainbowText animated={isGenerating}>{title}</RainbowText>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {audioUrl ? (
          <audio
            className="w-full"
            src={audioUrl}
            controls
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
          />
        ) : (
          <div className="w-full"></div>
        )}
      </CardContent>
    </Card>
  );
}
