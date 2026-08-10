import { useMemo, useState } from "react";
import { handbookAnswers, messages as initialMessages, resident, steps, type Message } from "./data";
import { classifyMessage, createTicketPrefill } from "./rules.js";
import { contactResident, createDraft, queryAgent, submitDraft, updateTicket } from "./api";

type Role = "resident" | "manager";
type ResidentTab = "home" | "onboarding" | "zalo" | "ticket" | "profile";
type ManagerTab = "home" | "queue" | "residents" | "tickets";
type TicketStatus = "DRAFT" | "SUBMITTED" | "APPROVED" | "IN_PROGRESS" | "RESOLVED" | "REJECTED";
type Ticket = { id?: string; ticketId?: string; title: string; category: string; priority: string; location: string; description: string; sourceMessageId: string; status: TicketStatus; rejectionReason?: string; resolutionNote?: string };

const icon = (name: string) => <span className="icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">{name === "chat" && <><path d="M5 5.5h14v10H9l-4 3v-13Z"/><path d="M8 9h8M8 12h5"/></>}{name === "ticket" && <><path d="M5 4.5h14v15H5z"/><path d="M8 9h8M8 13h6"/></>}{name === "check" && <><circle cx="12" cy="12" r="7.5"/><path d="m8.5 12 2.2 2.2 4.8-5"/></>}{name === "people" && <><circle cx="10" cy="9" r="3"/><path d="M4.5 19c.6-3.2 2.6-5 5.5-5s4.9 1.8 5.5 5M16 7c2.1 0 3.5 1.4 3.5 3.2"/></>}</svg></span>;

function App() {
  const [role, setRole] = useState<Role>("resident");
  const [tab, setTab] = useState<ResidentTab | ManagerTab>("home");
  const [completed, setCompleted] = useState(["01", "02", "03"]);
  const [zaloMessages, setZaloMessages] = useState<Message[]>(initialMessages);
  const [zaloDraft, setZaloDraft] = useState("");
  const [assistantDraft, setAssistantDraft] = useState("");
  const [assistantReply, setAssistantReply] = useState("Mình có thể hướng dẫn từng bước, hoặc trả lời về tiện ích và quy định tòa nhà.");
  const [candidate, setCandidate] = useState<Message | null>(null);
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [managerNote, setManagerNote] = useState("");

  const progress = Math.round((completed.length / steps.length) * 100);
  const currentTab = role === "resident" ? tab as ResidentTab : tab as ManagerTab;
  const issueCount = useMemo(() => zaloMessages.filter((message) => classifyMessage(message, resident.id).kind === "actionable").length, [zaloMessages]);

  const switchRole = (next: Role) => { setRole(next); setTab("home"); }
;
  const go = (next: ResidentTab | ManagerTab) => setTab(next);

  const askAssistant = async () => {
    const query = assistantDraft.toLowerCase();
    const answer = query.includes("hồ bơi") || query.includes("pool") ? handbookAnswers.pool : query.includes("đỗ") || query.includes("xe") ? handbookAnswers.parking : handbookAnswers.default;
    try {
      const result = await queryAgent(assistantDraft, "resident");
      setAssistantReply(`${result.answer} — ${result.citation ?? "OnBxrd demo"}`);
      if (result.notification?.kind === "ticket_draft_available") setCandidate({ id: "assistant-message", sender: "Nguyễn Minh · 12B", senderId: resident.id, time: "Now", text: assistantDraft });
    } catch {
      setAssistantReply(`${answer.answer} — ${answer.source}`);
    }
    setAssistantDraft("");
  };

  const sendZalo = async () => {
    const text = zaloDraft.trim();
    if (!text) return;
    const message = { id: `zalo-local-${Date.now()}`, sender: "Nguyễn Minh · 12B", senderId: resident.id, time: "Now", text };
    setZaloMessages((items) => [...items, message]);
    setZaloDraft("");
    try {
      const result = await queryAgent(text, "resident");
      if (result.notification?.kind === "ticket_draft_available") setCandidate(message);
    } catch {
      if (classifyMessage(message, resident.id).kind === "actionable") setCandidate(message);
    }
  };

  const openDraft = async (message: Message) => {
    const prefill = createTicketPrefill(message, classifyMessage(message, resident.id));
    if (!prefill) return;
    try {
      const draft = await createDraft(message.text);
      setTicket({ ...draft, sourceMessageId: message.id, status: "DRAFT" });
    } catch {
      setTicket({ ...prefill, status: "DRAFT" });
    }
    setCandidate(null);
    go("ticket");
  };

  const submit = async () => {
    if (!ticket) return;
    try {
      const result = ticket.id ? await submitDraft(ticket.id) : null;
      setTicket({ ...ticket, ...(result?.ticket ?? {}), ticketId: result?.ticket?.id, sourceMessageId: ticket.sourceMessageId, status: "SUBMITTED" });
    } catch {
      setTicket({ ...ticket, status: "SUBMITTED" });
    }
  };
  const managerAction = async (status: TicketStatus) => {
    if (!ticket) return;
    if (status === "REJECTED" && !managerNote.trim()) return;
    if (status === "RESOLVED" && !managerNote.trim()) return;
    try {
      const updated = ticket.ticketId ? await updateTicket(ticket.ticketId, status, managerNote) : null;
      setTicket({ ...ticket, ...(updated ?? {}), ticketId: ticket.ticketId, sourceMessageId: ticket.sourceMessageId, status, ...(status === "REJECTED" ? { rejectionReason: managerNote } : {}), ...(status === "RESOLVED" ? { resolutionNote: managerNote } : {}) });
    } catch {
      setTicket({ ...ticket, status, ...(status === "REJECTED" ? { rejectionReason: managerNote } : {}), ...(status === "RESOLVED" ? { resolutionNote: managerNote } : {}) });
    }
    setManagerNote("");
  };

  const nav = role === "resident"
    ? [["home", "Home", "people"], ["onboarding", "Onboarding", "check"], ["zalo", "Zalo agent", "chat"], ["ticket", "My tickets", "ticket"]] as const
    : [["home", "Overview", "people"], ["residents", "Residents", "people"], ["tickets", "Ticket management", "check"]] as const;

  return <div className="app">
    <header className="topbar">
      <button className="brand" onClick={() => go(role === "resident" ? "onboarding" : "tickets")}><span className="brand-mark">O</span><span>OnBxrd</span></button>
      <div className="role-switch" role="tablist" aria-label="Demo role">
        <button onClick={() => switchRole("resident")} className={role === "resident" ? "active" : ""} aria-selected={role === "resident"}>Resident</button>
        <button onClick={() => switchRole("manager")} className={role === "manager" ? "active" : ""} aria-selected={role === "manager"}>Manager</button>
      </div>
      <button className="user-chip" onClick={() => role === "resident" && go("profile")} aria-label="Open user profile"><span>{role === "resident" ? "NM" : "PM"}</span><small>{role === "resident" ? "Nguyễn Minh" : "Property team"}</small></button>
    </header>
    <aside className="rail">
      <div className="rail-label">{role === "resident" ? "YOUR HOME" : "OPERATIONS"}</div>
      {nav.map(([id, label, glyph]) => <button key={id} className={currentTab === id ? "rail-item selected" : "rail-item"} onClick={() => go(id)}>{icon(glyph)}<span>{label}</span></button>)}
      <div className="rail-foot"><span className="live-dot" /> Demo mode<br /><small>All Zalo activity is simulated</small></div>
    </aside>
    <main className="workspace">
      {currentTab === "home" && <Home role={role} progress={progress} ticket={ticket} go={go} />}
      {role === "resident" && currentTab === "onboarding" && <Onboarding progress={progress} completed={completed} setCompleted={setCompleted} draft={assistantDraft} setDraft={setAssistantDraft} reply={assistantReply} ask={askAssistant} />}
      {role === "resident" && currentTab === "zalo" && <Zalo messages={zaloMessages} draft={zaloDraft} setDraft={setZaloDraft} send={sendZalo} issueCount={issueCount} />}
      {role === "resident" && currentTab === "ticket" && <TicketDraft ticket={ticket} setTicket={setTicket} submit={submit} goZalo={() => go("zalo")} />}
      {role === "resident" && currentTab === "profile" && <Profile progress={progress} />}
      {role === "manager" && currentTab === "residents" && <Residents progress={progress} />}
      {role === "manager" && currentTab === "tickets" && <TicketManagement ticket={ticket} action={managerAction} note={managerNote} setNote={setManagerNote} />}
    </main>
    {candidate && <section className="confirmation" role="dialog" aria-label="Possible support issue"><p className="eyebrow">Possible issue detected</p><h2>Có vẻ bạn đang báo một vấn đề cần xử lý.</h2><p>OnBxrd có thể mở bản nháp ticket với nội dung từ tin nhắn của bạn. Bạn luôn có thể chỉnh sửa trước khi gửi.</p><div><button className="button ghost" onClick={() => setCandidate(null)}>Not now</button><button className="button primary" onClick={() => openDraft(candidate)}>Review ticket draft →</button></div></section>}
  </div>;
}

function Home({ role, progress, ticket, go }: { role: Role; progress: number; ticket: Ticket | null; go: (tab: ResidentTab | ManagerTab) => void }) {
  const residentHome = role === "resident";
  return <section className="home-scene">
    <div className="home-hero">
      <div className="home-copy"><span className="home-kicker">{residentHome ? "Your building, in one calm place" : "Building operations, in one clear view"}</span><h1>{residentHome ? "Your move-in, made visible." : "Signals become accountable action."}</h1><p>{residentHome ? "OnBxrd brings onboarding, building knowledge, support, and ticket updates into one resident journey." : "OnBxrd gives management the context to act on resident needs without losing the conversation that created them."}</p><div className="home-actions"><button className="button primary" onClick={() => go(residentHome ? "onboarding" : "tickets")}>{residentHome ? "Continue onboarding" : "Open ticket management"} →</button><button className="button ghost" onClick={() => go(residentHome ? "zalo" : "tickets")}>{residentHome ? "Explore Zalo signals" : "Review all tickets"}</button></div></div>
      <div className="home-orbit" aria-hidden="true"><span className="orbit-core">O</span><span className="orbit-node n1">ONBOARD</span><span className="orbit-node n2">SIGNAL</span><span className="orbit-node n3">TICKET</span><i className="orbit-ring r1"/><i className="orbit-ring r2"/></div>
    </div>
    <div className="home-command-grid">
      <article className="command-card resident-card"><span>Resident status</span><strong>{residentHome ? "Settling in" : "Operations live"}</strong><p>{residentHome ? `${progress}% of your six onboarding steps are complete.` : "One resident-confirmed issue is ready for a decision."}</p><div className="command-progress"><i style={{ transform: `scaleX(${residentHome ? progress / 100 : 0.72})` }} /></div></article>
      <article className="command-card signal-card"><span>Live signal layer</span><strong>30 + 815 messages</strong><p>Noise is condensed. Building notices and a verified kitchen leak remain actionable.</p><button onClick={() => go(residentHome ? "zalo" : "tickets")}>Inspect signal evidence →</button></article>
      <article className="command-card ticket-card"><span>Current ticket</span><strong>{ticket ? ticket.status.replace("_", " ") : "No ticket submitted"}</strong><p>{ticket ? ticket.title : "A rule-based draft appears only after an explicit resident confirmation."}</p><button onClick={() => go(residentHome ? "ticket" : "tickets")}>Open ticket workspace →</button></article>
    </div>
    <section className="home-flow"><span>01</span><div><strong>Guided onboarding</strong><p>Progress knows what comes next, and questions answer from building material.</p></div><span>02</span><div><strong>Signal with restraint</strong><p>Group noise stays in the group; a support issue becomes an editable draft.</p></div><span>03</span><div><strong>Human-owned resolution</strong><p>Residents confirm. Managers respond, approve, resolve, and leave a visible record.</p></div></section>
  </section>;
}

function Profile({ progress }: { progress: number }) {
  return <section className="scene profile-scene"><div className="profile-hero"><div className="profile-avatar">NM</div><div><h1>Nguyễn Minh</h1><p>Resident · River Residence · Tower A / Unit 12B</p></div><span className="status approved">Verified resident</span></div><div className="profile-grid"><article><h2>Home profile</h2><dl><div><dt>Phone</dt><dd>+84 90 123 4567</dd></div><div><dt>Email</dt><dd>minh.nguyen@example.com</dd></div><div><dt>Resident type</dt><dd>Owner</dd></div><div><dt>Emergency contact</dt><dd>Ngọc Anh · +84 91 456 7890</dd></div></dl></article><article><h2>Preferences & consent</h2><div className="preference"><strong>OnBxrd notifications</strong><span>In-app enabled</span></div><div className="preference"><strong>Zalo link</strong><span>Linked · ID protected</span></div><div className="preference"><strong>Group processing consent</strong><span>Confirmed for demo</span></div></article><article className="profile-progress"><h2>Onboarding position</h2><strong>{progress}%</strong><p>{Math.round(progress / 100 * 6)} of 6 steps completed. Your next suggested action is utility setup.</p><button className="button primary">Manage profile</button></article></div></section>;
}

function Onboarding({ progress, completed, setCompleted, draft, setDraft, reply, ask }: { progress: number; completed: string[]; setCompleted: (value: string[]) => void; draft: string; setDraft: (value: string) => void; reply: string; ask: () => void }) {
  const toggle = (id: string) => setCompleted(completed.includes(id) ? completed.filter((item) => item !== id) : [...completed, id]);
  return <section className="scene onboarding-scene"><div className="scene-heading"><div><p className="eyebrow">Resident onboarding agent</p><h1>Settle in with a clear next step.</h1><p>Personal guidance, source-grounded answers, and a simple checklist for your first week at home.</p></div><div className="progress-stamp"><strong>{progress}%</strong><span>complete</span></div></div><div className="onboard-grid"><article className="ledger"><div className="ledger-head"><h2>Your move-in path</h2><span>{completed.length}/6 steps</span></div><div className="progress-line"><span style={{ width: `${progress}%` }} /></div>{steps.map(([id, title, detail, done]) => <button className={completed.includes(id) ? "step done" : "step"} key={id} onClick={() => toggle(id)}><b>{completed.includes(id) ? "✓" : id}</b><span><strong>{title}</strong><small>{detail}</small></span><em>{completed.includes(id) ? "Done" : done ? "Ready" : "Next"}</em></button>)}</article><article className="agent-panel"><p className="eyebrow">Ask your OnBxrd assistant</p><h2>What can I help with?</h2><div className="agent-message">{reply}</div><div className="suggestions"><button onClick={() => { setDraft("Hồ bơi mở cửa lúc mấy giờ?"); }
}>Pool hours</button><button onClick={() => { setDraft("Khách đỗ xe qua đêm thế nào?"); }
}>Guest parking</button></div><div className="composer"><input aria-label="Ask a building question" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => event.key === "Enter" && ask()} placeholder="Ask about your building…" /><button onClick={ask} aria-label="Send question">→</button></div><p className="source-note">Answers stay inside the demo handbook and cite a source when available.</p></article></div></section>;
}

function Zalo({ messages, draft, setDraft, send, issueCount }: { messages: Message[]; draft: string; setDraft: (value: string) => void; send: () => void; issueCount: number }) {
  return <section className="scene zalo-scene"><div className="scene-heading"><div><p className="eyebrow">Zalo signal agent · simulated</p><h1>A crowded chat, a clear signal.</h1><p>OnBxrd separates support-worthy reports from everyday group conversation before it asks a resident to create a ticket.</p></div><div className="backlog"><strong>+815</strong><span>new messages<br />outside this demo window</span></div></div><div className="signal-layout"><article className="message-case"><div className="group-head"><div><span className="zalo-dot">z</span><div><h2>River Residence · Residents</h2><small>30 messages replayed · Demo only</small></div></div><span className="online">1,482 members</span></div><div className="message-stream">{messages.map((message) => <div className={message.senderId === resident.id ? "message mine" : "message"} key={message.id}><div><b>{message.sender}</b><time>{message.time}</time></div><p>{message.text}</p></div>)}</div><div className="composer"><input aria-label="Send a simulated Zalo message" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => event.key === "Enter" && send()} placeholder="Try an issue report, or chat normally…" /><button onClick={send} aria-label="Send message">→</button></div></article><aside className="signal-brief"><p className="eyebrow">Agent digest</p><h2>10:00 — 10:01</h2><div className="signal-block urgent"><span>Needs confirmation</span><strong>{issueCount ? "Water leak · Unit 12B" : "No new support request"}</strong><p>Resident report in the kitchen. OnBxrd will ask Nguyễn Minh before creating any ticket.</p></div><div className="signal-block"><span>Building notice</span><strong>Fire drill · Tomorrow 10:00</strong><p>Management announcement retained for resident awareness.</p></div><div className="signal-block muted"><span>Noise removed</span><strong>25 chat or community messages</strong><p>Questions, acknowledgements, pet-rule concerns and a neighbour-noise dispute stay out of ticket creation.</p></div><div className="rule-card"><b>Rule-based demo</b><p>Actionable + sender match + no resolved language → ticket draft.</p></div></aside></div></section>;
}

function TicketDraft({ ticket, setTicket, submit, goZalo }: { ticket: Ticket | null; setTicket: (ticket: Ticket) => void; submit: () => void; goZalo: () => void }) {
  if (!ticket) return <EmptyTicket goZalo={goZalo} />;
  const edit = (field: keyof Ticket, value: string) => setTicket({ ...ticket, [field]: value });
  return <section className="scene ticket-scene"><div className="scene-heading"><div><p className="eyebrow">Resident ticket review</p><h1>Review before it becomes a request.</h1><p>This is a draft only. You control the information and submit it explicitly.</p></div><span className={`status ${ticket.status.toLowerCase()}`}>{ticket.status.replace("_", " ")}</span></div><div className="ticket-layout"><form className="ticket-form" onSubmit={(event) => { event.preventDefault(); submit(); }
}><div className="source-strip">Source: simulated Zalo message {ticket.sourceMessageId} · Rule match: plumbing incident</div><label>Title<input value={ticket.title} onChange={(event) => edit("title", event.target.value)} /></label><div className="split"><label>Category<select value={ticket.category} onChange={(event) => edit("category", event.target.value)}><option>Plumbing</option><option>Electrical</option><option>Access</option></select></label><label>Priority<select value={ticket.priority} onChange={(event) => edit("priority", event.target.value)}><option>High</option><option>Medium</option><option>Low</option></select></label></div><label>Location<input value={ticket.location} onChange={(event) => edit("location", event.target.value)} /></label><label>Description<textarea rows={5} value={ticket.description} onChange={(event) => edit("description", event.target.value)} /></label><div className="form-actions"><button type="button" className="button ghost" onClick={goZalo}>Back to Zalo</button><button className="button primary" disabled={ticket.status !== "DRAFT"}>{ticket.status === "DRAFT" ? "Submit request →" : "Submitted for management review"}</button></div></form><Timeline ticket={ticket} /></div></section>;
}

function EmptyTicket({ goZalo }: { goZalo: () => void }) { return <section className="empty"><p className="eyebrow">No draft open</p><h1>Your next support request will appear here.</h1><p>Use the simulated Zalo agent to detect an issue, or send a message such as “Nước đang rò dưới bồn rửa bếp căn 12B.”</p><button className="button primary" onClick={goZalo}>Open Zalo agent →</button></section>; }

function Timeline({ ticket }: { ticket: Ticket }) { const stages: TicketStatus[] = ["DRAFT", "SUBMITTED", "APPROVED", "IN_PROGRESS", "RESOLVED"]; const active = stages.indexOf(ticket.status); return <aside className="timeline"><p className="eyebrow">Visible history</p><h2>Request lifecycle</h2>{stages.map((stage, index) => <div className={index <= active ? "timeline-step complete" : "timeline-step"} key={stage}><i /> <span><strong>{stage.replace("_", " ")}</strong><small>{index === active ? "Current stage" : "Awaiting next action"}</small></span></div>)}{ticket.rejectionReason && <div className="timeline-note">Rejected: {ticket.rejectionReason}</div>}{ticket.resolutionNote && <div className="timeline-note">Resolution: {ticket.resolutionNote}</div>}</aside>; }


function Queue({ ticket, action, note, setNote }: { ticket: Ticket | null; action: (status: TicketStatus) => void; note: string; setNote: (value: string) => void }) { return <section className="scene manager-scene"><div className="scene-heading"><div><p className="eyebrow">Manager · approval queue</p><h1>Every commitment has an owner.</h1><p>Review resident-submitted requests, keep the decision visible, and move work through a documented lifecycle.</p></div><div className="queue-count"><strong>{ticket?.status === "SUBMITTED" ? "1" : "0"}</strong><span>awaiting approval</span></div></div><div className="manager-grid"><article className="queue"><div className="queue-summary"><span>Submitted today</span><strong>04</strong><span>High priority</span><strong>01</strong></div><button className={ticket?.status === "SUBMITTED" ? "queue-row selected" : "queue-row"}><span className="channel">Zalo demo</span><strong>{ticket?.title ?? "No submitted ticket"}</strong><small>{ticket ? `${resident.name} · ${resident.unit} · ${ticket.priority}` : "A resident-confirmed draft appears here."}</small></button><button className="queue-row"><span className="channel app">App</span><strong>Activate electricity meter</strong><small>Trần Hạnh · Unit 08A · Medium</small></button></article><ManagerDetail ticket={ticket} action={action} note={note} setNote={setNote} /></div></section>; }

function ManagerDetail({ ticket, action, note, setNote }: { ticket: Ticket | null; action: (status: TicketStatus) => void; note: string; setNote: (value: string) => void }) {
  const [responseStatus, setResponseStatus] = useState("");
  if (!ticket) return <aside className="manager-detail empty-detail"><h2>Select a submitted request</h2><p>Demo ticket actions will become available after the resident confirms a draft.</p></aside>;
  const actionable = ticket.status === "SUBMITTED" || ticket.status === "APPROVED" || ticket.status === "IN_PROGRESS";
  const sendResponse = async (kind: "contact" | "clarify") => {
    if (kind === "contact" && ticket.ticketId) {
      try {
        const result = await contactResident(ticket.ticketId);
        setResponseStatus(result.message);
      } catch {
        setResponseStatus("Contact attempt recorded — Zalo demo fallback: in-app notification sent.");
      }
    } else {
      setResponseStatus("Clarification request queued for Nguyễn Minh in the demo inbox.");
    }
    setNote("");
  };
  return <aside className="manager-detail">
    <span className={`status ${ticket.status.toLowerCase()}`}>{ticket.status.replace("_", " ")}</span>
    <h2>{ticket.title}</h2>
    <div className="manager-context"><strong>High priority · Plumbing</strong><span>Submitted 10:02 · Simulated Zalo source</span></div>
    <dl>
      <div><dt>Resident</dt><dd>{resident.name} · Unit {resident.unit} · Tower A, floor 12</dd></div>
      <div><dt>Contact preference</dt><dd>In-app notification, then Zalo OA when permitted</dd></div>
      <div><dt>Location</dt><dd>{ticket.location}</dd></div>
      <div><dt>Source evidence</dt><dd>“{ticket.description}”</dd></div>
      <div><dt>Detection note</dt><dd>Resident sender match · plumbing rule · no resolved language</dd></div>
    </dl>
    <div className="activity-log"><strong>Activity</strong><span>10:01 · Issue reported in demo group</span><span>10:02 · Resident reviewed and submitted ticket</span></div>
    {actionable && <>
      <label className="manager-note">Manager response / operational note<textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder={ticket.status === "SUBMITTED" ? "Add a clarification, rejection reason, or approval note…" : "A resolution note is required before closing…"} /></label>
      <div className="response-actions"><button className="button ghost" onClick={() => sendResponse("contact")}>Contact resident</button><button className="button ghost" onClick={() => sendResponse("clarify")}>Request clarification</button></div>
      <div className="manager-actions">{ticket.status === "SUBMITTED" && <><button className="button ghost danger" onClick={() => action("REJECTED")}>Reject with reason</button><button className="button primary" onClick={() => action("APPROVED")}>Approve ticket</button></>}{ticket.status === "APPROVED" && <button className="button primary" onClick={() => action("IN_PROGRESS")}>Move to in progress</button>}{ticket.status === "IN_PROGRESS" && <button className="button primary" onClick={() => action("RESOLVED")}>Resolve with note</button>}</div>
    </>}
    {responseStatus && <p className="response-status" role="status">{responseStatus}</p>}
  </aside>;
}

function Residents({ progress }: { progress: number }) { return <section className="scene manager-scene"><div className="scene-heading"><div><p className="eyebrow">Manager · residents</p><h1>See who needs a helpful nudge.</h1><p>Progress is visible without requiring a resident to repeat their onboarding state.</p></div></div><div className="resident-list"><div className="resident-row"><b>Nguyễn Minh</b><span>12B</span><div><i style={{ width: `${progress}%` }} /></div><em>{progress}% · on track</em></div><div className="resident-row"><b>Trần Hạnh</b><span>08A</span><div><i style={{ width: "67%" }} /></div><em>67% · on track</em></div><div className="resident-row"><b>Lê Anh</b><span>21C</span><div><i style={{ width: "33%" }} /></div><em>33% · needs attention</em></div></div></section>; }

function TicketManagement({ ticket, action, note, setNote }: { ticket: Ticket | null; action: (status: TicketStatus) => void; note: string; setNote: (value: string) => void }) { return <section className="scene manager-scene"><div className="scene-heading"><div><p className="eyebrow">Manager · ticket management</p><h1>One place for request history.</h1><p>Filter-ready visual inventory for this local demo. Every change remains visible to the resident.</p></div></div><div className="ticket-management"><div className="table-head"><span>Request</span><span>Source</span><span>Priority</span><span>Status</span></div><div className="table-row"><b>{ticket?.title ?? "Water leak under kitchen sink"}</b><span>Zalo demo</span><span className="priority">High</span><span className={`status ${ticket?.status.toLowerCase() ?? "draft"}`}>{ticket?.status.replace("_", " ") ?? "DRAFT"}</span></div><div className="table-row"><b>Activate electricity meter</b><span>App</span><span>Medium</span><span className="status approved">APPROVED</span></div></div>{ticket && <ManagerDetail ticket={ticket} action={action} note={note} setNote={setNote} />}</section>; }


export default App;
