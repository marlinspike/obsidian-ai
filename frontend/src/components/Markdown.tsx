import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { useTheme } from "@/hooks/useTheme";
import { Copy, Check } from "lucide-react";
import { useState } from "react";

interface MarkdownProps {
  content: string;
  className?: string;
}

function CodeBlock({
  language,
  value,
}: {
  language: string | undefined;
  value: string;
}) {
  const { resolvedTheme } = useTheme();
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-4">
      {/* Language label & copy button */}
      <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-4 py-2 bg-[rgb(var(--muted))] dark:bg-gray-800 border-b border-[rgb(var(--border))] rounded-t-xl">
        <span className="text-xs font-medium text-[rgb(var(--muted-foreground))] uppercase tracking-wider">
          {language || "code"}
        </span>
        <button
          onClick={copyToClipboard}
          className="flex items-center gap-1 text-xs text-[rgb(var(--muted-foreground))] hover:text-[rgb(var(--foreground))] transition-colors"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-green-500" />
              <span className="text-green-500">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code content */}
      <SyntaxHighlighter
        style={resolvedTheme === "dark" ? oneDark : oneLight}
        language={language || "text"}
        PreTag="div"
        customStyle={{
          margin: 0,
          borderRadius: "0.75rem",
          paddingTop: "3rem",
          fontSize: "0.875rem",
          lineHeight: "1.5",
        }}
        codeTagProps={{
          style: {
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
          },
        }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
}

export function Markdown({ content, className = "" }: MarkdownProps) {
  return (
    <div className={`prose prose-sm dark:prose-invert max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
        // Code blocks with syntax highlighting
        code({ className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || "");
          const isInline = !match && !className;

          if (isInline) {
            return (
              <code
                className="px-1.5 py-0.5 rounded-md bg-[rgb(var(--muted))] text-obsidian-700 dark:text-obsidian-300 font-mono text-sm border border-[rgb(var(--border))]"
                {...props}
              >
                {children}
              </code>
            );
          }

          return (
            <CodeBlock
              language={match ? match[1] : undefined}
              value={String(children).replace(/\n$/, "")}
            />
          );
        },

        // Styled headings
        h1: ({ children }) => (
          <h1 className="text-2xl font-bold text-[rgb(var(--foreground))] mt-6 mb-4 pb-2 border-b border-[rgb(var(--border))]">
            {children}
          </h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-xl font-semibold text-[rgb(var(--foreground))] mt-5 mb-3">
            {children}
          </h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-lg font-semibold text-[rgb(var(--foreground))] mt-4 mb-2">
            {children}
          </h3>
        ),
        h4: ({ children }) => (
          <h4 className="text-base font-semibold text-[rgb(var(--foreground))] mt-3 mb-2">
            {children}
          </h4>
        ),

        // Paragraphs
        p: ({ children }) => (
          <p className="text-[rgb(var(--foreground))] leading-relaxed mb-4 last:mb-0">
            {children}
          </p>
        ),

        // Lists
        ul: ({ children }) => (
          <ul className="list-disc list-outside ml-5 mb-4 space-y-1.5 text-[rgb(var(--foreground))]">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-outside ml-5 mb-4 space-y-1.5 text-[rgb(var(--foreground))]">
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li className="text-[rgb(var(--foreground))] leading-relaxed pl-1">
            {children}
          </li>
        ),

        // Blockquotes
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-obsidian-400 dark:border-obsidian-600 pl-4 py-1 my-4 italic text-[rgb(var(--muted-foreground))] bg-[rgb(var(--muted))] rounded-r-lg">
            {children}
          </blockquote>
        ),

        // Links
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-obsidian-600 dark:text-obsidian-400 hover:text-obsidian-800 dark:hover:text-obsidian-300 underline underline-offset-2 decoration-obsidian-300 dark:decoration-obsidian-700 hover:decoration-obsidian-500"
          >
            {children}
          </a>
        ),

        // Strong/bold text
        strong: ({ children }) => (
          <strong className="font-semibold text-[rgb(var(--foreground))]">
            {children}
          </strong>
        ),

        // Emphasis/italic text
        em: ({ children }) => (
          <em className="italic text-[rgb(var(--foreground))]">{children}</em>
        ),

        // Horizontal rule
        hr: () => (
          <hr className="my-6 border-[rgb(var(--border))]" />
        ),

        // Tables
        table: ({ children }) => (
          <div className="overflow-x-auto my-4 rounded-xl border border-[rgb(var(--border))]">
            <table className="min-w-full divide-y divide-[rgb(var(--border))]">
              {children}
            </table>
          </div>
        ),
        thead: ({ children }) => (
          <thead className="bg-[rgb(var(--muted))]">{children}</thead>
        ),
        tbody: ({ children }) => (
          <tbody className="divide-y divide-[rgb(var(--border))]">{children}</tbody>
        ),
        tr: ({ children }) => <tr>{children}</tr>,
        th: ({ children }) => (
          <th className="px-4 py-3 text-left text-xs font-semibold text-[rgb(var(--foreground))] uppercase tracking-wider">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="px-4 py-3 text-sm text-[rgb(var(--foreground))]">
            {children}
          </td>
        ),

        // Task lists (GFM)
        input: ({ checked, ...props }) => (
          <input
            type="checkbox"
            checked={checked}
            readOnly
            className="mr-2 h-4 w-4 rounded border-[rgb(var(--border))] text-obsidian-600 focus:ring-obsidian-500"
            {...props}
          />
        ),

        // Pre (fallback for code blocks without language)
        pre: ({ children }) => (
          <pre className="overflow-x-auto">{children}</pre>
        ),
      }}
    >
      {content}
      </ReactMarkdown>
    </div>
  );
}
