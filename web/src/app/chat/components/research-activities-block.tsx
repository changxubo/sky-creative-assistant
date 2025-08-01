import { PythonOutlined } from "@ant-design/icons";
import { motion } from "framer-motion";
import { LRUCache } from "lru-cache";
import { BookOpenText, FileText, PencilRuler, Search } from "lucide-react";
import { useTheme } from "next-themes";
import { useMemo } from "react";
import SyntaxHighlighter from "react-syntax-highlighter";
import { docco } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";

import { FavIcon } from "~/components/core/fav-icon";
import Image from "~/components/core/image";
import { LoadingAnimation } from "~/components/core/loading-animation";
import { Markdown } from "~/components/core/markdown";
import { RainbowText } from "~/components/core/rainbow-text";
import { Tooltip } from "~/components/core/tooltip";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "~/components/ui/accordion";
import { Skeleton } from "~/components/ui/skeleton";
import { findMCPTool } from "~/core/mcp";
import type { ToolCallRuntime } from "~/core/messages";
import { useMessage, useStore } from "~/core/store";
import { parseJSON } from "~/core/utils";
import { cn } from "~/lib/utils";

export function ResearchActivitiesBlock({
  className,
  researchId,
}: {
  className?: string;
  researchId: string;
}) {
  const activityIds = useStore((state) =>
    state.researchActivityIds.get(researchId),
  )!;
  const ongoing = useStore((state) => state.ongoingResearchId === researchId);
  return (
    <>
      <ul className={cn("flex flex-col py-4", className)}>
        {activityIds.map(
          (activityId, i) =>
            i !== 0 && (
              <motion.li
                key={activityId}
                style={{ transition: "all 0.4s ease-out" }}
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.4,
                  ease: "easeOut",
                }}
              >
                <ActivityMessage messageId={activityId} />
                <ActivityListItem messageId={activityId} />
                {i !== activityIds.length - 1 && <hr className="my-8" />}
              </motion.li>
            ),
        )}
      </ul>
      {ongoing && <LoadingAnimation className="mx-4 my-12" />}
    </>
  );
}

function ActivityMessage({ messageId }: { messageId: string }) {
  const message = useMessage(messageId);
  if (message?.agent && message.content) {
    if (message.agent !== "reporter" && message.agent !== "planner") {
      return (
        <div className="px-4 py-2">
          <Markdown animated checkLinkCredibility className="research-markdown">
            {message.content}
          </Markdown>
        </div>
      );
    }
  }
  return null;
}

function ActivityListItem({ messageId }: { messageId: string }) {
  const message = useMessage(messageId);
  if (message) {
    if (!message.isStreaming && message.toolCalls?.length) {
      for (const toolCall of message.toolCalls) {
        if (toolCall.name === "web_search") {
          return <WebSearchToolCall key={toolCall.id} toolCall={toolCall} />;
        } else if (toolCall.name === "crawl_tool") {
          return <CrawlToolCall key={toolCall.id} toolCall={toolCall} />;
        } else if (toolCall.name === "python_repl_tool") {
          return <PythonToolCall key={toolCall.id} toolCall={toolCall} />;
        } else if (toolCall.name === "local_search_tool") {
          return <RetrieverToolCall key={toolCall.id} toolCall={toolCall} />;
        }else if (toolCall.name === "search_notes" || toolCall.name === "get_note_details") {
          return <RednoteMCPCall key={toolCall.id} toolCall={toolCall} />;
        } else {
          return <MCPToolCall key={toolCall.id} toolCall={toolCall} />;
        }
      }
    }
  }
  return null;
}

const __pageCache = new LRUCache<string, string>({ max: 100 });
type SearchResult =
  | {
      type: "page";
      title: string;
      url: string;
      content: string;
    }
  | {
      type: "image";
      image_url: string;
      image_description: string;
    };

function WebSearchToolCall({ toolCall }: { toolCall: ToolCallRuntime }) {
  const searching = useMemo(() => {
    return toolCall.result === undefined;
  }, [toolCall.result]);
  const searchResults = useMemo<SearchResult[]>(() => {
    let results: SearchResult[] | undefined = undefined;
    try {
      results = toolCall.result ? parseJSON(toolCall.result, []) : undefined;
    } catch {
      results = undefined;
    }
    if (Array.isArray(results)) {
      results.forEach((result) => {
        if (result.type === "page") {
          __pageCache.set(result.url, result.title);
        }
      });
    } else {
      results = [];
    }
    return results;
  }, [toolCall.result]);
  const pageResults = useMemo(
    () => searchResults?.filter((result) => result.type === "page"),
    [searchResults],
  );
  const imageResults = useMemo(
    () => searchResults?.filter((result) => result.type === "image" ),
    [searchResults],
  );
  return (
    <section className="mt-4 pl-4">
      <div className="font-medium italic">
        <RainbowText
          className="flex items-center"
          animated={searchResults === undefined}
        >
          <Search size={16} className={"mr-2"} />
          <span>Searching for&nbsp;</span>
          <span className="max-w-[500px] overflow-hidden text-ellipsis whitespace-nowrap">
            {(toolCall.args as { query: string }).query}
          </span>
        </RainbowText>
      </div>
      <div className="pr-4">
        {pageResults && (
          <ul className="mt-2 flex flex-wrap gap-4">
            {searching &&
              [...Array(6)].map((_, i) => (
                <li
                  key={`search-result-${i}`}
                  className="flex h-40 w-40 gap-2 rounded-md text-sm"
                >
                  <Skeleton
                    className="to-accent h-full w-full rounded-md bg-gradient-to-tl from-slate-400"
                    style={{ animationDelay: `${i * 0.2}s` }}
                  />
                </li>
              ))}
            {pageResults
              .filter((result) => result.type === "page")
              .map((searchResult, i) => (
                <motion.li
                  key={`search-result-${i}`}
                  className="text-muted-foreground bg-accent flex max-w-40 gap-2 rounded-md px-2 py-1 text-sm"
                  initial={{ opacity: 0, y: 10, scale: 0.66 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{
                    duration: 0.2,
                    delay: i * 0.1,
                    ease: "easeOut",
                  }}
                >
                  <FavIcon
                    className="mt-1"
                    url={searchResult.url}
                    title={searchResult.title}
                  />
                  <a href={searchResult.url} target="_blank">
                    {searchResult.title}
                  </a>
                </motion.li>
              ))}
            {imageResults.map((searchResult, i) => (
              <motion.li
                key={`search-result-${i}`}
                initial={{ opacity: 0, y: 10, scale: 0.66 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{
                  duration: 0.2,
                  delay: i * 0.1,
                  ease: "easeOut",
                }}
              >
                <a
                  className="flex flex-col gap-2 overflow-hidden rounded-md opacity-75 transition-opacity duration-300 hover:opacity-100"
                  href={searchResult.image_url.includes("x-raw-image")? "/images/deer-hero.svg?with=800&height=600": searchResult.image_url}
                  target="_blank"
                >
                  <Image
                    src={searchResult.image_url.includes("x-raw-image")? "/images/deer-hero.svg?with=800&height=600": searchResult.image_url}
                    alt={searchResult.image_description}
                    className="bg-accent h-40 w-40 max-w-full rounded-md bg-cover bg-center bg-no-repeat"
                    imageClassName="hover:scale-110"
                    imageTransition
                  />
                </a>
              </motion.li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function CrawlToolCall({ toolCall }: { toolCall: ToolCallRuntime }) {
  const url = useMemo(
    () => (toolCall.args as { url: string }).url,
    [toolCall.args],
  );
  const title = useMemo(() => __pageCache.get(url), [url]);
  return (
    <section className="mt-4 pl-4">
      <div>
        <RainbowText
          className="flex items-center text-base font-medium italic"
          animated={toolCall.result === undefined}
        >
          <BookOpenText size={16} className={"mr-2"} />
          <span>Reading</span>
        </RainbowText>
      </div>
      <ul className="mt-2 flex flex-wrap gap-4">
        <motion.li
          className="text-muted-foreground bg-accent flex h-40 w-40 gap-2 rounded-md px-2 py-1 text-sm"
          initial={{ opacity: 0, y: 10, scale: 0.66 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{
            duration: 0.2,
            ease: "easeOut",
          }}
        >
          <FavIcon className="mt-1" url={url} title={title} />
          <a
            className="h-full flex-grow overflow-hidden text-ellipsis whitespace-nowrap"
            href={url}
            target="_blank"
          >
            {title ?? url}
          </a>
        </motion.li>
      </ul>
    </section>
  );
}

function RetrieverToolCall({ toolCall }: { toolCall: ToolCallRuntime }) {
  const searching = useMemo(() => {
    return toolCall.result === undefined;
  }, [toolCall.result]);
  const documents = useMemo<
    Array<{ id: string; title: string; content: string }>
  >(() => {
    return toolCall.result ? parseJSON(toolCall.result, []) : [];
  }, [toolCall.result]);
  return (
    <section className="mt-4 pl-4">
      <div className="font-medium italic">
        <RainbowText className="flex items-center" animated={searching}>
          <Search size={16} className={"mr-2"} />
          <span>Retrieving documents from RAG&nbsp;</span>
          <span className="max-w-[500px] overflow-hidden text-ellipsis whitespace-nowrap">
            {(toolCall.args as { keywords: string }).keywords}
          </span>
        </RainbowText>
      </div>
      <div className="pr-4">
        {documents && (
          <ul className="mt-2 flex flex-wrap gap-4">
            {searching &&
              [...Array(2)].map((_, i) => (
                <li
                  key={`search-result-${i}`}
                  className="flex h-40 w-40 gap-2 rounded-md text-sm"
                >
                  <Skeleton
                    className="to-accent h-full w-full rounded-md bg-gradient-to-tl from-slate-400"
                    style={{ animationDelay: `${i * 0.2}s` }}
                  />
                </li>
              ))}
            {documents.map((doc, i) => (
              <motion.li
                key={`search-result-${i}`}
                className="text-muted-foreground bg-accent flex max-w-40 gap-2 rounded-md px-2 py-1 text-sm"
                initial={{ opacity: 0, y: 10, scale: 0.66 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{
                  duration: 0.2,
                  delay: i * 0.1,
                  ease: "easeOut",
                }}
              >
                <FileText size={32} />
                {doc.title}
              </motion.li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function PythonToolCall({ toolCall }: { toolCall: ToolCallRuntime }) {
  const code = useMemo<string | undefined>(() => {
    return (toolCall.args as { code?: string }).code;
  }, [toolCall.args]);
  const { resolvedTheme } = useTheme();
  return (
    <section className="mt-4 pl-4">
      <div className="flex items-center">
        <PythonOutlined className={"mr-2"} />
        <RainbowText
          className="text-base font-medium italic"
          animated={toolCall.result === undefined}
        >
          Running Python code
        </RainbowText>
      </div>
      <div>
        <div className="bg-accent mt-2 max-h-[400px] max-w-[calc(100%-120px)] overflow-y-auto rounded-md p-2 text-sm">
          <SyntaxHighlighter
            language="python"
            style={resolvedTheme === "dark" ? atomDark : docco}
            customStyle={{
              background: "transparent",
              border: "none",
              boxShadow: "none",
            }}
          >
            {code?.trim() ?? ""}
          </SyntaxHighlighter>
        </div>
      </div>
      {toolCall.result && <PythonToolCallResult result={toolCall.result} />}
    </section>
  );
}

function PythonToolCallResult({ result }: { result: string }) {
  const { resolvedTheme } = useTheme();
  const hasError = useMemo(
    () => result.includes("Error executing code:\n"),
    [result],
  );
  const error = useMemo(() => {
    if (hasError) {
      const parts = result.split("```\nError: ");
      if (parts.length > 1) {
        return parts[1]!.trim();
      }
    }
    return null;
  }, [result, hasError]);
  const stdout = useMemo(() => {
    if (!hasError) {
      const parts = result.split("```\nStdout: ");
      if (parts.length > 1) {
        return parts[1]!.trim();
      }
    }
    return null;
  }, [result, hasError]);
  return (
    <>
      <div className="mt-4 font-medium italic">
        {hasError ? "Error when executing the above code" : "Execution output"}
      </div>
      <div className="bg-accent mt-2 max-h-[400px] max-w-[calc(100%-120px)] overflow-y-auto rounded-md p-2 text-sm">
        <SyntaxHighlighter
          language="plaintext"
          style={resolvedTheme === "dark" ? atomDark : docco}
          customStyle={{
            color: hasError ? "red" : "inherit",
            background: "transparent",
            border: "none",
            boxShadow: "none",
          }}
        >
          {error ?? stdout ?? "(empty)"}
        </SyntaxHighlighter>
      </div>
    </>
  );
}
const __noteCache = new LRUCache<string, string>({ max: 100 });
type RednotePageResult ={
    id: string;
    modelType: string;
    xsecToken: string;
    noteCard: {
      type: string;
      displayTitle: string;
      user: {
        userId: string;
        nickname: string;
        xsecToken: string;
      }
      cover: {
        urlPre: string;
        urlDefault: string;
        width: number;
        height: number;
      };
      interactInfo: {
        likedCount: number;
      };
    }
  }
type RednoteImageResult = {
      note_id: string;
      title: string;
      desc: string;
      type: string;
      user: string;
      time: string;
      counts: {
        collected: number;
        liked: number;
        comment: number;
        share: number;
      },
      images: [],
      video: {}
    }
type RednoteResult =
  | RednotePageResult | RednoteImageResult;

function RednoteMCPCall({ toolCall }: { toolCall: ToolCallRuntime }) {
  const searching = useMemo(() => {
    return toolCall.result === undefined;
  }, [toolCall.result]);
  function hasNoteCard(result: RednoteResult): result is Extract<RednoteResult, { modelType: string }> {
    return (result as RednotePageResult).modelType !== undefined;
  }
  
  const searchResults = useMemo<RednoteResult[]>(() => {
    let results: RednoteResult[] | undefined = undefined;
    try {
      results = toolCall.result ? parseJSON(toolCall.result, []) : undefined;
    } catch {
      results = undefined;
    }
    if (Array.isArray(results)) {
      results.forEach((result) => {
        if (hasNoteCard(result)) {
          __noteCache.set(result.id, result.noteCard.displayTitle);
        }
      });
    } else {
      results = [];
    }
    return results;
  }, [toolCall.result]);
  
  const noteResults = useMemo(
    () => searchResults?.filter((result) => hasNoteCard(result)),
    [searchResults],
  );
  const imageResults = useMemo(
    () => searchResults?.filter((result) => hasNoteCard(result)),
    [searchResults],
  );

  return (
    <section className="mt-4 pl-4">
      <div className="font-medium italic">
        <RainbowText
          className="flex items-center"
          animated={searchResults === undefined}
        >
          <Search size={16} className={"mr-2"} />
          <span>Searching for&nbsp;</span>
          <span className="max-w-[500px] overflow-hidden text-ellipsis whitespace-nowrap">
            {(toolCall.args as { query: string }).query}
          </span>
        </RainbowText>
      </div>
      <div className="pr-4">
        {noteResults && (
          <ul className="mt-2 flex flex-wrap gap-4">
            {searching &&
              [...Array(6)].map((_, i) => (
                <li
                  key={`search-result-${i}`}
                  className="flex h-40 w-40 gap-2 rounded-md text-sm"
                >
                  <Skeleton
                    className="to-accent h-full w-full rounded-md bg-gradient-to-tl from-slate-400"
                    style={{ animationDelay: `${i * 0.2}s` }}
                  />
                </li>
              ))}
            {noteResults
          
              .map((searchResult, i) => (
                <motion.li
                  key={`search-result-${i}`}
                  className="text-muted-foreground bg-accent flex max-w-40 gap-2 rounded-md px-2 py-1 text-sm"
                  initial={{ opacity: 0, y: 10, scale: 0.66 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{
                    duration: 0.2,
                    delay: i * 0.1,
                    ease: "easeOut",
                  }}
                >
                  <FavIcon
                    className="mt-1"
                    url={`https://www.xiaohongshu.com/discovery/item/${searchResult.id}?source=webshare&xhsshare=pc_web&xsec_token=${searchResult.xsecToken}&xsec_source=pc_share`}
                    title={searchResult.noteCard.displayTitle}
                  />
                  <a href={`https://www.xiaohongshu.com/discovery/item/${searchResult.id}?source=webshare&xhsshare=pc_web&xsec_token=${searchResult.xsecToken}&xsec_source=pc_share`} target="_blank">
                    {searchResult.noteCard.displayTitle}
                  </a>
                </motion.li>
              ))}
            {imageResults.map((searchResult, i) => (
              <motion.li
                key={`search-result-${i}`}
                initial={{ opacity: 0, y: 10, scale: 0.66 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{
                  duration: 0.2,
                  delay: i * 0.1,
                  ease: "easeOut",
                }}
              >
                
                  <a
                    key={`note-image-${i}`}
                    className="flex flex-col gap-2 overflow-hidden rounded-md opacity-75 transition-opacity duration-300 hover:opacity-100"
                    href={`https://www.xiaohongshu.com/discovery/item/${searchResult.id}?source=webshare&xhsshare=pc_web&xsec_token=${searchResult.xsecToken}&xsec_source=pc_share`}
                    target="_blank"
                  >
                    <Image
                      src={searchResult.noteCard.cover.urlDefault}
                      alt={searchResult.noteCard.displayTitle}
                      className="bg-accent h-40 w-40 max-w-full rounded-md bg-cover bg-center bg-no-repeat"
                      imageClassName="hover:scale-110"
                      imageTransition
                    />
                  </a>
                 
              </motion.li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
function MCPToolCall({ toolCall }: { toolCall: ToolCallRuntime }) {
  const tool = useMemo(() => findMCPTool(toolCall.name), [toolCall.name]);
  const { resolvedTheme } = useTheme();
  return (
    <section className="mt-4 pl-4">
      <div className="w-fit overflow-y-auto rounded-md py-0">
        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="item-1">
            <AccordionTrigger>
              <Tooltip title={tool?.description}>
                <div className="flex items-center font-medium italic">
                  <PencilRuler size={16} className={"mr-2"} />
                  <RainbowText
                    className="pr-0.5 text-base font-medium italic"
                    animated={toolCall.result === undefined}
                  >
                    Running {toolCall.name ? toolCall.name + "()" : "MCP tool"}
                  </RainbowText>
                </div>
              </Tooltip>
            </AccordionTrigger>
            <AccordionContent>
              {toolCall.result && (
                <div className="bg-accent max-h-[400px] max-w-[560px] overflow-y-auto rounded-md text-sm">
                  <SyntaxHighlighter
                    language="json"
                    style={resolvedTheme === "dark" ? atomDark : docco}
                    customStyle={{
                      background: "transparent",
                      border: "none",
                      boxShadow: "none",
                    }}
                  >
                    {toolCall.result.trim()}
                  </SyntaxHighlighter>
                </div>
              )}
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    </section>
  );
}
