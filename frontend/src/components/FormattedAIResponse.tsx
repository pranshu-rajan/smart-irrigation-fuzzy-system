'use client';

import React from 'react';

interface FormattedAIResponseProps {
  content: string;
  className?: string;
}

export default function FormattedAIResponse({ content, className = '' }: FormattedAIResponseProps) {
  if (!content) return null;

  // Split into lines to parse paragraphs, lists, and headers
  const lines = content.split('\n');
  const renderedElements: React.ReactNode[] = [];

  let inList = false;
  let listItems: React.ReactNode[] = [];

  const flushList = () => {
    if (inList && listItems.length > 0) {
      renderedElements.push(
        <ul key={`list-${renderedElements.length}`} className="my-2 space-y-1.5 pl-1">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  const parseInlineMarkdown = (text: string): React.ReactNode => {
    // Replace **bold** with <strong> and $math$ with <code>
    const parts = text.split(/(\*\*.*?\*\*|\$.*?\$|`.*?`)/g);

    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={idx} className="font-bold text-slate-900">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('$') && part.endsWith('$')) {
        return (
          <code
            key={idx}
            className="mx-0.5 rounded bg-emerald-50 px-1.5 py-0.5 font-mono text-[11px] font-semibold text-emerald-800 border border-emerald-200/80"
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code
            key={idx}
            className="mx-0.5 rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] font-medium text-slate-800"
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  lines.forEach((rawLine, idx) => {
    const line = rawLine.trim();

    // Empty line
    if (!line) {
      flushList();
      return;
    }

    // Unordered List item (- or *)
    if (line.startsWith('- ') || line.startsWith('* ')) {
      inList = true;
      const itemText = line.substring(2);
      listItems.push(
        <li key={`li-${idx}`} className="flex items-start gap-2 text-xs leading-relaxed text-slate-700">
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
          <div className="flex-1">{parseInlineMarkdown(itemText)}</div>
        </li>
      );
      return;
    }

    // Numbered list item (1. 2. etc)
    const numMatch = line.match(/^(\d+)\.\s+(.*)$/);
    if (numMatch) {
      flushList();
      renderedElements.push(
        <div key={`num-${idx}`} className="my-1.5 flex items-start gap-2 text-xs leading-relaxed text-slate-700">
          <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-emerald-100 font-mono text-[10px] font-bold text-emerald-800">
            {numMatch[1]}
          </span>
          <div className="flex-1">{parseInlineMarkdown(numMatch[2])}</div>
        </div>
      );
      return;
    }

    // Header / Section Title (e.g. **Title:** or # Title)
    if (line.startsWith('#') || (line.startsWith('**') && (line.endsWith('**') || line.endsWith('**:')))) {
      flushList();
      const cleanHeader = line.replace(/^#+\s*/, '').replace(/^\*\*/, '').replace(/\*\*:?$/, '');
      renderedElements.push(
        <div
          key={`header-${idx}`}
          className="mt-3 mb-1 text-xs font-bold uppercase tracking-wider text-emerald-950 font-sans flex items-center gap-1.5"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
          <span>{cleanHeader}</span>
        </div>
      );
      return;
    }

    // Note / Callout (*Note: ...* or Note: ...)
    if (line.startsWith('*Note:') || line.startsWith('Note:')) {
      flushList();
      const cleanNote = line.replace(/^\*Note:\s*/, '').replace(/^Note:\s*/, '').replace(/\*$/, '');
      renderedElements.push(
        <div
          key={`note-${idx}`}
          className="my-2 rounded-xl bg-emerald-50/80 border border-emerald-200/80 p-2.5 text-[11px] text-emerald-900 leading-relaxed font-sans"
        >
          <span className="font-bold">Operational Note: </span>
          {parseInlineMarkdown(cleanNote)}
        </div>
      );
      return;
    }

    // Standard paragraph
    flushList();
    renderedElements.push(
      <p key={`p-${idx}`} className="my-1.5 text-xs leading-relaxed text-slate-700 font-sans">
        {parseInlineMarkdown(line)}
      </p>
    );
  });

  flushList();

  return <div className={`space-y-1 ${className}`}>{renderedElements}</div>;
}
