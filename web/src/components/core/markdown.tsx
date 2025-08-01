

import { Check, Copy } from "lucide-react";
import { useMemo, useState } from "react";
import ReactMarkdown, {
  type Options as ReactMarkdownOptions,
} from "react-markdown";

import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import "katex/dist/katex.min.css";

import { Button } from "~/components/ui/button";
import { rehypeSplitWordsIntoSpans } from "~/core/rehype";
import { autoFixMarkdown } from "~/core/utils/markdown";
import { cn } from "~/lib/utils";

import Image from "./image";
import { Tooltip } from "./tooltip";
import { Link } from "./link";


export function Markdown({
  className,
  children,
  style,
  enableCopy,
  animated = false,
  checkLinkCredibility = false,

  ...props
}: ReactMarkdownOptions & {
  className?: string;
  enableCopy?: boolean;
  style?: React.CSSProperties;
  animated?: boolean;
  checkLinkCredibility?: boolean;
 
}) {
  const components: ReactMarkdownOptions["components"] = useMemo(() => {
    return {
      a: ({ href, children }) => (
        <Link href={href} checkLinkCredibility={checkLinkCredibility}>
          {children}
        </Link>
      ),
      img: ({ src, alt }) => (
        <a href={src as string} target="_blank" rel="noopener noreferrer">
          <Image className="rounded" src={src as string} alt={alt ?? ""} />
        </a>
      ),
    };
  }, [checkLinkCredibility]);
  
  const rehypePlugins = useMemo(() => {
 
    if (animated) {
      return [rehypeKatex, rehypeSplitWordsIntoSpans];
    }
    return [rehypeKatex];
  }, [animated]);
  
  return (
    <div className={cn(className, "prose dark:prose-invert")} style={style}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={rehypePlugins}
        components={components}
        {...props}
      >
        {autoFixMarkdown(
          dropMarkdownQuote(processKatexInMarkdown(children ?? "")) ?? "",
        )}
      </ReactMarkdown>
      {enableCopy && typeof children === "string" && (
        <div className="flex">
          <CopyButton content={children} />
        </div>
      )}
    </div>
  );
}

function CopyButton({ content }: { content: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <Tooltip title="Copy">
      <Button
        variant="outline"
        size="sm"
        className="rounded-full"
        onClick={async () => {
          try {
            await navigator.clipboard.writeText(content);
            setCopied(true);
            setTimeout(() => {
              setCopied(false);
            }, 1000);
          } catch (error) {
            console.error(error);
          }
        }}
      >
        {copied ? (
          <Check className="h-4 w-4" />
        ) : (
          <Copy className="h-4 w-4" />
        )}{" "}
      </Button>
    </Tooltip>
  );
}

function processKatexInMarkdown(markdown?: string | null) {
  if (!markdown) return markdown;

  const markdownWithKatexSyntax = markdown
    .replace(/\\\\\[/g, "$$$$") // Replace '\\[' with '$$'
    .replace(/\\\\\]/g, "$$$$") // Replace '\\]' with '$$'
    .replace(/\\\\\(/g, "$$$$") // Replace '\\(' with '$$'
    .replace(/\\\\\)/g, "$$$$") // Replace '\\)' with '$$'
    .replace(/\\\[/g, "$$$$") // Replace '\[' with '$$'
    .replace(/\\\]/g, "$$$$") // Replace '\]' with '$$'
    .replace(/\\\(/g, "$$$$") // Replace '\(' with '$$'
    .replace(/\\\)/g, "$$$$"); // Replace '\)' with '$$';
  return markdownWithKatexSyntax;
}

function dropMarkdownQuote(markdown?: string | null) {
  if (!markdown) return markdown;
  return markdown
    .replace(/^```markdown\n/gm, "")
    .replace(/^```text\n/gm, "")
    .replace(/^```\n/gm, "")
    .replace(/\n```$/gm, "");
}
