"use client";

import { LoaderCircle, Paperclip, Send } from "lucide-react";
import { useEffect, useRef, type KeyboardEvent, type RefObject } from "react";
import { ChatAttachments } from "@/components/chat-attachments";

interface ChatComposerProps {
  id: string;
  value: string;
  placeholder?: string;
  workflowId?: string;
  disabled?: boolean;
  pending?: boolean;
  attachmentsUploading?: boolean;
  clearAttachmentsSignal?: number;
  textareaRef?: RefObject<HTMLTextAreaElement | null>;
  onChange: (value: string) => void;
  onSubmit: () => void | Promise<void>;
  onAttachmentChange: (attachmentIds: string[]) => void;
  onUploadingChange: (uploading: boolean) => void;
}

export function ChatComposer({
  id,
  value,
  placeholder = "Ask a follow-up...",
  workflowId,
  disabled = false,
  pending = false,
  attachmentsUploading = false,
  clearAttachmentsSignal = 0,
  textareaRef,
  onChange,
  onSubmit,
  onAttachmentChange,
  onUploadingChange,
}: ChatComposerProps) {
  const internalRef = useRef<HTMLTextAreaElement | null>(null);
  const attachmentInputRef = useRef<HTMLInputElement | null>(null);
  const inputRef = textareaRef ?? internalRef;
  const isDisabled = disabled || attachmentsUploading;

  useEffect(() => {
    const input = inputRef.current;
    if (!input) return;
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
  }, [inputRef, value]);

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey) return;
    event.preventDefault();
    if (!isDisabled && value.trim()) void onSubmit();
  }

  return <div className="ai-composer-shell">
    <form className="composer ai-composer" onSubmit={(event) => { event.preventDefault(); if (!isDisabled && value.trim()) void onSubmit(); }}>
      <ChatAttachments
        workflowId={workflowId}
        compact
        hidePicker
        inputRef={attachmentInputRef}
        disabled={isDisabled}
        clearSignal={clearAttachmentsSignal}
        onChange={onAttachmentChange}
        onUploadingChange={onUploadingChange}
      />
      <label className="sr-only" htmlFor={id}>{placeholder}</label>
      <textarea
        id={id}
        ref={inputRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={1}
        disabled={isDisabled}
      />
      <div className="composer-toolbar">
        <div className="composer-toolbar-left">
          <button className="composer-attachment-button" type="button" aria-label="Attach files" onClick={() => attachmentInputRef.current?.click()} disabled={isDisabled}>
            <Paperclip size={16} aria-hidden="true" />
          </button>
        </div>
        <button
          className={`composer-send-button${pending ? " is-loading" : ""}`}
          type="submit"
          aria-label={pending ? "Assistant is generating" : "Send message"}
          disabled={isDisabled || pending || !value.trim()}
        >
          {pending ? <LoaderCircle className="composer-spinner-icon" size={17} aria-hidden="true" /> : <Send size={17} aria-hidden="true" />}
        </button>
      </div>
    </form>
  </div>;
}
