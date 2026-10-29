const form = document.querySelector("#analyzer-form");
const fileInput = document.querySelector("#resume-file");
const dropzone = document.querySelector("#dropzone");
const fileName = document.querySelector("#file-name");
const status = document.querySelector("#status");
const results = document.querySelector("#results");
const content = document.querySelector("#result-content");
let latestAnalysis = null;

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "";
});
["dragover", "dragenter"].forEach((event) => dropzone.addEventListener(event, (e) => {
  e.preventDefault(); dropzone.classList.add("active");
}));
["dragleave", "drop"].forEach((event) => dropzone.addEventListener(event, (e) => {
  e.preventDefault(); dropzone.classList.remove("active");
}));
dropzone.addEventListener("drop", (event) => {
  fileInput.files = event.dataTransfer.files;
  fileName.textContent = fileInput.files[0]?.name || "";
});

const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
}[char]));
const pills = (items, soft = false) => (items || []).map((item) => `<span class="pill ${soft ? "soft" : ""}">${escapeHtml(item)}</span>`).join("");
const listItems = (items, type) => (items || []).map((item) => {
  if (type === "missing") return `<div class="item"><span class="priority">${escapeHtml(item.priority)}</span><strong>${escapeHtml(item.skill)}</strong><p>${escapeHtml(item.reason)}</p></div>`;
  return `<div class="item"><strong>${escapeHtml(item.topic || item.section)}</strong><p>${escapeHtml(item.project_idea || item.suggestion)}</p></div>`;
}).join("") || '<p class="empty">No items detected.</p>';

function render(data) {
  latestAnalysis = data;
  const roles = data.job_recommendations.map((role) => `<div class="role"><div class="role-line"><span>${escapeHtml(role.role)}</span><span class="score">${role.suitability_score}%</span></div><div class="bar"><i style="width:${role.suitability_score}%"></i></div><small>${escapeHtml(role.reason)}</small></div>`).join("");
  content.innerHTML = `<div class="summary">${escapeHtml(data.resume_summary)}</div><div class="grid">
    <div class="panel"><h3>Skills detected</h3>${pills(data.skills.technical)}${pills(data.skills.soft, true)}<p><b>Strengths:</b> ${escapeHtml(data.skills.strengths.join(", "))}</p></div>
    <div class="panel"><h3>Recommended roles</h3>${roles}</div>
    <div class="panel"><h3>Skill gaps</h3>${listItems(data.missing_skills, "missing")}</div>
    <div class="panel"><h3>Learning roadmap</h3>${listItems(data.learning_suggestions, "learning")}</div>
    <div class="panel" style="grid-column:1/-1"><h3>Resume improvements</h3>${listItems(data.resume_improvements, "improvement")}</div>
  </div><p class="privacy">${escapeHtml(data.disclaimer)}</p>`;
  results.hidden = false;
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  status.style.display = "none";
  const text = document.querySelector("#resume-text").value.trim();
  const role = document.querySelector("#target-role").value;
  if (!fileInput.files.length && text.length < 50) {
    status.textContent = "Upload a PDF/DOCX or paste at least 50 characters of resume text.";
    status.style.display = "block";
    return;
  }
  const button = form.querySelector("button");
  button.disabled = true; button.innerHTML = "Analyzing…";
  try {
    let response;
    if (fileInput.files.length) {
      const body = new FormData();
      body.append("file", fileInput.files[0]);
      if (role) body.append("target_role", role);
      response = await fetch("/api/analyze/file", { method: "POST", body });
    } else {
      response = await fetch("/api/analyze/text", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: text, target_role: role || null }),
      });
    }
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Analysis failed.");
    render(data);
  } catch (error) {
    status.textContent = error.message;
    status.style.display = "block";
  } finally {
    button.disabled = false; button.innerHTML = "Analyze my resume <span>→</span>";
  }
});
document.querySelector("#print-report").addEventListener("click", async () => {
  if (!latestAnalysis) return;
  const button = document.querySelector("#print-report");
  button.disabled = true;
  button.textContent = "Preparing PDF…";
  status.style.display = "none";
  try {
    const response = await fetch("/api/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(latestAnalysis),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "The report could not be generated.");
    }
    const blob = await response.blob();
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = "career-lens-report.pdf";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    status.textContent = error.message;
    status.style.display = "block";
  } finally {
    button.disabled = false;
    button.textContent = "Export report";
  }
});
