import { useEffect, useMemo, useState } from "react";
import { ArrowRight } from "lucide-react";
import BoomerangVideoBg from "./components/BoomerangVideoBg";
import {
  agentSummary,
  capabilities,
  checklist,
  conciergeAnswer,
  issueKeywords,
  resident,
  ticketCategories,
  type DemoTab,
  type ZaloMessage,
  zaloMessages,
} from "./data";

type TicketRole = "resident" | "management";
type TicketStatus = "Draft" | "Submitted" | "Approved" | "Rejected";

type TicketDraft = {
  resident: string;
  unit: string;
  category: string;
  priority: string;
  location: string;
  description: string;
  source: string;
};

type DetectedIssue = {
  category: string;
  keyword: string;
  sourceText: string;
};

const tabLabels: Array<[DemoTab, string]> = [
  ["landing", "Landing"],
  ["onboarding", "Onboarding"],
  ["zalo", "Demo Zalo chat"],
  ["ticket", "Ticket"],
];

function Logo() {
  return (
    <a className="flex items-center gap-2.5" href="#landing" aria-label="Boomerang home">
      <svg className="h-6 w-6 text-[#191919]" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">
        <path d="M 144 256 L 27.598 256 L 144 139.598 Z M 256 207.5 L 200 256 L 200 56 L 0 56 L 48 0 L 256 0 Z M 0 204.402 L 0 112 L 92.402 112 Z" />
      </svg>
      <span className="text-base font-semibold tracking-tight text-[#191919]">Boomerang</span>
    </a>
  );
}

function StatusDot({ complete }: { complete: boolean }) {
  return <span className={`status-dot ${complete ? "status-dot-complete" : "status-dot-pending"}`}>{complete ? "✓" : ""}</span>;
}

function TabNavigation({ activeTab, navigate }: { activeTab: DemoTab; navigate: (tab: DemoTab) => void }) {
  return (
    <div className="app-tab-list" role="tablist" aria-label="Demo pages">
      {tabLabels.map(([tab, label]) => (
        <button
          key={tab}
          className={`app-tab ${activeTab === tab ? "app-tab-active" : ""}`}
          onClick={() => navigate(tab)}
          role="tab"
          aria-selected={activeTab === tab}
          type="button"
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function AppNav({ activeTab, navigate }: { activeTab: DemoTab; navigate: (tab: DemoTab) => void }) {
  return (
    <nav className={`app-nav ${activeTab === "landing" ? "app-nav-landing" : ""}`}>
      <Logo />
      <TabNavigation activeTab={activeTab} navigate={navigate} />
      <button className="nav-context-button" onClick={() => navigate("ticket")} type="button">
        Open demo
      </button>
    </nav>
  );
}

function detectIssue(text: string): DetectedIssue | null {
  const normalized = text.toLowerCase();
  const match = [...issueKeywords].sort((a, b) => b.keyword.length - a.keyword.length).find((item) => normalized.includes(item.keyword));
  return match ? { ...match, sourceText: text } : null;
}

function LandingView({ navigate }: { navigate: (tab: DemoTab) => void }) {
  return (
    <>
      <section id="landing" className="relative flex min-h-[700px] h-screen flex-col items-center overflow-hidden">
        <BoomerangVideoBg />
        <div className="relative z-10 flex w-full flex-col items-center px-4 pt-28 text-center sm:px-6 md:pt-36">
          <h1 className="max-w-5xl font-serif text-4xl font-normal leading-[1.1] tracking-tighter text-[#191919] sm:text-5xl md:text-7xl lg:text-8xl">
            Build lasting
            <br />
            relationships.
          </h1>
          <p className="mt-5 max-w-sm text-sm leading-relaxed text-[#191919]/70 sm:mt-6 sm:max-w-md md:mt-8 md:text-base">
            Conversational AI platform for modern financial institutions — agents that handle the full borrower lifecycle across email, SMS, and voice.
          </p>
          <button className="button-dark mt-7 px-6 py-3 text-sm sm:mt-9 sm:px-8 sm:py-3.5" onClick={() => navigate("onboarding")} type="button">
            Explore the demo
          </button>
        </div>

        <div className="relative z-10 mt-auto w-full max-w-5xl px-4 sm:px-6">
          <div className="border border-b-0 border-gray-200 bg-white/90 px-5 pt-8 shadow-sm backdrop-blur-sm sm:px-8 sm:pt-12 md:px-12 md:pt-16">
            <div className="grid gap-6 md:grid-cols-2 md:gap-16">
              <div>
                <p className="eyebrow">What do we do?</p>
                <h2 className="mt-3 max-w-md font-serif text-2xl font-normal leading-tight tracking-tight sm:text-3xl md:text-4xl">
                  Conversations that
                  <br className="hidden sm:block" /> build momentum
                </h2>
              </div>
              <p className="self-end text-sm leading-relaxed text-[#191919]/70 md:text-[15px]">
                Conversational AI built for resident onboarding and post-handover care. Agents that listen, organize, and show their work before a ticket moves forward.
              </p>
            </div>
            <div className="my-6 h-px w-full bg-gray-200 sm:my-8 md:my-10" />
            <div className="grid gap-2 pb-0 sm:grid-cols-3 sm:gap-3">
              {([
                ["01", "Onboarding", "onboarding" as DemoTab],
                ["02", "Demo Zalo chat", "zalo" as DemoTab],
                ["03", "Ticket flow", "ticket" as DemoTab],
              ] as Array<[string, string, DemoTab]>).map(([number, label, tab]) => (
                <button key={tab} className="feature-row group" onClick={() => navigate(tab)} type="button">
                  <span><span className="text-[#191919]/40">{number}</span><span className="mx-2 text-[#191919]/30">/</span><span className="font-medium">{label}</span></span>
                  <ArrowRight className="h-4 w-4 text-gray-400 transition-all duration-200 group-hover:translate-x-0.5 group-hover:text-gray-700" />
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="capability-section landing-capabilities">
        <div className="section-intro">
          <p className="eyebrow">A connected resident journey</p>
          <h2 className="section-title">One conversation, every next step.</h2>
          <p className="section-lede">Explore the three working surfaces behind the promise: guided onboarding, a Zalo signal layer, and a human-approved ticket flow.</p>
        </div>
        <div className="landing-route-grid">
          {capabilities.map((capability, index) => {
            const tab: DemoTab = index === 0 ? "onboarding" : index === 1 ? "zalo" : "ticket";
            return <button key={capability.label} className="landing-route-card" onClick={() => navigate(tab)} type="button"><span className="capability-index">0{index + 1}</span><span className="capability-name">{capability.label}</span><span className="capability-description">{capability.description}</span><ArrowRight className="h-4 w-4 text-[#191919]/40" /></button>;
          })}
        </div>
      </section>
      <footer className="flex flex-col justify-between gap-4 border-t border-gray-200 px-6 py-7 text-xs text-[#191919]/45 sm:flex-row sm:px-14"><span>© 2026 Boomerang</span><span>Conversational AI for lasting relationships.</span></footer>
    </>
  );
}

function OnboardingView({ completedSteps, activeStep, setActiveStep, toggleStep, chatDraft, setChatDraft, sendChat, navigate }: {
  completedSteps: string[];
  activeStep: number;
  setActiveStep: (step: number) => void;
  toggleStep: (id: string) => void;
  chatDraft: string;
  setChatDraft: (value: string) => void;
  sendChat: () => void;
  navigate: (tab: DemoTab) => void;
}) {
  const progress = Math.round((completedSteps.length / checklist.length) * 100);
  const current = checklist[activeStep] ?? checklist[0];
  return (
    <section className="app-view section-shell" id="onboarding">
      <div className="view-heading"><div><p className="eyebrow">01 / Onboarding agent</p><h1 className="view-title">Một khởi đầu thật rõ ràng.</h1><p className="view-lede">Agent dẫn đường cho cư dân từ ngày nhận nhà đến khi mọi tiện ích và yêu cầu đầu tiên đã được xử lý.</p></div><button className="button-light" onClick={() => navigate("zalo")} type="button">Try Demo Zalo <ArrowRight className="inline h-4 w-4" /></button></div>
      <div className="onboarding-grid">
        <article className="workspace-panel checklist-panel">
          <div className="panel-heading"><div><p className="panel-kicker">Checklist của cư dân</p><h3>{resident.name} · {resident.unit}</h3></div><span className="progress-number">{progress}%</span></div>
          <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
          <div className="step-list">
            {checklist.map((item, index) => {
              const complete = completedSteps.includes(item.id);
              const active = index === activeStep;
              return <button key={item.id} className={`onboarding-step ${active ? "onboarding-step-active" : ""}`} onClick={() => setActiveStep(index)} type="button"><StatusDot complete={complete} /><span><span className="step-number">{item.step}</span><strong>{item.label}</strong><small>{item.detail}</small></span><ArrowRight className="ml-auto h-4 w-4" /></button>;
            })}
          </div>
          <div className="checklist-footer"><span>{completedSteps.length} / {checklist.length} bước hoàn thành</span><span>Ngày bàn giao {resident.handover}</span></div>
        </article>
        <article className="workspace-panel onboarding-chat-panel">
          <div className="panel-heading"><div><p className="panel-kicker">Onboarding concierge</p><h3>Bây giờ làm gì?</h3></div><span className="live-dot"><span /> Agent online</span></div>
          <div className="onboarding-current"><span className="current-label">Bước hiện tại · {current.step}</span><h2>{current.label}</h2><p>{current.detail}. Agent sẽ giữ lại ngữ cảnh này trong các câu hỏi tiếp theo.</p><button className="button-dark" onClick={() => toggleStep(current.id)} type="button">{completedSteps.includes(current.id) ? "Đánh dấu chưa xong" : "Hoàn thành bước"}</button></div>
          <div className="chat-thread onboarding-thread"><div className="chat-bubble chat-bubble-agent">{conciergeAnswer.answer}<span className="citation">Nguồn: {conciergeAnswer.source} <ArrowRight className="inline h-3 w-3 -rotate-45" /></span></div><div className="chat-bubble chat-bubble-user">Tôi muốn được hướng dẫn từng bước.</div><div className="chat-bubble chat-bubble-agent">Được ạ. Mình đang ở bước {current.step} — {current.label}. Anh/chị có thể hoàn thành ở bảng bên trái, hoặc hỏi mình bất cứ lúc nào.</div></div>
          <div className="chat-input-wrap"><input aria-label="Hỏi onboarding agent" value={chatDraft} onChange={(event) => setChatDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") sendChat(); }} placeholder="Hỏi agent về bước này..." /><button aria-label="Gửi câu hỏi" className="send-button" onClick={sendChat} type="button"><ArrowRight className="h-4 w-4" /></button></div>
        </article>
        <aside className="workspace-panel summary-panel"><p className="panel-kicker">Agent memory</p><h3>Resident summary</h3><div className="summary-block"><span>Hồ sơ</span><strong>Đã xác thực</strong><small>CCCD và thông tin căn hộ đã khớp</small></div><div className="summary-block"><span>Tiện ích</span><strong>2 việc cần làm</strong><small>Thẻ cư dân · Đăng ký internet</small></div><div className="summary-block"><span>Open request</span><strong>1 yêu cầu</strong><small>REQ-12345 · {resident.unit}</small></div><button className="summary-link" onClick={() => navigate("ticket")} type="button">Xem ticket của tôi <ArrowRight className="h-4 w-4" /></button></aside>
      </div>
    </section>
  );
}

function ZaloView({ messages, draft, setDraft, sendMessage, detectedIssue, dismissIssue, createTicket, navigate }: {
  messages: ZaloMessage[];
  draft: string;
  setDraft: (value: string) => void;
  sendMessage: () => void;
  detectedIssue: DetectedIssue | null;
  dismissIssue: () => void;
  createTicket: () => void;
  navigate: (tab: DemoTab) => void;
}) {
  const importantCount = messages.filter((message) => message.important).length;
  return (
    <section className="app-view section-shell" id="zalo">
      <div className="view-heading"><div><p className="eyebrow">02 / Zalo signal layer</p><h1 className="view-title">Không bỏ sót điều quan trọng.</h1><p className="view-lede">Agent đọc luồng chat đông đúc, gom những tín hiệu cần xử lý và đưa đúng vấn đề vào ticket.</p></div><div className="unread-badge"><strong>800</strong><span>tin nhắn chưa đọc</span></div></div>
      <div className="zalo-grid">
        <article className="workspace-panel zalo-chat-panel">
          <div className="zalo-header"><div><p className="panel-kicker">Zalo group</p><h3>The River Residence · Cư dân</h3></div><span className="message-count">{messages.length} tin nhắn mock</span></div>
          <div className="zalo-messages" aria-label="Danh sách tin nhắn Zalo">
            {messages.map((message) => <div key={message.id} className={`zalo-message ${message.sender === "Cư dân" ? "zalo-message-resident" : "zalo-message-management"} ${message.important ? "zalo-message-important" : ""}`}><div className="zalo-message-meta"><strong>{message.sender}</strong><span>{message.time}</span></div><p>{message.text}</p>{message.important && <span className="issue-chip">Agent detected · {message.issueType}</span>}</div>)}
          </div>
          <div className="chat-input-wrap"><input aria-label="Nhắn tin Zalo" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") sendMessage(); }} placeholder="Nhập tin nhắn để agent phân loại..." /><button aria-label="Gửi tin nhắn Zalo" className="send-button" onClick={sendMessage} type="button"><ArrowRight className="h-4 w-4" /></button></div>
        </article>
        <aside className="workspace-panel signal-panel"><div className="panel-heading"><div><p className="panel-kicker">Agent summary</p><h3>Important signals</h3></div><span className="signal-count">{importantCount} nhóm vấn đề</span></div><p className="signal-intro">Rule-based agent đang quét các từ khóa: <strong>nước, điện, cháy, nứt, hỏng, mất mạng</strong>.</p><div className="signal-list">{agentSummary.map((signal) => <button key={signal.issueType} className="signal-item" onClick={() => setDraft(`${signal.issueType} tại căn ${resident.unit}, nhờ ban quản lý kiểm tra giúp.`)} type="button"><span className={`severity severity-${signal.severity === "Khẩn cấp" ? "urgent" : signal.severity === "Cao" ? "high" : "medium"}`}>{signal.severity}</span><span><strong>{signal.issueType}</strong><small>{signal.count} báo cáo · {signal.detail}</small></span><ArrowRight className="ml-auto h-4 w-4" /></button>)}</div><div className="signal-footer"><span>Last sweep</span><strong>Vừa xong · 09:58</strong></div><button className="button-dark w-full" onClick={() => navigate("ticket")} type="button">Mở ticket queue <ArrowRight className="inline h-4 w-4" /></button></aside>
      </div>
      {detectedIssue && <div className="agent-toast" role="dialog" aria-label="Agent phát hiện vấn đề"><span className="toast-kicker">Agent detected a possible issue</span><strong>Phát hiện từ khóa “{detectedIssue.keyword}”</strong><p>Agent có thể tạo ticket thuộc nhóm <b>{detectedIssue.category}</b> và điền sẵn nội dung cho bạn xác nhận.</p><div className="toast-actions"><button className="button-light" onClick={dismissIssue} type="button">Để sau</button><button className="button-dark" onClick={createTicket} type="button">Có, tạo ticket <ArrowRight className="inline h-4 w-4" /></button></div></div>}
    </section>
  );
}

function TicketView({ role, setRole, draft, setDraft, status, submit, approve, navigate }: {
  role: TicketRole;
  setRole: (role: TicketRole) => void;
  draft: TicketDraft;
  setDraft: (draft: TicketDraft) => void;
  status: TicketStatus;
  submit: () => void;
  approve: () => void;
  navigate: (tab: DemoTab) => void;
}) {
  const update = (key: keyof TicketDraft, value: string) => setDraft({ ...draft, [key]: value });
  return (
    <section className="app-view section-shell" id="ticket">
      <div className="view-heading"><div><p className="eyebrow">03 / Ticket workflow</p><h1 className="view-title">Một ticket rõ ràng, một người chịu trách nhiệm.</h1><p className="view-lede">Hai role trong cùng một flow demo: cư dân kiểm tra thông tin, quản lý duyệt trước khi hệ thống tạo ticket.</p></div><div className="role-switch" role="tablist" aria-label="Ticket role"><button className={role === "resident" ? "role-button-active" : ""} onClick={() => setRole("resident")} role="tab" aria-selected={role === "resident"} type="button">Cư dân</button><button className={role === "management" ? "role-button-active" : ""} onClick={() => setRole("management")} role="tab" aria-selected={role === "management"} type="button">Quản lý</button></div></div>
      {role === "resident" ? <div className="ticket-grid"><article className="workspace-panel ticket-form-panel"><div className="panel-heading"><div><p className="panel-kicker">Resident verification</p><h3>Kiểm tra thông tin ticket</h3></div><span className={`status-label ${status === "Approved" ? "status-label-success" : ""}`}>{status}</span></div><div className="prefill-note">Agent đã điền sẵn từ tin nhắn Zalo. Bạn hãy kiểm tra lại trước khi submit.</div><div className="ticket-form"><label>Cư dân<input value={draft.resident} onChange={(event) => update("resident", event.target.value)} /></label><label>Căn hộ<input value={draft.unit} onChange={(event) => update("unit", event.target.value)} /></label><label>Nhóm vấn đề<select value={draft.category} onChange={(event) => update("category", event.target.value)}>{ticketCategories.map((category) => <option key={category}>{category}</option>)}</select></label><label>Priority<select value={draft.priority} onChange={(event) => update("priority", event.target.value)}><option>Cao</option><option>Trung bình</option><option>Thấp</option></select></label><label>Vị trí<input value={draft.location} onChange={(event) => update("location", event.target.value)} /></label><label className="field-wide">Mô tả vấn đề<textarea value={draft.description} onChange={(event) => update("description", event.target.value)} rows={4} /></label></div><div className="ticket-form-actions"><button className="button-light" onClick={() => navigate("zalo")} type="button">Quay lại Zalo</button><button className="button-dark" disabled={status === "Submitted" || status === "Approved"} onClick={submit} type="button">{status === "Draft" ? "Submit ticket" : `Đã ${status.toLowerCase()}`} <ArrowRight className="inline h-4 w-4" /></button></div></article><aside className="workspace-panel ticket-context-panel"><p className="panel-kicker">Agent context</p><h3>Vì sao ticket này được tạo?</h3><div className="context-quote">“{draft.description || "Tin nhắn mô tả vấn đề sẽ xuất hiện ở đây."}”</div><div className="context-row"><span>Nguồn</span><strong>{draft.source}</strong></div><div className="context-row"><span>Agent rule</span><strong>Keyword match</strong></div><div className="context-row"><span>Cam kết</span><strong>Chưa tạo ticket trước khi duyệt</strong></div></aside></div> : <div className="management-ticket-layout"><article className="workspace-panel management-queue-panel"><div className="panel-heading"><div><p className="panel-kicker">Management console</p><h3>Approval queue</h3></div><span className="queue-count">1 pending</span></div><div className="queue-ticket queue-ticket-active"><div><span className="status-label">{status === "Draft" ? "Pending approval" : status}</span><h4>{draft.category}</h4><p>{draft.resident} · {draft.unit}</p><small>{draft.description}</small></div><ArrowRight className="h-4 w-4" /></div><div className="queue-ticket"><div><span className="status-label status-label-success">Approved</span><h4>Đăng ký thẻ cư dân</h4><p>Trần Hải · B-0812</p></div><span className="text-xs text-[#191919]/45">Hôm qua</span></div></article><article className="workspace-panel approval-detail-panel"><p className="panel-kicker">Selected request</p><h3>Review before ticket creation</h3><dl className="approval-details"><div><dt>Resident</dt><dd>{draft.resident} · {draft.unit}</dd></div><div><dt>Classification</dt><dd>{draft.category} · Priority {draft.priority}</dd></div><div><dt>Source</dt><dd>{draft.source}</dd></div><div><dt>Description</dt><dd>{draft.description}</dd></div></dl><div className="approval-audit"><span>HITL gate</span><strong>Ticket chưa được tạo</strong><small>Approval action sẽ được lưu vào audit trail.</small></div><div className="approval-actions"><button className="button-light" onClick={() => setRole("resident")} type="button">Request edit</button><button className="button-dark" disabled={status === "Approved"} onClick={approve} type="button">{status === "Approved" ? "Approved" : "Approve & create"} <ArrowRight className="inline h-4 w-4" /></button></div></article></div>}
    </section>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState<DemoTab>(() => {
    const hash = window.location.hash.slice(1) as DemoTab;
    return tabLabels.some(([tab]) => tab === hash) ? hash : "landing";
  });
  const [completedSteps, setCompletedSteps] = useState<string[]>(["welcome"]);
  const [activeStep, setActiveStep] = useState(0);
  const [onboardingChatDraft, setOnboardingChatDraft] = useState("");
  const [zaloMessagesState, setZaloMessagesState] = useState<ZaloMessage[]>(zaloMessages);
  const [zaloDraft, setZaloDraft] = useState("");
  const [detectedIssue, setDetectedIssue] = useState<DetectedIssue | null>(null);
  const [ticketRole, setTicketRole] = useState<TicketRole>("resident");
  const [ticketStatus, setTicketStatus] = useState<TicketStatus>("Draft");
  const [ticketDraft, setTicketDraft] = useState<TicketDraft>({ resident: resident.name, unit: resident.unit, category: "Cấp thoát nước", priority: "Cao", location: "Căn A-1204 · Khu vực bếp", description: "", source: "Zalo group · Rule-based agent" });

  useEffect(() => {
    const syncFromHash = () => {
      const hash = window.location.hash.slice(1) as DemoTab;
      if (tabLabels.some(([tab]) => tab === hash)) setActiveTab(hash);
    };
    window.addEventListener("hashchange", syncFromHash);
    return () => window.removeEventListener("hashchange", syncFromHash);
  }, []);

  const navigate = (tab: DemoTab) => {
    setActiveTab(tab);
    window.history.replaceState(null, "", `#${tab}`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const toggleStep = (id: string) => setCompletedSteps((current) => current.includes(id) ? current.filter((step) => step !== id) : [...current, id]);
  const sendOnboardingChat = () => setOnboardingChatDraft("");
  const sendZaloMessage = () => {
    const text = zaloDraft.trim();
    if (!text) return;
    setZaloMessagesState((current) => [...current, { id: Date.now(), sender: "Cư dân", text, time: "Vừa xong", important: Boolean(detectIssue(text)), issueType: detectIssue(text)?.category }]);
    const issue = detectIssue(text);
    setZaloDraft("");
    if (issue) setDetectedIssue(issue);
  };
  const createTicketFromIssue = () => {
    if (!detectedIssue) return;
    setTicketDraft((current) => ({ ...current, category: detectedIssue.category, description: detectedIssue.sourceText, priority: detectedIssue.category.includes("An toàn") ? "Cao" : "Trung bình", source: "Demo Zalo chat · Agent keyword detection" }));
    setDetectedIssue(null);
    navigate("ticket");
  };

  const content = useMemo(() => {
    if (activeTab === "onboarding") return <OnboardingView completedSteps={completedSteps} activeStep={activeStep} setActiveStep={setActiveStep} toggleStep={toggleStep} chatDraft={onboardingChatDraft} setChatDraft={setOnboardingChatDraft} sendChat={sendOnboardingChat} navigate={navigate} />;
    if (activeTab === "zalo") return <ZaloView messages={zaloMessagesState} draft={zaloDraft} setDraft={setZaloDraft} sendMessage={sendZaloMessage} detectedIssue={detectedIssue} dismissIssue={() => setDetectedIssue(null)} createTicket={createTicketFromIssue} navigate={navigate} />;
    if (activeTab === "ticket") return <TicketView role={ticketRole} setRole={setTicketRole} draft={ticketDraft} setDraft={setTicketDraft} status={ticketStatus} submit={() => setTicketStatus("Submitted")} approve={() => setTicketStatus("Approved")} navigate={navigate} />;
    return <LandingView navigate={navigate} />;
  }, [activeTab, activeStep, completedSteps, detectedIssue, onboardingChatDraft, ticketDraft, ticketRole, ticketStatus, zaloDraft, zaloMessagesState]);

  return <main className="min-h-screen overflow-x-hidden bg-white text-[#191919]"><AppNav activeTab={activeTab} navigate={navigate} />{content}</main>;
}
