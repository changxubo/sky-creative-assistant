"use client";

// React imports
import { useMemo } from "react";

// Store and utilities
import { useStore } from "~/core/store";
import { cn } from "~/lib/utils";

// Local components
import { MessagesBlock } from "./components/messages-block";
import { ResearchBlock } from "./components/research-block";

// Layout constants for better maintainability
const LAYOUT_CONSTANTS = {
  MESSAGE_COLUMN_WIDTH: 43,
  MESSAGE_COLUMN_WIDTH_SINGLE: 75,
  RESEARCH_COLUMN_WIDTH: 55,
  LAYOUT_PADDING: "px-4 pt-20 pb-4",
  COLUMN_GAP: "gap-8",
  TRANSITION: "transition-all duration-300 ease-out",
} as const;

interface ChatLayoutProps {
  className?: string;
}

/**
 * Validates if the research ID is a valid format
 * @param id - Research ID to validate
 * @returns boolean indicating if ID is valid
 */
function isValidResearchId(id: string | null): id is string {
  return typeof id === "string" && id.length > 0 && id.trim() !== "";
}

/**
 * ChatLayout - Main layout component for the chat interface
 * Handles responsive dual-column layout with messages and research panels
 * 
 * @param {ChatLayoutProps} props - Component props
 * @returns {JSX.Element} The rendered chat layout
 */
export default function ChatLayout({ className }: ChatLayoutProps = {}) {
  const openResearchId = useStore((state) => state.openResearchId);
  
  // Validate research ID and memoize layout mode calculation
  const isDoubleColumnMode = useMemo(
    () => isValidResearchId(openResearchId),
    [openResearchId],
  );

  // Memoize complex className calculations for better performance
  const messagesBlockClassName = useMemo(() => {
    const baseClasses = `${LAYOUT_CONSTANTS.TRANSITION}`; //shrink-0 
    
    if (isDoubleColumnMode) {
      return cn(baseClasses, `w-[${LAYOUT_CONSTANTS.MESSAGE_COLUMN_WIDTH}%] min-w-[560px] max-w-[1260px]`);
    }
    
    // Single column mode - center the messages block
    const singleModeClasses = `w-[${LAYOUT_CONSTANTS.MESSAGE_COLUMN_WIDTH_SINGLE}%]`; //translate-x-0
    return cn(baseClasses, singleModeClasses);
  }, [isDoubleColumnMode]);

  const researchBlockClassName = useMemo(() => {
    const baseClasses = `pb-4 ${LAYOUT_CONSTANTS.TRANSITION}`;
    
    if (isDoubleColumnMode) {
      const responsiveWidth = `w-[${LAYOUT_CONSTANTS.RESEARCH_COLUMN_WIDTH}%] min-w-[575px] max-w-[1260px]`;
      return cn(baseClasses, responsiveWidth);
    }
    
    // Single column mode - hide research block by setting width to 0
    return cn(baseClasses, "w-0 overflow-hidden scale-0");
  }, [isDoubleColumnMode]);

  return (
    <main
      className={cn(
        "flex h-full w-full",
        isDoubleColumnMode ? "justify-center-safe" : "justify-center",
        LAYOUT_CONSTANTS.LAYOUT_PADDING,
        isDoubleColumnMode && LAYOUT_CONSTANTS.COLUMN_GAP,
        className,
      )}
      role="main"
      aria-label="Chat interface"
    >
      <MessagesBlock
        className={messagesBlockClassName}
        aria-label="Messages panel"
      />
      <ResearchBlock
        className={researchBlockClassName}
        researchId={openResearchId}
        aria-label="Research panel"
        aria-hidden={!isDoubleColumnMode}
      />
    </main>
  );
}
