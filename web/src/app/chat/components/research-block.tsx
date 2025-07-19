import { Check, Copy, Download, Headphones, Pencil, Undo2, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { ScrollContainer } from "~/components/core/scroll-container";
import { Tooltip } from "~/components/core/tooltip";
import { Button } from "~/components/ui/button";
import { Card } from "~/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { useReplay } from "~/core/replay";
import { closeResearch, listenToPodcast, useStore } from "~/core/store";
import { cn } from "~/lib/utils";

// Local component imports
import { ResearchActivitiesBlock } from "./research-activities-block";
import { ResearchReportBlock } from "./research-report-block";

// Types
interface ResearchBlockProps {
  className?: string;
  researchId: string | null;
}

type TabValue = "report" | "activities";

export function ResearchBlock({
  className,
  researchId = null,
}: ResearchBlockProps) {
  const reportId = useStore((state) =>
    researchId ? state.researchReportIds.get(researchId) : undefined,
  );
  const [activeTab, setActiveTab] = useState<TabValue>("activities");
  const [editing, setEditing] = useState(false);
  const [copied, setCopied] = useState(false);
  
  const hasReport = useStore((state) =>
    researchId ? state.researchReportIds.has(researchId) : false,
  );
  const reportStreaming = useStore((state) =>
    reportId ? (state.messages.get(reportId)?.isStreaming ?? false) : false,
  );
  const { isReplay } = useReplay();
  // Auto-switch to report tab when report becomes available
  useEffect(() => {
    if (hasReport) {
      setActiveTab("report");
    }
  }, [hasReport]);

  // Reset to activities tab when research changes or report is unavailable
  useEffect(() => {
    if (!hasReport) {
      setActiveTab("activities");
    }
  }, [hasReport, researchId]);

  const handleGeneratePodcastFromResearch = useCallback(async () => {
    if (!researchId) {
      console.warn('Cannot generate podcast: researchId is null');
      return;
    }
    
    try {
      await listenToPodcast(researchId);
    } catch (error) {
      console.error('Failed to generate podcast:', error);
      // Could add user notification here
    }
  }, [researchId]);

  const handleCopyReportToClipboard = useCallback(() => {
    if (!reportId) {
      console.warn('Cannot copy report: reportId is null');
      return;
    }
    
    const report = useStore.getState().messages.get(reportId);
    if (!report) {
      console.warn('Cannot copy report: report not found');
      return;
    }
    
    navigator.clipboard.writeText(report.content)
      .then(() => {
        setCopied(true);
        setTimeout(() => {
          setCopied(false);
        }, 1000);
      })
      .catch((error) => {
        console.error('Failed to copy report to clipboard:', error);
        // Could add user notification here
      });
  }, [reportId]);

  const handleDownloadReportAsMarkdown = useCallback(() => {
    if (!reportId) {
      console.warn('Cannot download report: reportId is null');
      return;
    }
    
    const report = useStore.getState().messages.get(reportId);
    if (!report) {
      console.warn('Cannot download report: report not found');
      return;
    }
    
    try {
      const now = new Date();
      const pad = (n: number) => n.toString().padStart(2, '0');
      const timestamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;
      
      // Sanitize filename to prevent path traversal
      const filename = `research-report-${timestamp}.md`;
      
      const blob = new Blob([report.content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      
      const downloadLink = document.createElement('a');
      downloadLink.href = url;
      downloadLink.download = filename;
      downloadLink.style.display = 'none';
      
      document.body.appendChild(downloadLink);
      downloadLink.click();
      
      // Clean up immediately
      setTimeout(() => {
        document.body.removeChild(downloadLink);
        URL.revokeObjectURL(url);
      }, 0);
    } catch (error) {
      console.error('Failed to download report:', error);
      // Could add user notification here
    }
  }, [reportId]);

  const handleToggleEditMode = useCallback(() => {
    setEditing((prevEditing) => !prevEditing);
  }, []);

  const handleCloseResearchPanel = useCallback(() => {
    try {
      closeResearch();
    } catch (error) {
      console.error('Failed to close research panel:', error);
    }
  }, []);

  return (
    <div className={cn("flex h-full w-full flex-col", className)}>
      <Card className={cn("relative h-full w-full pt-4 border-0 shadow-none", className)}>
        <div className="absolute right-4 flex h-9 items-center justify-center">
          {hasReport && !reportStreaming && (
            <>
              <Tooltip title="Generate podcast">
                <Button
                  className="text-gray-400"
                  size="icon"
                  variant="ghost"
                  disabled={isReplay}
                  onClick={handleGeneratePodcastFromResearch}
                >
                  <Headphones />
                </Button>
              </Tooltip>
              <Tooltip title="Edit">
                <Button
                  className="text-gray-400"
                  size="icon"
                  variant="ghost"
                  disabled={isReplay}
                  onClick={handleToggleEditMode}
                >
                  {editing ? <Undo2 /> : <Pencil />}
                </Button>
              </Tooltip>
              <Tooltip title="Copy">
                <Button
                  className="text-gray-400"
                  size="icon"
                  variant="ghost"
                  onClick={handleCopyReportToClipboard}
                >
                  {copied ? <Check /> : <Copy />}
                </Button>
              </Tooltip>
              <Tooltip title="Download report as markdown">
                <Button
                  className="text-gray-400"
                  size="icon"
                  variant="ghost"
                  onClick={handleDownloadReportAsMarkdown}
                >
                  <Download />
                </Button>
              </Tooltip>
            </>
          )}
          <Tooltip title="Close">
            <Button
              className="text-gray-400"
              size="sm"
              variant="ghost"
              onClick={handleCloseResearchPanel}
            >
              <X />
            </Button>
          </Tooltip>
        </div>
        <Tabs
          className="flex h-full w-full flex-col"
          value={activeTab}
          onValueChange={(value) => setActiveTab(value as TabValue)}
        >
          <div className="flex w-full justify-center">
            <TabsList className="">
              <TabsTrigger
                className="px-8"
                value="report"
                disabled={!hasReport}
              >
                Report
              </TabsTrigger>
              <TabsTrigger className="px-8" value="activities">
                Activities
              </TabsTrigger>
            </TabsList>
          </div>
          <TabsContent
            className="h-full min-h-0 flex-grow px-8"
            value="report"
            forceMount
            hidden={activeTab !== "report"}
          >
            <ScrollContainer
              className="h-full px-5 pb-20"
              scrollShadowColor="var(--card)"
              autoScrollToBottom={!hasReport || reportStreaming}
            >
              {reportId && researchId && (
                <ResearchReportBlock
                  className="mt-4"
                  researchId={researchId}
                  messageId={reportId}
                  editing={editing}
                />
              )}
            </ScrollContainer>
          </TabsContent>
          <TabsContent
            className="h-full min-h-0 flex-grow px-8"
            value="activities"
            forceMount
            hidden={activeTab !== "activities"}
          >
            <ScrollContainer
              className="h-full"
              scrollShadowColor="var(--card)"
              autoScrollToBottom={!hasReport || reportStreaming}
            >
              {researchId && (
                <ResearchActivitiesBlock
                  className="mt-4"
                  researchId={researchId}
                />
              )}
            </ScrollContainer>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}
