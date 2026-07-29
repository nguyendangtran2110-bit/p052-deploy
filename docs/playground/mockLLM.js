// MockLLM Engine for EduHub (docs/playground)
window.MockLLM = {
  // Helper to filter documents accessible to current role
  getAccessibleApprovedDocuments: function(userId, role, subjectId = null) {
    const data = window.EduHubData;
    return data.documents.filter(doc => {
      // 1. Must be APPROVED (PENDING or REJECTED are ignored by AI)
      if (doc.approval_status !== "APPROVED") return false;

      // 2. Subject filter if provided
      if (subjectId && subjectId !== "ALL" && doc.subject_id !== subjectId) return false;

      // 3. Permission check
      if (role === "LECTURER") return true; // Lecturer has access to all internal docs

      if (doc.visibility === "PUBLIC") return true;

      if (doc.visibility === "PRIVATE") {
        return doc.invited_user_ids && doc.invited_user_ids.includes(userId);
      }

      return false;
    });
  },

  // 1. Knowledge Hub Agent - Interactive Document Overview Generator
  generateDocumentOverview: function(docId) {
    const data = window.EduHubData;
    const doc = data.documents.find(d => d.id === docId);

    if (!doc) {
      return {
        summary: "Không tìm thấy dữ liệu tài liệu.",
        takeaways: [],
        sections: []
      };
    }

    if (doc.subject_name.includes("Tín hiệu")) {
      return {
        summary: `Tài liệu "${doc.title}" là giáo trình/lời giải nền tảng cho ngành Kỹ thuật Điện tử & Máy tính tại ${doc.school}. Nội dung tập trung vào lý thuyết LTI, biểu diễn miền tần số (Fourier) và miền s (Laplace).`,
        takeaways: [
          "⚡ **Phép cuộn LTI**: Đầu ra y(t) = x(t) * h(t). Khảo sát tính nhân quả & ổn định.",
          "📈 **Biến đổi Fourier**: Chuyển đổi từ tín hiệu thời gian liên tục sang miền tần số w.",
          "🎯 **Biến đổi Laplace**: Phân tích hàm truyền H(s) = Y(s)/X(s) và vị trí các cực trên mặt phẳng phức s."
        ],
        sections: [
          { title: "Phần 1: Tín hiệu & Hệ thống LTI (Trang 1-80)", detail: "Tổng quan phân loại tín hiệu và phương pháp tích phân cuộn." },
          { title: "Phần 2: Phân tích miền tần số Fourier (Trang 81-220)", detail: "Tính chất biến đổi Fourier, chuỗi Fourier và phổ tần số." },
          { title: "Phần 3: Biến đổi Laplace & Ứng dụng (Trang 221-400)", detail: "Giải phương trình vi phân và khảo sát độ ổn định của hệ thống." }
        ],
        examAdvice: "💡 **Lời khuyên ôn thi từ AI Agent**: Dành 60% thời gian luyện tập bài tập tính tích phân cuộn và xác định miền hội tụ ROC của biến đổi Laplace."
      };
    } else if (doc.subject_name.includes("Triết học")) {
      return {
        summary: `Tài liệu "${doc.title}" hệ thống hóa kiến thức Triết học Mác-Lênin theo chuẩn Bộ Giáo Dục, nhấn mạnh thế giới quan duy vật biện chứng và phương pháp luận duy vật lịch sử.`,
        takeaways: [
          "🌐 **Chủ nghĩa duy vật biện chứng**: Vật chất có trước, ý thức có sau; ý thức phản ánh năng động sáng tạo thế giới khách quan.",
          "⚖️ **Quy luật Lượng - Chất**: Tích lũy về lượng đến Điểm nút gặp Bước nhảy sẽ làm thay đổi về chất.",
          "🏛️ **Duy vật lịch sử**: Hình thái kinh tế - xã hội, quy luật quan hệ sản xuất phù hợp với trình độ phát triển của lực lượng sản xuất."
        ],
        sections: [
          { title: "Chương 1: Triết học & Vai trò trong đời sống xã hội (Trang 1-50)", detail: "Khái niệm triết học, vấn đề cơ bản của triết học." },
          { title: "Chương 2: Chủ nghĩa duy vật biện chứng (Trang 51-180)", detail: "Vật chất, ý thức, hai nguyên lý và ba quy luật cơ bản." },
          { title: "Chương 3: Chủ nghĩa duy vật lịch sử (Trang 181-340)", detail: "Học thuyết hình thái kinh tế - xã hội và vai trò quần chúng." }
        ],
        examAdvice: "💡 **Lời khuyên ôn thi từ AI Agent**: Liên hệ thực tiễn mối quan hệ giữa Lực lượng sản xuất và Quan hệ sản xuất tại Việt Nam hiện nay."
      };
    } else if (doc.subject_name.includes("Vật lý")) {
      return {
        summary: `Tài liệu đề thi & bài tập "${doc.title}" giúp tổng ôn lý thuyết Điện học và Từ học môn Vật lý đại cương 2 UET.`,
        takeaways: [
          "🧲 **Định luật Biot-Savart-Laplace**: Tính cảm ứng từ B tạo bởi dòng điện tròn B = (mu_0 * I)/(2R).",
          "⚡ **Định luật Gauss & Điện trường**: Phân tích điện thế V và cường độ điện trường E trong tụ điện.",
          "🌀 **Cảm ứng điện từ Faraday**: Suất điện động cảm ứng e = - d(Phi)/dt."
        ],
        sections: [
          { title: "Phần Điện học & Tụ điện (Câu 1-3)", detail: "Tính điện thế, công của lực điện trường." },
          { title: "Phần Từ trường & Dòng điện (Câu 4-6)", detail: "Từ trường trong dây dẫn thẳng và cuộn dây tròn." }
        ],
        examAdvice: "💡 **Lời khuyên ôn thi từ AI Agent**: Chú ý đổi đúng đơn vị SI (mm -> m, uF -> F) trước khi áp dụng công thức."
      };
    } else {
      return {
        summary: `Tài liệu "${doc.title}" thuộc danh mục môn ${doc.subject_name}. Tài liệu cung cấp kiến thức hệ thống, bài giảng và tài liệu tham khảo chính thức của ${doc.school}.`,
        takeaways: [
          "📌 **Cấu trúc tài liệu**: Được trình bày ngắn gọn, cô đọng.",
          "🎯 **Mục tiêu**: Giúp người học làm chủ các khái niệm trọng tâm.",
          "✅ **Tình trạng kiểm duyệt**: Đã được Giảng viên xác minh nội dung."
        ],
        sections: [
          { title: "Nội dung tổng quát", detail: doc.description }
        ],
        examAdvice: "💡 **Lời khuyên ôn thi từ AI Agent**: Đọc kết hợp tài liệu này với bài giảng Slide trên lớp để đạt hiệu quả cao nhất."
      };
    }
  },

  // 2. Academic Assistant Q&A Engine
  askAcademicAssistant: function({ query, subjectId, userId, role, onChunk, onComplete }) {
    const accessibleDocs = this.getAccessibleApprovedDocuments(userId, role, subjectId);
    let currentText = "";
    const lowerQuery = query.toLowerCase();

    if (lowerQuery.includes("mật") || lowerQuery.includes("bí mật") || lowerQuery.includes("đề thi mật") || lowerQuery.includes("olympic")) {
      const hasSecretAccess = accessibleDocs.some(d => d.id === "doc-10-private-denied");
      if (!hasSecretAccess) {
        const fallbackMsg = "⚠️ **Thông báo hệ thống (Strict Grounding Rules)**:\n\nHệ thống không tìm thấy tài liệu phù hợp đã được kiểm duyệt (`APPROVED`) mà tài khoản của bạn được cấp quyền truy cập để trả lời câu hỏi này. (Tài liệu ngân hàng đề thi mật thuộc phạm vi riêng tư chưa được chia sẻ cho tài khoản sinh viên).";
        onComplete({
          text: fallbackMsg,
          citations: [],
          grounded_status: "INSUFFICIENT_SOURCE"
        });
        return;
      }
    }

    let responseObj = null;

    if (lowerQuery.includes("tín hiệu") || lowerQuery.includes("lti") || lowerQuery.includes("cuộn") || lowerQuery.includes("fourier") || lowerQuery.includes("oppenheim")) {
      const doc1 = accessibleDocs.find(d => d.id === "doc-1");
      const doc2 = accessibleDocs.find(d => d.id === "doc-2");
      const doc9Private = accessibleDocs.find(d => d.id === "doc-9-private-allowed");

      let extraPrivateNote = "";
      let citations = [];

      if (doc1) {
        citations.push({
          docId: doc1.id,
          docTitle: doc1.title,
          page: 42,
          excerpt: doc1.chunks[0].content
        });
        citations.push({
          docId: doc1.id,
          docTitle: doc1.title,
          page: 178,
          excerpt: doc1.chunks[1].content
        });
      }

      if (doc2) {
        citations.push({
          docId: doc2.id,
          docTitle: doc2.title,
          page: 15,
          excerpt: doc2.chunks[0].content
        });
      }

      if (doc9Private) {
        extraPrivateNote = "\n\n🔒 **Bổ sung từ Tài liệu Private (Lab Nghiên cứu được cấp quyền)**:\nTrích dẫn nghiên cứu xử lý tín hiệu nâng cao bằng thuật toán Wavelet khử nhiễu ECG.";
        citations.push({
          docId: doc9Private.id,
          docTitle: doc9Private.title,
          page: 10,
          excerpt: doc9Private.chunks[0].content
        });
      }

      responseObj = {
        text: `Dựa trên các tài liệu đã kiểm duyệt về môn **Tín hiệu và Hệ thống**:\n\n` +
              `1. **Hệ thống LTI và Phép cuộn (Convolution)**:\n` +
              `Hệ thống Tuyến tính Bất biến theo thời gian (LTI) có đặc tính quan trọng: Đầu ra $y(t)$ được tính bằng phép tích phân cuộn giữa đầu vào $x(t)$ và phản ứng xung $h(t)$ [1].\n\n` +
              `2. **Biến đổi Fourier (CTFT)**:\n` +
              `Phân tích tín hiệu từ miền thời gian sang miền tần số $\\omega$. Công thức thuận: $X(\\omega) = \\int_{-\\infty}^{\\infty} x(t) e^{-j\\omega t} dt$ [2].\n\n` +
              `3. **Bài tập mẫu có đáp án**:\n` +
              `Với tín hiệu bước $u(t)$ và phản ứng xung $e^{-2t}u(t)$, kết quả tích phân cuộn thu được là $y(t) = 0.5(1 - e^{-2t})u(t)$ [3].` + extraPrivateNote,
        citations: citations,
        grounded_status: "GROUNDED"
      };
    } else if (lowerQuery.includes("triết") || lowerQuery.includes("chất") || lowerQuery.includes("lượng") || lowerQuery.includes("mác")) {
      const doc5 = accessibleDocs.find(d => d.id === "doc-5");
      let citations = [];
      if (doc5) {
        citations.push({
          docId: doc5.id,
          docTitle: doc5.title,
          page: 65,
          excerpt: doc5.chunks[0].content
        });
      }
      responseObj = {
        text: `Dựa trên **Giáo trình Triết học Mác-Lênin** [1]:\n\n` +
              `**Quy luật chuyển hóa từ những thay đổi về lượng dẫn đến những thay đổi về chất và ngược lại**:\n` +
              `- **Lượng** là thuộc tính biểu thị số lượng, quy mô, tốc độ của sự vật hiện tượng.\n` +
              `- **Chất** là tổng hợp các thuộc tính khách quan làm cho sự vật là chính nó.\n` +
              `- Sự tích lũy về lượng đến một giới hạn nhất định (Độ) gặp Bước nhảy sẽ dẫn tới sự thay đổi căn bản về chất.`,
        citations: citations,
        grounded_status: "GROUNDED"
      };
    } else {
      if (accessibleDocs.length === 0) {
        responseObj = {
          text: "⚠️ **Không tìm thấy dữ liệu**: Hiện không có tài liệu nào trong danh mục môn học này được cấp quyền cho bạn hoặc tài liệu chưa được duyệt (`APPROVED`).",
          citations: [],
          grounded_status: "INSUFFICIENT_SOURCE"
        };
      } else {
        const topDoc = accessibleDocs[0];
        responseObj = {
          text: `Dựa trên tài liệu **${topDoc.title}** [1] (Học kỳ ${topDoc.semester}):\n\n` +
                `Hệ thống đã trích xuất nội dung liên quan tới câu hỏi "${query}":\n` +
                `Nội dung tài liệu cung cấp kiến thức nền tảng và bài tập thực hành theo chuẩn chương trình đào tạo của ${topDoc.school}.`,
          citations: [
            {
              docId: topDoc.id,
              docTitle: topDoc.title,
              page: topDoc.chunks && topDoc.chunks[0] ? topDoc.chunks[0].page_number : 1,
              excerpt: topDoc.chunks && topDoc.chunks[0] ? topDoc.chunks[0].content : topDoc.description
            }
          ],
          grounded_status: "GROUNDED"
        };
      }
    }

    let chars = responseObj.text.split("");
    let idx = 0;
    const interval = setInterval(() => {
      if (idx < chars.length) {
        const chunk = chars.slice(0, idx + 5).join("");
        onChunk(chunk);
        idx += 5;
      } else {
        clearInterval(interval);
        onComplete(responseObj);
      }
    }, 15);
  },

  // 3. Knowledge Hub Batch Operations
  summarizeDocuments: function(docIds) {
    const data = window.EduHubData;
    const selectedDocs = data.documents.filter(d => docIds.includes(d.id));
    if (selectedDocs.length === 0) return "Vui lòng chọn ít nhất 1 tài liệu để tổng hợp.";

    let summaryText = `### 📊 KNOWLEDGE HUB AGENT - TỔNG HỢP ${selectedDocs.length} TÀI LIỆU\n\n`;
    selectedDocs.forEach((doc, idx) => {
      summaryText += `#### ${idx + 1}. ${doc.title} (${doc.document_type} - ${doc.school})\n`;
      summaryText += `- **Tác giả / Nguồn**: ${doc.owner_name} | **Năm học**: ${doc.academic_year}\n`;
      summaryText += `- **Nội dung chính**: ${doc.description}\n\n`;
    });
    return summaryText;
  },

  compareDocuments: function(docIds) {
    const data = window.EduHubData;
    const selectedDocs = data.documents.filter(d => docIds.includes(d.id));
    if (selectedDocs.length < 2) return "Vui lòng chọn từ 2 tài liệu trở lên để thực hiện so sánh.";

    let compareHTML = `<div class="compare-container">
      <h3>⚖️ KNOWLEDGE HUB AGENT - BẢNG SO SÁNH ĐỐI CHIẾU</h3>
      <table class="neo-table">
        <thead>
          <tr>
            <th>Tiêu chí</th>
            ${selectedDocs.map(d => `<th>${d.title}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Loại tài liệu</strong></td>
            ${selectedDocs.map(d => `<td><span class="badge yellow">${d.document_type}</span></td>`).join('')}
          </tr>
          <tr>
            <td><strong>Trường / Khoa</strong></td>
            ${selectedDocs.map(d => `<td>${d.school}</td>`).join('')}
          </tr>
          <tr>
            <td><strong>Nội dung trọng tâm</strong></td>
            ${selectedDocs.map(d => `<td>${d.description}</td>`).join('')}
          </tr>
        </tbody>
      </table>
    </div>`;

    return compareHTML;
  },

  // 4. Learning Assistant Roadmap Generator
  generateLearningPath: function({ subjectId, goal, durationDays }) {
    const data = window.EduHubData;
    const subj = data.subjects.find(s => s.id === subjectId) || data.subjects[0];
    const relatedDoc = data.documents.find(d => d.subject_id === subj.id && d.approval_status === "APPROVED") || data.documents[0];

    const newPath = {
      id: "path-" + Date.now(),
      user_id: data.users[0].id,
      subject_id: subj.id,
      subject_name: subj.name,
      title: `Lộ trình ${durationDays} ngày: ${goal || 'Ôn tập môn ' + subj.name}`,
      goal: goal || `Nắm vững toàn bộ kiến thức trọng tâm môn ${subj.name}`,
      duration_days: parseInt(durationDays) || 5,
      status: "ACTIVE",
      progress_percent: 0,
      sessions: []
    };

    const sessionCount = Math.max(2, Math.min(7, parseInt(durationDays)));
    for (let i = 1; i <= sessionCount; i++) {
      newPath.sessions.push({
        id: `sess-${newPath.id}-${i}`,
        session_order: i,
        title: `Buổi ${i}: ${i === 1 ? 'Tổng quan & Khái niệm cơ bản' : i === sessionCount ? 'Tổng ôn & Giải đề thi mẫu' : 'Chuyên đề lý thuyết & Vận dụng ' + (i - 1)}`,
        objectives: `Nắm vững mục tiêu bài học số ${i} và hoàn thành bài tập áp dụng.`,
        document_id: relatedDoc.id,
        document_title: relatedDoc.title,
        page_range: `Trang ${i * 15} - ${i * 15 + 25}`,
        theory_content: `Nội dung cô đọng buổi ${i}: Nghiên cứu các khái niệm cốt lõi theo tài liệu ${relatedDoc.title}.`,
        exercise_content: `Bài tập vận dụng buổi ${i}: Trả lời các câu hỏi tự luyện trong tài liệu.`,
        status: "NOT_STARTED"
      });
    }

    return newPath;
  }
};
