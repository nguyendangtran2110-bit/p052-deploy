"use client";

import { AlertCircle, Check, Paperclip, RefreshCw, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Badge, IconButton, ProgressBar } from "@/components/ui";
import { uploadAttachment, validateAttachment } from "@/lib/data";
import { formatFileSize } from "@/lib/format";

type UploadState = "uploading" | "ready" | "failed";

interface ChatAttachmentItem {
  id: string;
  file: File;
  filename: string;
  size_bytes: number;
  mime_type: string;
  progress: number;
  status: UploadState;
  error?: string;
}

interface ChatAttachmentsProps {
  workflowId?: string;
  disabled?: boolean;
  maxFiles?: number;
  clearSignal?: number;
  onChange: (attachmentIds: string[]) => void;
  onUploadingChange?: (uploading: boolean) => void;
}

export function ChatAttachments({ workflowId, disabled = false, maxFiles = 10, clearSignal = 0, onChange, onUploadingChange }: ChatAttachmentsProps) {
  const [items, setItems] = useState<ChatAttachmentItem[]>([]);
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const callbackRef = useRef(onChange);
  const uploadingCallbackRef = useRef(onUploadingChange);
  callbackRef.current = onChange;
  uploadingCallbackRef.current = onUploadingChange;

  useEffect(() => {
    callbackRef.current(items.filter((item) => item.status === "ready").map((item) => item.id));
    uploadingCallbackRef.current?.(items.some((item) => item.status === "uploading"));
  }, [items]);

  useEffect(() => {
    if (clearSignal > 0) setItems([]);
  }, [clearSignal]);

  function updateItem(id: string, patch: Partial<ChatAttachmentItem>) {
    setItems((current) => current.map((item) => item.id === id ? { ...item, ...patch } : item));
  }

  async function uploadOne(item: ChatAttachmentItem) {
    updateItem(item.id, { status: "uploading", progress: 0, error: undefined });
    try {
      const uploaded = await uploadAttachment(item.file, { workflow_id: workflowId }, (progress) => updateItem(item.id, { progress }));
      updateItem(item.id, { id: uploaded.id, status: "ready", progress: 100 });
    } catch (error) {
      updateItem(item.id, { status: "failed", error: error instanceof Error ? error.message : "Upload failed" });
    }
  }

  function addFiles(fileList: FileList | null) {
    if (!fileList || disabled) return;
    const selected = Array.from(fileList);
    if (items.length + selected.length > maxFiles) {
      setSelectionError(`Maximum ${maxFiles} attachments per message.`);
      return;
    }
    const next: ChatAttachmentItem[] = [];
    for (const file of selected) {
      const error = validateAttachment(file);
      if (error) {
        setSelectionError(error);
        continue;
      }
      next.push({
        id: `pending-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        file,
        filename: file.name,
        size_bytes: file.size,
        mime_type: file.type || "application/octet-stream",
        progress: 0,
        status: "uploading",
      });
    }
    if (!next.length) return;
    setSelectionError(null);
    setItems((current) => [...current, ...next]);
    for (const item of next) void uploadOne(item);
  }

  function remove(id: string) {
    setItems((current) => current.filter((item) => item.id !== id));
  }

  return <div className="chat-attachments">
    <label className="attachment-picker" title="Attach files">
      <Paperclip size={15} />
      <span>Attach</span>
      <input type="file" hidden multiple accept="image/*,.pdf,.doc,.docx,.txt" disabled={disabled || items.length >= maxFiles} onChange={(event) => { addFiles(event.target.files); event.currentTarget.value = ""; }} />
    </label>
    {items.map((item) => <div className="chat-attachment-row" key={item.id}>
      <div className="chat-attachment-copy"><strong title={item.filename}>{item.filename}</strong><span>{formatFileSize(item.size_bytes)}</span>{item.status === "uploading" && <ProgressBar value={item.progress} tone="teal" />}</div>
      {item.status === "uploading" && <Badge tone="info">{item.progress}%</Badge>}
      {item.status === "ready" && <Badge tone="success"><Check size={11} /> Ready</Badge>}
      {item.status === "failed" && <Badge tone="danger"><AlertCircle size={11} /> {item.error ?? "Failed"}</Badge>}
      {item.status === "failed" && <IconButton label={`Retry ${item.filename}`} onClick={() => void uploadOne(item)} disabled={disabled}><RefreshCw size={14} /></IconButton>}
      <IconButton label={`Remove ${item.filename}`} onClick={() => remove(item.id)} disabled={disabled}><X size={14} /></IconButton>
    </div>)}
    {selectionError && <p className="field-error" role="alert">{selectionError}</p>}
  </div>;
}
