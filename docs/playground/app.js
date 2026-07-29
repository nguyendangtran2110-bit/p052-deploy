// Main Application Logic for EduHub Playground Demo (MD3 Multi-Course Dashboard & Reader)
document.addEventListener("DOMContentLoaded", () => {
  const data = window.EduHubData;
  const llm = window.MockLLM;

  // App State
  let activeRole = "STUDENT";
  let activeTab = "hub";
  let selectedDocIds = new Set();
  
  let filters = {
    school: "ALL",
    docType: "ALL",
    visibility: "ALL",
    search: ""
  };

  // Active Viewer Document & Path State
  let activeViewerDoc = null;
  let activeDetailPath = null;
  let docChatHistory = [];

  let globalChatHistory = [
    {
      id: "msg-welcome",
      sender: "ASSISTANT",
      text: "👋 Chào bạn! Tôi là Academic Assistant của EduHub. Hãy đặt câu hỏi về các môn học (như Tín hiệu & Hệ thống, Triết học, Vật lý...). Mọi câu trả lời của tôi đều được trích dẫn trực tiếp từ tài liệu nội bộ đã duyệt mà bạn có quyền truy cập.",
      citations: [],
      grounded_status: "GROUNDED"
    }
  ];

  // DOM Elements
  const roleSelect = document.getElementById("role-select");
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabSections = document.querySelectorAll(".tab-section");
  const tabBtnManagement = document.getElementById("tab-btn-management");

  const schoolFilterList = document.getElementById("school-filter-list");
  const docTypeFilterItems = document.querySelectorAll("#doctype-filter-list .filter-item");
  const visibilityFilterItems = document.querySelectorAll("#visibility-filter-list .filter-item");
  
  const globalSearchInput = document.getElementById("global-search-input");
  const btnGlobalSearch = document.getElementById("btn-global-search");

  const docCardsGrid = document.getElementById("doc-cards-grid");
  const selectedCountEl = document.getElementById("selected-count");
  const btnBatchSummary = document.getElementById("btn-batch-summary");
  const btnBatchCompare = document.getElementById("btn-batch-compare");

  // Modals
  const modalUpload = document.getElementById("modal-upload");
  const btnOpenUpload = document.getElementById("btn-open-upload");
  const btnCloseUpload = document.getElementById("btn-close-upload");
  const formUpload = document.getElementById("form-upload");
  const lecturerUploadOptions = document.getElementById("lecturer-upload-options");
  const uploadNoticeBanner = document.getElementById("upload-notice-banner");

  // Split Viewer Modal
  const modalDocDetails = document.getElementById("modal-doc-details");
  const btnCloseDetails = document.getElementById("btn-close-details");
  const viewerLeftScrollCol = document.getElementById("viewer-left-scroll-col");
  const docMetaHeader = document.getElementById("doc-meta-header");
  const docMetaTableContainer = document.getElementById("doc-meta-table-container");
  const btnDownloadFileLeft = document.getElementById("btn-download-file-left");
  const downloadFilenameSpan = document.getElementById("download-filename-span");
  
  const inlinePageIndicator = document.getElementById("inline-page-indicator");
  const inlineReaderStackedPages = document.getElementById("inline-reader-stacked-pages");

  const docAiOverviewBox = document.getElementById("doc-ai-overview-box");
  const docChatMessagesContainer = document.getElementById("doc-chat-messages-container");
  const docChatInput = document.getElementById("doc-chat-input");
  const btnDocSendChat = document.getElementById("btn-doc-send-chat");

  const modalCitation = document.getElementById("modal-citation");
  const btnCloseCitation = document.getElementById("btn-close-citation");
  const citationBody = document.getElementById("citation-body");

  const modalBatchResult = document.getElementById("modal-batch-result");
  const btnCloseBatch = document.getElementById("btn-close-batch");
  const batchResultTitle = document.getElementById("batch-result-title");
  const batchResultBody = document.getElementById("batch-result-body");

  // Global Chat Elements
  const chatSubjectSelect = document.getElementById("chat-subject-select");
  const chatMessagesEl = document.getElementById("chat-messages");
  const chatInput = document.getElementById("chat-input");
  const btnSendChat = document.getElementById("btn-send-chat");

  // Multi-Course Dashboard Elements
  const pathSubjectSelect = document.getElementById("path-subject-select");
  const pathGoalInput = document.getElementById("path-goal-input");
  const pathDurationInput = document.getElementById("path-duration-input");
  const btnGeneratePath = document.getElementById("btn-generate-path");
  const learningPathsGrid = document.getElementById("learning-paths-grid");
  const userPathCountEl = document.getElementById("user-path-count");

  // Path Details Modal
  const modalPathDetails = document.getElementById("modal-path-details");
  const btnClosePathDetails = document.getElementById("btn-close-path-details");
  const pathModalTitle = document.getElementById("path-modal-title");
  const pathDetailsBody = document.getElementById("path-details-body");

  // Management Elements
  const pendingDocsList = document.getElementById("pending-docs-list");
  const privateDocsManagementList = document.getElementById("private-docs-management-list");

  // ==========================================
  // INITIALIZATION & EVENT LISTENERS
  // ==========================================

  function init() {
    renderSchoolFilters();
    populateSelects();
    renderDocumentGrid();
    renderGlobalChatMessages();
    renderLearningPathsDashboard();
    renderManagementTab();
    setupEventListeners();
  }

  function getCurrentUser() {
    return data.users.find(u => u.role === activeRole) || data.users[0];
  }

  function renderSchoolFilters() {
    schoolFilterList.innerHTML = data.schools.map(s => {
      const activeClass = filters.school === s.id ? "active" : "";
      return `<li class="filter-item ${activeClass}" data-school="${s.id}">
        <span>${s.name}</span>
      </li>`;
    }).join("");

    schoolFilterList.querySelectorAll(".filter-item").forEach(item => {
      item.addEventListener("click", () => {
        filters.school = item.dataset.school;
        renderSchoolFilters();
        renderDocumentGrid();
      });
    });
  }

  function populateSelects() {
    const subjOptions = data.subjects.map(s => `<option value="${s.id}">[${s.code}] ${s.name} (${s.school})</option>`).join("");
    chatSubjectSelect.innerHTML = `<option value="ALL">Tất cả môn học</option>` + subjOptions;
    pathSubjectSelect.innerHTML = subjOptions;

    const uploadSubjSelect = document.getElementById("upload-subject");
    if (uploadSubjSelect) uploadSubjSelect.innerHTML = subjOptions;
  }

  function handleRoleChange(newRole) {
    activeRole = newRole;
    data.currentUserRole = newRole;

    if (activeRole === "LECTURER") {
      tabBtnManagement.classList.remove("hidden");
      lecturerUploadOptions.classList.remove("hidden");
      uploadNoticeBanner.innerHTML = "⚡ Tài liệu do Giảng viên tải lên được mặc định phê duyệt (APPROVED) và bạn có thể chọn quyền Private.";
    } else {
      tabBtnManagement.classList.add("hidden");
      lecturerUploadOptions.classList.add("hidden");
      uploadNoticeBanner.innerHTML = "ℹ️ Tài liệu của Sinh viên sẽ được khởi tạo với trạng thái PENDING (Chờ duyệt).";
      if (activeTab === "management") switchTab("hub");
    }

    renderDocumentGrid();
    renderLearningPathsDashboard();
    renderManagementTab();
  }

  function switchTab(targetTab) {
    activeTab = targetTab;
    tabBtns.forEach(btn => {
      if (btn.dataset.tab === targetTab) btn.classList.add("active");
      else btn.classList.remove("active");
    });

    tabSections.forEach(sec => {
      if (sec.id === `tab-content-${targetTab}`) sec.classList.remove("hidden");
      else sec.classList.add("hidden");
    });
  }

  function setupEventListeners() {
    roleSelect.addEventListener("change", (e) => handleRoleChange(e.target.value));

    tabBtns.forEach(btn => {
      btn.addEventListener("click", () => switchTab(btn.dataset.tab));
    });

    docTypeFilterItems.forEach(item => {
      item.addEventListener("click", () => {
        docTypeFilterItems.forEach(i => i.classList.remove("active"));
        item.classList.add("active");
        filters.docType = item.dataset.type;
        renderDocumentGrid();
      });
    });

    visibilityFilterItems.forEach(item => {
      item.addEventListener("click", () => {
        visibilityFilterItems.forEach(i => i.classList.remove("active"));
        item.classList.add("active");
        filters.visibility = item.dataset.vis;
        renderDocumentGrid();
      });
    });

    btnGlobalSearch.addEventListener("click", () => {
      filters.search = globalSearchInput.value.trim().toLowerCase();
      renderDocumentGrid();
    });

    globalSearchInput.addEventListener("keyup", (e) => {
      if (e.key === "Enter") {
        filters.search = globalSearchInput.value.trim().toLowerCase();
        renderDocumentGrid();
      }
    });

    btnBatchSummary.addEventListener("click", handleBatchSummary);
    btnBatchCompare.addEventListener("click", handleBatchCompare);

    btnCloseUpload.addEventListener("click", () => modalUpload.classList.add("hidden"));
    btnCloseDetails.addEventListener("click", () => modalDocDetails.classList.add("hidden"));
    btnCloseCitation.addEventListener("click", () => modalCitation.classList.add("hidden"));
    btnCloseBatch.addEventListener("click", () => modalBatchResult.classList.add("hidden"));
    btnClosePathDetails.addEventListener("click", () => modalPathDetails.classList.add("hidden"));

    btnOpenUpload.addEventListener("click", () => modalUpload.classList.remove("hidden"));
    formUpload.addEventListener("submit", handleUploadSubmit);

    btnSendChat.addEventListener("click", handleSendGlobalChat);
    chatInput.addEventListener("keyup", (e) => {
      if (e.key === "Enter") handleSendGlobalChat();
    });

    btnGeneratePath.addEventListener("click", handleGeneratePath);

    // In-Context Document Q&A Send
    btnDocSendChat.addEventListener("click", handleSendDocChat);
    docChatInput.addEventListener("keyup", (e) => {
      if (e.key === "Enter") handleSendDocChat();
    });

    // Download File Button
    btnDownloadFileLeft.addEventListener("click", () => {
      if (activeViewerDoc) {
        alert(`📥 Đã khởi tạo tải tệp thành công: "${activeViewerDoc.file_url}".`);
      }
    });

    // Outer Left Column Scroll Listener
    viewerLeftScrollCol.addEventListener("scroll", handleOuterLeftColScroll);
  }

  // ==========================================
  // UNIFIED SCROLL DOCUMENT VIEWER LOGIC
  // ==========================================

  function openDocumentDetails(docId) {
    const doc = data.documents.find(d => d.id === docId);
    if (!doc) return;

    activeViewerDoc = doc;

    // 1. Render Left Column Metadata Header & Table
    docMetaHeader.innerHTML = `
      <div style="margin-bottom: 8px;">
        <span class="badge yellow">${doc.school}</span>
        <span class="badge blue">${doc.document_type}</span>
        <span class="badge ${doc.visibility === 'PUBLIC' ? 'green' : 'purple'}">${doc.visibility}</span>
        <span class="badge green">${doc.approval_status}</span>
      </div>
      <h2 style="font-size: 16px; font-weight: 800; color: #fff; margin-bottom: 4px; line-height: 1.3;">${doc.title}</h2>
      <p style="font-size: 12px; color: var(--md-sys-color-on-surface-variant);">${doc.description}</p>
    `;

    docMetaTableContainer.innerHTML = `
      <table class="neo-table">
        <tr><td><strong>Môn học:</strong></td><td>${doc.subject_name}</td></tr>
        <tr><td><strong>Người đăng:</strong></td><td>${doc.owner_name}</td></tr>
        <tr><td><strong>Học kỳ & Năm học:</strong></td><td>${doc.semester} (${doc.academic_year})</td></tr>
        <tr><td><strong>Số trang:</strong></td><td>${doc.pages} trang</td></tr>
        <tr><td><strong>Lượt tải / xem:</strong></td><td>${doc.downloads} lượt</td></tr>
      </table>
    `;

    downloadFilenameSpan.textContent = doc.file_url;

    // 2. Render Stacked Pages in outer flow
    renderContinuousPages();

    // 3. Render Right Column Top: Knowledge Hub Agent Overview
    const aiOverview = llm.generateDocumentOverview(doc.id);
    docAiOverviewBox.innerHTML = `
      <div style="font-size: 12px; font-weight: 800; color: var(--md-sys-color-primary); margin-bottom: 8px;">
        🤖 KNOWLEDGE HUB AGENT — TỔNG QUAN TÀI LIỆU
      </div>
      <p style="font-size: 12px; color: var(--md-sys-color-on-surface-variant); margin-bottom: 10px; line-height: 1.5;">${aiOverview.summary}</p>
      <div style="font-size: 11px; font-weight: 700; color: #a5b4fc; margin-bottom: 4px;">⚡ CÁC ĐIỂM KIẾN THỨC CỐT LÕI:</div>
      <ul style="padding-left: 14px; font-size: 11px; color: var(--md-sys-color-on-surface-variant); line-height: 1.5;">
        ${aiOverview.takeaways.map(t => `<li style="margin-bottom: 4px;">${t}</li>`).join("")}
      </ul>
    `;

    // 4. Render Right Column Bottom: Academic Assistant Document Q&A Chat
    docChatHistory = [
      {
        id: "msg-doc-welcome",
        sender: "ASSISTANT",
        text: `👋 Tôi là Academic Assistant. Bạn có câu hỏi nào về tài liệu **"${doc.title}"** không? Hãy nhập câu hỏi bên dưới!`,
        citations: []
      }
    ];

    renderDocChatMessages();

    modalDocDetails.classList.remove("hidden");
    viewerLeftScrollCol.scrollTop = 0;
    updatePageCounterIndicator(1);
  }

  function renderContinuousPages() {
    if (!activeViewerDoc) return;
    const user = getCurrentUser();
    const watermarkText = `EDUHUB • ${user.email} • UNIFIED READER`;

    const totalPages = Math.min(8, activeViewerDoc.pages || 5);
    let stackedPagesHTML = "";

    for (let p = 1; p <= totalPages; p++) {
      const chunk = (activeViewerDoc.chunks || []).find(c => c.page_number === p) || 
                    (activeViewerDoc.chunks && activeViewerDoc.chunks[0]);

      const pageContent = chunk ? chunk.content : 
        `Nội dung tài liệu "${activeViewerDoc.title}" (Trang ${p}). Phân tích chi tiết các định lý, công thức và bài tập vận dụng. Được phép bôi đen chọn văn bản và sao chép theo nhu cầu học tập.`;

      stackedPagesHTML += `
        <div class="gdrive-pdf-page-card" data-page="${p}">
          <div class="watermark-overlay">
            <div>${watermarkText}</div>
            <div>${watermarkText}</div>
          </div>
          <div class="gdrive-page-header">
            <span>📄 ${activeViewerDoc.title}</span>
            <span>Trang ${p} / ${totalPages}</span>
          </div>
          <div style="position: relative; z-index: 2; font-size: 14px; line-height: 1.8; color: #0f172a;">
            <p style="margin-bottom: 12px; font-weight: 700;">[Nội dung trang ${p}]:</p>
            <p>${pageContent}</p>
          </div>
        </div>
      `;
    }

    inlineReaderStackedPages.innerHTML = stackedPagesHTML;
  }

  function handleOuterLeftColScroll() {
    if (!activeViewerDoc) return;

    const pageCards = viewerLeftScrollCol.querySelectorAll(".gdrive-pdf-page-card");
    const containerTop = viewerLeftScrollCol.scrollTop;

    let currentPage = 1;
    pageCards.forEach(card => {
      if (card.offsetTop <= containerTop + 180) {
        currentPage = parseInt(card.dataset.page) || 1;
      }
    });

    updatePageCounterIndicator(currentPage);
  }

  function updatePageCounterIndicator(pageNum) {
    const totalPages = Math.min(8, activeViewerDoc ? (activeViewerDoc.pages || 5) : 5);
    inlinePageIndicator.textContent = `Trang ${pageNum} / ${totalPages}`;
  }

  function renderDocChatMessages() {
    docChatMessagesContainer.innerHTML = docChatHistory.map(msg => {
      const isUser = msg.sender === "USER";
      return `
        <div style="align-self: ${isUser ? 'flex-end' : 'flex-start'}; max-width: 85%;">
          <div style="font-size: 10px; font-weight: 700; color: var(--md-sys-color-on-surface-variant); margin-bottom: 2px;">
            ${isUser ? '👤 BẠN' : '🤖 ACADEMIC ASSISTANT'}
          </div>
          <div style="background: ${isUser ? 'var(--md-sys-color-primary-container)' : 'var(--md-sys-color-surface)'}; border: 1px solid var(--md-sys-color-outline); padding: 8px 12px; border-radius: 8px; font-size: 12px; line-height: 1.5; color: var(--md-sys-color-on-surface);">
            ${msg.text}
          </div>
        </div>
      `;
    }).join("");

    docChatMessagesContainer.scrollTop = docChatMessagesContainer.scrollHeight;
  }

  function handleSendDocChat() {
    const query = docChatInput.value.trim();
    if (!query || !activeViewerDoc) return;

    docChatHistory.push({
      id: "doc-msg-" + Date.now(),
      sender: "USER",
      text: query
    });

    docChatInput.value = "";
    renderDocChatMessages();

    const assistantMsgId = "doc-msg-ai-" + Date.now();
    docChatHistory.push({
      id: assistantMsgId,
      sender: "ASSISTANT",
      text: "⌛ <i>Đang phân tích đoạn trích tài liệu...</i>"
    });
    renderDocChatMessages();

    const user = getCurrentUser();
    llm.askAcademicAssistant({
      query: query + " trong tài liệu " + activeViewerDoc.title,
      subjectId: activeViewerDoc.subject_id,
      userId: user.id,
      role: activeRole,
      onChunk: (chunkText) => {
        const msgObj = docChatHistory.find(m => m.id === assistantMsgId);
        if (msgObj) {
          msgObj.text = chunkText;
          renderDocChatMessages();
        }
      },
      onComplete: (resObj) => {
        const msgObj = docChatHistory.find(m => m.id === assistantMsgId);
        if (msgObj) {
          msgObj.text = resObj.text;
          renderDocChatMessages();
        }
      }
    });
  }

  // ==========================================
  // KNOWLEDGE HUB GRID LOGIC
  // ==========================================

  function getFilteredDocuments() {
    const user = getCurrentUser();

    return data.documents.filter(doc => {
      if (activeRole === "STUDENT") {
        const isApprovedPublic = doc.visibility === "PUBLIC" && doc.approval_status === "APPROVED";
        const isOwnDoc = doc.owner_id === user.id;
        const isInvitedPrivate = doc.visibility === "PRIVATE" && doc.approval_status === "APPROVED" && doc.invited_user_ids && doc.invited_user_ids.includes(user.id);

        if (!isApprovedPublic && !isOwnDoc && !isInvitedPrivate) return false;
      }

      if (filters.school !== "ALL" && doc.school !== filters.school) return false;
      if (filters.docType !== "ALL" && doc.document_type !== filters.docType) return false;
      if (filters.visibility !== "ALL" && doc.visibility !== filters.visibility) return false;

      if (filters.search) {
        const text = (doc.title + " " + doc.description + " " + doc.subject_name + " " + doc.owner_name).toLowerCase();
        if (!text.includes(filters.search)) return false;
      }

      return true;
    });
  }

  function renderDocumentGrid() {
    const docs = getFilteredDocuments();

    if (docs.length === 0) {
      docCardsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 48px; text-align: center; background: var(--md-sys-color-surface); border: 1px solid var(--md-sys-color-outline); border-radius: var(--md-shape-corner-large);">
          <h3>🔍 KHÔNG TÌM THẤY TÀI LIỆU PHÙ HỢP</h3>
          <p style="font-size: 13px; color: var(--md-sys-color-on-surface-variant); margin-top: 8px;">Vui lòng điều chỉnh lại bộ lọc hoặc từ khóa tìm kiếm.</p>
        </div>`;
      return;
    }

    docCardsGrid.innerHTML = docs.map(doc => {
      const isSelected = selectedDocIds.has(doc.id);
      const isPublic = doc.visibility === "PUBLIC";
      const isApproved = doc.approval_status === "APPROVED";
      const isPending = doc.approval_status === "PENDING";

      return `
        <div class="doc-card">
          <input type="checkbox" class="doc-select-checkbox" data-id="${doc.id}" ${isSelected ? 'checked' : ''}>
          <div class="doc-card-body">
            <div class="doc-card-meta">
              <span class="badge yellow">${doc.school}</span>
              <span class="badge blue">${doc.document_type}</span>
              <span class="badge ${isPublic ? 'green' : 'purple'}">${isPublic ? 'PUBLIC' : 'PRIVATE'}</span>
              ${!isApproved ? `<span class="badge ${isPending ? 'yellow' : 'red'}">${doc.approval_status}</span>` : ''}
            </div>
            <div class="doc-card-title">${doc.title}</div>
            <div class="doc-card-desc">${doc.description}</div>
            <div class="doc-card-footer-info">
              <span>📅 ${doc.created_at}</span>
              <span>👤 ${doc.owner_name}</span>
            </div>
          </div>
          <button class="doc-card-btn btn-view-doc" data-id="${doc.id}">VIEW DETAILS / XEM CHI TIẾT ➔</button>
        </div>
      `;
    }).join("");

    docCardsGrid.querySelectorAll(".doc-select-checkbox").forEach(cb => {
      cb.addEventListener("change", (e) => {
        const id = e.target.dataset.id;
        if (e.target.checked) selectedDocIds.add(id);
        else selectedDocIds.delete(id);
        selectedCountEl.textContent = selectedDocIds.size;
      });
    });

    docCardsGrid.querySelectorAll(".btn-view-doc").forEach(btn => {
      btn.addEventListener("click", () => openDocumentDetails(btn.dataset.id));
    });
  }

  // Batch Operations
  function handleBatchSummary() {
    const ids = Array.from(selectedDocIds);
    if (ids.length === 0) {
      alert("Vui lòng chọn ít nhất 1 tài liệu!");
      return;
    }

    const summaryText = llm.summarizeDocuments(ids);
    batchResultTitle.textContent = "📝 KNOWLEDGE HUB AGENT - TỔNG HỢP TÀI LIỆU";
    batchResultBody.innerHTML = `<div style="white-space: pre-wrap; font-size: 14px; line-height: 1.6; color: var(--md-sys-color-on-surface);">${summaryText}</div>`;
    modalBatchResult.classList.remove("hidden");
  }

  function handleBatchCompare() {
    const ids = Array.from(selectedDocIds);
    if (ids.length < 2) {
      alert("Vui lòng chọn từ 2 tài liệu trở lên!");
      return;
    }

    const compareHTML = llm.compareDocuments(ids);
    batchResultTitle.textContent = "⚖️ KNOWLEDGE HUB AGENT - BẢNG SO SÁNH ĐỐI CHIẾU";
    batchResultBody.innerHTML = compareHTML;
    modalBatchResult.classList.remove("hidden");
  }

  // ==========================================
  // GLOBAL ACADEMIC ASSISTANT LOGIC
  // ==========================================

  function renderGlobalChatMessages() {
    chatMessagesEl.innerHTML = globalChatHistory.map(msg => {
      const isUser = msg.sender === "USER";
      
      let citationsHTML = "";
      if (msg.citations && msg.citations.length > 0) {
        citationsHTML = `<div style="margin-top: 10px; border-top: 1px dashed var(--md-sys-color-outline); padding-top: 8px;">
          <div style="font-size: 11px; font-weight: 700; color: #a5b4fc;">📍 Trích dẫn nguồn tài liệu:</div>
          ${msg.citations.map((c, i) => `
            <span class="citation-pill" data-docid="${c.docId}" data-page="${c.page}" data-excerpt="${encodeURIComponent(c.excerpt)}">
              📌 [${i + 1}] ${c.docTitle} (Trang ${c.page})
            </span>
          `).join("")}
        </div>`;
      }

      return `
        <div class="message ${isUser ? 'user' : 'assistant'}">
          <div style="font-size: 11px; font-weight: 700; margin-bottom: 4px; color: var(--md-sys-color-on-surface-variant);">${isUser ? '👤 BẠN' : '🤖 ACADEMIC ASSISTANT'}</div>
          <div class="message-bubble">
            ${msg.text}
            ${citationsHTML}
          </div>
        </div>
      `;
    }).join("");

    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;

    chatMessagesEl.querySelectorAll(".citation-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        const docTitle = pill.textContent;
        const page = pill.dataset.page;
        const excerpt = decodeURIComponent(pill.dataset.excerpt);

        citationBody.innerHTML = `
          <div style="font-size: 14px; font-weight: 800; margin-bottom: 8px; color: var(--md-sys-color-primary);">Nguồn trích dẫn chính xác:</div>
          <div style="background: var(--md-sys-color-surface-container); border: 1px solid var(--md-sys-color-primary); padding: 12px; font-weight: 700; font-size: 13px; margin-bottom: 12px; border-radius: 8px; color: #fff;">
            ${docTitle}
          </div>
          <div style="background: var(--md-sys-color-background); border: 1px solid var(--md-sys-color-outline); padding: 16px; font-size: 13px; border-radius: 8px;">
            <strong>[Trang ${page}]:</strong> "${excerpt}"
          </div>
        `;
        modalCitation.classList.remove("hidden");
      });
    });
  }

  function handleSendGlobalChat() {
    const query = chatInput.value.trim();
    if (!query) return;

    globalChatHistory.push({
      id: "msg-" + Date.now(),
      sender: "USER",
      text: query,
      citations: []
    });

    chatInput.value = "";
    renderGlobalChatMessages();

    const assistantMsgId = "msg-ai-" + Date.now();
    globalChatHistory.push({
      id: assistantMsgId,
      sender: "ASSISTANT",
      text: "⌛ <i>Đang truy xuất vector chunks và kiểm tra quyền tài liệu...</i>",
      citations: []
    });
    renderGlobalChatMessages();

    const user = getCurrentUser();
    const selectedSubj = chatSubjectSelect.value;

    llm.askAcademicAssistant({
      query: query,
      subjectId: selectedSubj,
      userId: user.id,
      role: activeRole,
      onChunk: (chunkText) => {
        const msgObj = globalChatHistory.find(m => m.id === assistantMsgId);
        if (msgObj) {
          msgObj.text = chunkText;
          renderGlobalChatMessages();
        }
      },
      onComplete: (resObj) => {
        const msgObj = globalChatHistory.find(m => m.id === assistantMsgId);
        if (msgObj) {
          msgObj.text = resObj.text;
          msgObj.citations = resObj.citations;
          msgObj.grounded_status = resObj.grounded_status;
          renderGlobalChatMessages();
        }
      }
    });
  }

  // ==========================================
  // MULTI-COURSE LEARNING DASHBOARD LOGIC
  // ==========================================

  function renderLearningPathsDashboard() {
    const user = getCurrentUser();
    const userPaths = data.learningPaths.filter(p => p.user_id === user.id || activeRole === "LECTURER");
    userPathCountEl.textContent = userPaths.length;

    if (userPaths.length === 0) {
      learningPathsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 40px; text-align: center; background: var(--md-sys-color-surface); border: 1px solid var(--md-sys-color-outline); border-radius: var(--md-shape-corner-large);">
          <h3>🎯 CHƯA CÓ LỘ TRÌNH HỌC NÀO ĐƯỢC TẠO</h3>
          <p style="font-size: 13px; color: var(--md-sys-color-on-surface-variant); margin-top: 8px;">Hãy chọn môn học và mục tiêu ở biểu mẫu phía trên để AI khởi tạo lộ trình tự động!</p>
        </div>`;
      return;
    }

    learningPathsGrid.innerHTML = userPaths.map(path => {
      const completedSessions = path.sessions.filter(s => s.status === "COMPLETED").length;
      const totalSessions = path.sessions.length;
      const percent = Math.round((completedSessions / totalSessions) * 100);
      path.progress_percent = percent;

      const isCompleted = percent === 100;

      return `
        <div class="course-path-card">
          <div>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
              <span class="badge yellow">${path.subject_name}</span>
              <span class="badge ${isCompleted ? 'blue' : 'green'}">${isCompleted ? 'HOÀN THÀNH 100%' : 'ĐANG HỌC (' + path.duration_days + ' NGÀY)'}</span>
            </div>
            
            <h3 style="font-size: 15px; font-weight: 800; color: #fff; margin-bottom: 6px; line-height: 1.3;">${path.title}</h3>
            <p style="font-size: 12px; color: var(--md-sys-color-on-surface-variant); margin-bottom: 14px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
              🎯 ${path.goal}
            </p>

            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; font-size: 12px; font-weight: 700;">
              <span>Mức độ hoàn thiện:</span>
              <span style="color: ${isCompleted ? '#34d399' : '#a5b4fc'};">${percent}% (${completedSessions}/${totalSessions} buổi)</span>
            </div>

            <div class="progress-bar-container">
              <div class="progress-bar-fill" style="width: ${percent}%;"></div>
            </div>
          </div>

          <button class="btn-action btn-open-path-details" data-pathid="${path.id}" style="width: 100%; margin-top: 12px; height: 40px; font-size: 13px; background: var(--md-sys-color-surface-container); color: var(--md-sys-color-primary); border: 1px solid var(--md-sys-color-outline);">
            👁️ XEM CHI TIẾT LỘ TRÌNH ➔
          </button>
        </div>
      `;
    }).join("");

    learningPathsGrid.querySelectorAll(".btn-open-path-details").forEach(btn => {
      btn.addEventListener("click", () => openPathDetailsModal(btn.dataset.pathid));
    });
  }

  function openPathDetailsModal(pathId) {
    const path = data.learningPaths.find(p => p.id === pathId);
    if (!path) return;

    activeDetailPath = path;
    pathModalTitle.textContent = `🎯 ${path.title}`;

    renderPathDetailsModalBody();
    modalPathDetails.classList.remove("hidden");
  }

  function renderPathDetailsModalBody() {
    if (!activeDetailPath) return;

    const path = activeDetailPath;
    const completedSessions = path.sessions.filter(s => s.status === "COMPLETED").length;
    const totalSessions = path.sessions.length;
    const percent = Math.round((completedSessions / totalSessions) * 100);
    path.progress_percent = percent;

    pathDetailsBody.innerHTML = `
      <div style="background: var(--md-sys-color-surface); border: 1px solid var(--md-sys-color-outline); padding: 18px; border-radius: 12px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
          <div>
            <span class="badge yellow">${path.subject_name}</span>
            <span class="badge green">${path.duration_days} NGÀY</span>
          </div>
          <div style="font-size: 20px; font-weight: 900; color: #34d399;">${percent}% HOÀN THÀNH</div>
        </div>
        <p style="font-size: 13px; color: var(--md-sys-color-on-surface-variant); margin-bottom: 12px;"><strong>Mục tiêu:</strong> ${path.goal}</p>
        
        <div class="progress-bar-container">
          <div class="progress-bar-fill" style="width: ${percent}%;"></div>
        </div>
      </div>

      <div style="font-size: 14px; font-weight: 800; color: #fff; margin-bottom: 12px;">📚 NỘI DUNG VÀ TIẾN ĐỘ CÁC BUỔI HỌC (${completedSessions}/${totalSessions} buổi):</div>

      <div style="display: flex; flex-direction: column; gap: 14px;">
        ${path.sessions.map(s => {
          const isDone = s.status === "COMPLETED";
          return `
            <div class="session-card ${isDone ? 'completed' : ''}">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <div style="font-size: 15px; font-weight: 800; color: ${isDone ? '#34d399' : '#fff'};">${isDone ? '✅' : '📌'} ${s.title}</div>
                <button class="btn-action btn-toggle-session-modal" data-pathid="${path.id}" data-sessid="${s.id}" style="padding: 6px 14px; font-size: 12px; background: ${isDone ? 'rgba(16, 185, 129, 0.2)' : 'var(--md-sys-color-primary)'}; color: ${isDone ? '#34d399' : '#0f172a'}; border: ${isDone ? '1px solid #34d399' : 'none'};">
                  ${isDone ? 'ĐÃ HOÀN THÀNH ✓' : 'ĐÁNH DẤU HOÀN THÀNH'}
                </button>
              </div>
              
              <p style="font-size: 12px; font-weight: 700; color: #a5b4fc; margin-bottom: 8px;">🎯 Mục tiêu: ${s.objectives}</p>
              
              <div style="font-size: 12px; background: var(--md-sys-color-surface); border: 1px solid var(--md-sys-color-outline); padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;">
                <strong>📚 Tài liệu gợi ý:</strong> ${s.document_title} (${s.page_range})
              </div>
              
              <div style="font-size: 12px; background: var(--md-sys-color-surface); border: 1px solid var(--md-sys-color-outline); padding: 12px 14px; border-radius: 8px;">
                <div style="color: #6ee7b7; font-weight: 700; margin-bottom: 4px;">💡 Lý thuyết cô đọng:</div>
                <div style="margin-bottom: 8px; line-height: 1.5; color: var(--md-sys-color-on-surface-variant);">${s.theory_content}</div>
                <div style="color: #fbbf24; font-weight: 700; margin-bottom: 2px;">✏️ Bài tập luyện tập:</div>
                <div style="font-style: italic; color: var(--md-sys-color-on-surface-variant);">${s.exercise_content}</div>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    `;

    pathDetailsBody.querySelectorAll(".btn-toggle-session-modal").forEach(btn => {
      btn.addEventListener("click", () => {
        toggleSessionStatus(btn.dataset.pathid, btn.dataset.sessid);
      });
    });
  }

  function toggleSessionStatus(pathId, sessId) {
    const path = data.learningPaths.find(p => p.id === pathId);
    if (!path) return;
    const sess = path.sessions.find(s => s.id === sessId);
    if (!sess) return;

    sess.status = sess.status === "COMPLETED" ? "NOT_STARTED" : "COMPLETED";

    const completedCount = path.sessions.filter(s => s.status === "COMPLETED").length;
    path.progress_percent = Math.round((completedCount / path.sessions.length) * 100);

    renderPathDetailsModalBody();
    renderLearningPathsDashboard();
  }

  function handleGeneratePath() {
    const subjectId = pathSubjectSelect.value;
    const goal = pathGoalInput.value.trim();
    const durationDays = pathDurationInput.value;

    const newPath = llm.generateLearningPath({ subjectId, goal, durationDays });
    data.learningPaths.unshift(newPath);
    renderLearningPathsDashboard();
    alert(`🎉 Đã khởi tạo thành công lộ trình học tập "${newPath.title}"!`);
  }

  // ==========================================
  // LECTURER MANAGEMENT LOGIC
  // ==========================================

  function renderManagementTab() {
    if (activeRole !== "LECTURER") return;

    const pendingDocs = data.documents.filter(d => d.approval_status === "PENDING");
    if (pendingDocs.length === 0) {
      pendingDocsList.innerHTML = `<p style="font-size: 13px; color: var(--md-sys-color-on-surface-variant);">(Chưa có tài liệu nào chờ duyệt)</p>`;
    } else {
      pendingDocsList.innerHTML = pendingDocs.map(d => `
        <div style="background: var(--md-sys-color-surface-container); border: 1px solid var(--md-sys-color-outline); padding: 14px; border-radius: 12px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
          <div>
            <span class="badge yellow">${d.school}</span>
            <span class="badge blue">${d.document_type}</span>
            <strong style="font-size: 14px;">${d.title}</strong>
            <div style="font-size: 12px; color: var(--md-sys-color-on-surface-variant);">Người đăng: ${d.owner_name}</div>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn-action btn-approve" data-id="${d.id}" style="background: var(--md-sys-color-secondary); color: #000;">✅ DUYỆT</button>
            <button class="btn-action btn-reject" data-id="${d.id}" style="background: var(--md-sys-color-error); color: #fff;">❌ TỪ CHỐI</button>
          </div>
        </div>
      `).join("");

      pendingDocsList.querySelectorAll(".btn-approve").forEach(btn => {
        btn.addEventListener("click", () => approveDoc(btn.dataset.id));
      });

      pendingDocsList.querySelectorAll(".btn-reject").forEach(btn => {
        btn.addEventListener("click", () => rejectDoc(btn.dataset.id));
      });
    }

    const privateDocs = data.documents.filter(d => d.visibility === "PRIVATE");
    privateDocsManagementList.innerHTML = privateDocs.map(d => {
      const invitedCount = (d.invited_user_ids || []).length;
      return `
        <div style="background: var(--md-sys-color-surface-container); border: 1px solid var(--md-sys-color-outline); padding: 14px; border-radius: 12px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
          <div>
            <span class="badge purple">PRIVATE</span>
            <strong style="font-size: 14px;">${d.title}</strong>
            <div style="font-size: 12px; color: var(--md-sys-color-on-surface-variant);">Được cấp quyền: ${invitedCount} sinh viên</div>
          </div>
          <button class="btn-action btn-toggle-invite" data-id="${d.id}">🔒 CẤP / THU HỒI QUYỀN SINH VIÊN A</button>
        </div>
      `;
    }).join("");

    privateDocsManagementList.querySelectorAll(".btn-toggle-invite").forEach(btn => {
      btn.addEventListener("click", () => togglePrivateAccess(btn.dataset.id));
    });
  }

  function approveDoc(docId) {
    const doc = data.documents.find(d => d.id === docId);
    if (!doc) return;
    doc.approval_status = "APPROVED";
    alert(`✅ Đã phê duyệt tài liệu "${doc.title}"!`);
    renderDocumentGrid();
    renderManagementTab();
  }

  function rejectDoc(docId) {
    const doc = data.documents.find(d => d.id === docId);
    if (!doc) return;
    const reason = prompt("Nhập lý do từ chối:", "Không đúng định dạng chuẩn.");
    if (reason !== null) {
      doc.approval_status = "REJECTED";
      alert(`❌ Đã từ chối tài liệu "${doc.title}".`);
      renderDocumentGrid();
      renderManagementTab();
    }
  }

  function togglePrivateAccess(docId) {
    const doc = data.documents.find(d => d.id === docId);
    if (!doc) return;

    if (!doc.invited_user_ids) doc.invited_user_ids = [];
    const stdId = "user-std-1";

    if (doc.invited_user_ids.includes(stdId)) {
      doc.invited_user_ids = doc.invited_user_ids.filter(id => id !== stdId);
      alert(`🚫 Đã thu hồi quyền của Sinh viên A với "${doc.title}"!`);
    } else {
      doc.invited_user_ids.push(stdId);
      alert(`✅ Đã cấp quyền cho Sinh viên A vào "${doc.title}"!`);
    }

    renderDocumentGrid();
    renderManagementTab();
  }

  // Upload Submit
  function handleUploadSubmit(e) {
    e.preventDefault();

    const title = document.getElementById("upload-title").value.trim();
    const subjectId = document.getElementById("upload-subject").value;
    const docType = document.getElementById("upload-type").value;
    const desc = document.getElementById("upload-desc").value.trim();
    const visibility = (activeRole === "LECTURER") ? document.getElementById("upload-visibility").value : "PUBLIC";

    const user = getCurrentUser();
    const subj = data.subjects.find(s => s.id === subjectId) || data.subjects[0];

    const newDoc = {
      id: "doc-" + Date.now(),
      school: subj.school,
      subject_id: subj.id,
      subject_name: subj.name,
      title: title,
      description: desc || "Tài liệu tải lên từ người dùng.",
      document_type: docType,
      file_url: title.replace(/\s+/g, '_') + ".pdf",
      owner_id: user.id,
      owner_name: user.full_name,
      visibility: visibility,
      approval_status: activeRole === "LECTURER" ? "APPROVED" : "PENDING",
      approved_by: activeRole === "LECTURER" ? user.id : null,
      rejection_reason: null,
      semester: "Học kỳ 2",
      academic_year: "2025-2026",
      created_at: new Date().toLocaleDateString('vi-VN'),
      downloads: 0,
      pages: 15,
      chunks: [
        {
          id: "chunk-new-1",
          page_number: 1,
          content: desc || `Nội dung tổng quan của tài liệu ${title}.`
        }
      ]
    };

    data.documents.unshift(newDoc);
    modalUpload.classList.add("hidden");
    formUpload.reset();

    alert(activeRole === "LECTURER" ? `🚀 Giảng viên tải lên thành công!` : `ℹ️ Sinh viên tải lên thành công! Đang ở trạng thái CHỜ DUYỆT (PENDING).`);
    renderDocumentGrid();
    renderManagementTab();
  }

  init();
});
