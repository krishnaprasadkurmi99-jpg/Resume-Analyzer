const form = document.querySelector("#analyzer-form");
const fileInput = document.querySelector("#resume-file");
const dropzone = document.querySelector("#dropzone");
const fileName = document.querySelector("#file-name");
const resumeText = document.querySelector("#resume-text");
const toast = document.querySelector("#toast");
const content = document.querySelector("#insights-content");
const emptyInsights = document.querySelector("#insights-empty");
const exportButton = document.querySelector("#print-report");
let latestAnalysis = null;
let currentResumeText = "";
let roadmapData = null;
let toastTimer;

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
}[char]));
const asArray = (value) => Array.isArray(value) ? value : [];
const clampScore = (value) => Math.max(0, Math.min(100, Number(value) || 0));
const scoreText = (value) => value === null || value === undefined ? "N/A" : `${clampScore(value)}%`;

function notify(message, type = "error") {
  clearTimeout(toastTimer);
  toast.textContent = message;
  toast.classList.toggle("success", type === "success");
  toast.classList.add("visible");
  toastTimer = setTimeout(() => toast.classList.remove("visible"), 4500);
}

async function requestJson(url, options) {
  const response = await fetch(url, options);
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The server returned an unreadable response. Please try again.");
  }
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg).join("; ")
      : data.detail;
    throw new Error(detail || "The request could not be completed.");
  }
  return data;
}

function setLoading(button, loading, label) {
  if (loading) {
    button.dataset.originalLabel = button.innerHTML;
    button.disabled = true;
    button.innerHTML = `<span class="loading-label">${escapeHtml(label)}</span><span class="loading-dots" aria-hidden="true">···</span>`;
  } else {
    button.disabled = false;
    button.innerHTML = button.dataset.originalLabel || label;
    delete button.dataset.originalLabel;
  }
}

function renderBars(items, kind = "metric") {
  return asArray(items).map((item) => {
    const score = item.score;
    const shown = scoreText(score);
    const width = score === null || score === undefined ? 0 : clampScore(score);
    const label = escapeHtml(item.name);
    const detail = item.evidence ? `<p class="metric-evidence">${escapeHtml(item.evidence)}</p>` : "";
    return `<div class="${kind === "metric" ? "metric-row" : "category-row"}">
      <span class="metric-label">${label}</span>
      <span class="bar-track" aria-label="${label}: ${shown}"><span class="bar-fill" style="width:${width}%"></span></span>
      <span class="metric-value">${shown}</span>${detail}
    </div>`;
  }).join("");
}

function renderList(items) {
  const values = asArray(items);
  if (!values.length) return "<li>No items detected.</li>";
  return values.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderRoles(roles) {
  const values = asArray(roles);
  if (!values.length) return '<p class="micro-copy">No role recommendations are available.</p>';
  return values.map((role) => `<div class="role-item">
    <div class="role-topline"><span>${escapeHtml(role.role)}</span><span class="role-score">${clampScore(role.suitability_score)}% skill coverage</span></div>
    <div class="bar-track"><span class="bar-fill" style="width:${clampScore(role.suitability_score)}%"></span></div>
    <p>${escapeHtml(role.reason)}</p>
  </div>`).join("");
}

function renderIntelligence(data) {
  latestAnalysis = data.analysis;
  roadmapData = data.roadmap;
  window.careerQuestions = asArray(data.interview_questions);
  currentResumeText = resumeText.value.trim();
  emptyInsights.hidden = true;
  content.hidden = false;
  exportButton.disabled = false;
  document.querySelector("#match-button").disabled = false;
  document.querySelector("#generate-interview").disabled = false;
  document.querySelector("#resume-summary").textContent = data.analysis.resume_summary;
  document.querySelector("#dna-note").textContent = data.career_dna.interpretation;
  document.querySelector("#dna-bars").innerHTML = renderBars(data.career_dna.indicators);
  document.querySelector("#skill-chips").innerHTML = [
    ...asArray(data.career_dna.technical_skills).map((skill) => `<span class="skill-chip">${escapeHtml(skill)}</span>`),
    ...asArray(data.career_dna.soft_skills).map((skill) => `<span class="skill-chip soft-chip">${escapeHtml(skill)}</span>`),
  ].join("") || '<span class="micro-copy">No catalogued skills detected in this resume text.</span>';
  document.querySelector("#strength-list").innerHTML = renderList(data.career_dna.strengths);

  document.querySelector("#ats-score").textContent = `${clampScore(data.ats.score)}%`;
  document.querySelector("#ats-disclaimer").textContent = data.ats.disclaimer;
  document.querySelector("#ats-bars").innerHTML = renderBars(data.ats.categories, "category");
  document.querySelector("#ats-deductions").innerHTML = asArray(data.ats.deductions).map((item) => `<li><strong>${item.points} points · ${escapeHtml(item.category)}:</strong> ${escapeHtml(item.reason)}<em>${escapeHtml(item.improvement)}</em></li>`).join("") || "<li>No checklist points were deducted.</li>";

  document.querySelector("#readiness-score").textContent = `${clampScore(data.readiness.score)}%`;
  document.querySelector("#readiness-formula").textContent = data.readiness.formula;
  document.querySelector("#readiness-bars").innerHTML = renderBars(data.readiness.categories, "category");
  document.querySelector("#readiness-strengths").innerHTML = renderList(data.readiness.strengths);
  document.querySelector("#readiness-weaknesses").innerHTML = renderList(data.readiness.weaknesses);
  document.querySelector("#readiness-priorities").innerHTML = renderList(data.readiness.priorities);
  document.querySelector("#readiness-disclaimer").textContent = data.readiness.disclaimer;
  document.querySelector("#role-list").innerHTML = renderRoles(data.analysis.job_recommendations);
  document.querySelector("#skill-gap-list").innerHTML = asArray(data.analysis.missing_skills).map((item) => `<div class="role-item"><div class="role-topline"><span>${escapeHtml(item.skill)}</span><span class="role-score">${escapeHtml(item.priority)}</span></div><p>${escapeHtml(item.reason)}</p></div>`).join("") || '<p class="micro-copy">No role-specific skill gaps detected. Choose a target role for a focused comparison.</p>';
  document.querySelector("#resume-improvements").innerHTML = asArray(data.analysis.resume_improvements).map((item) => `<div class="role-item"><div class="role-topline"><span>${escapeHtml(item.section)}</span></div><p>${escapeHtml(item.issue)}</p><p><b>Try:</b> ${escapeHtml(item.suggestion)}</p></div>`).join("") || '<p class="micro-copy">No resume suggestions are available.</p>';
  document.querySelector("#interview-content").innerHTML = "";
  document.querySelector("#roadmap-content").innerHTML = renderRoadmap(data.roadmap, "days_30");
  document.querySelector("#match-result").innerHTML = '<div class="empty-feature"><span class="panel-icon violet-icon">⌕</span><h3>Find your overlap</h3><p>Your match will show detected skills, related experience, keyword overlap, and role-specific next steps.</p></div>';
  document.querySelector("#match-button").disabled = false;
  document.querySelector("#insights").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderRoadmap(data, selected) {
  if (!data) return '<p class="tool-empty">Analyze a resume to build a role-focused roadmap.</p>';
  const period = data[selected];
  const milestones = asArray(period?.milestones);
  return `<div class="roadmap-tabs" role="tablist" aria-label="Roadmap duration">
    <button class="roadmap-tab ${selected === "days_30" ? "active" : ""}" type="button" data-period="days_30" role="tab" aria-selected="${selected === "days_30"}">30 days</button>
    <button class="roadmap-tab ${selected === "days_60" ? "active" : ""}" type="button" data-period="days_60" role="tab" aria-selected="${selected === "days_60"}">60 days</button>
    <button class="roadmap-tab ${selected === "days_90" ? "active" : ""}" type="button" data-period="days_90" role="tab" aria-selected="${selected === "days_90"}">90 days</button>
  </div>
  <p class="roadmap-focus">${escapeHtml(period?.focus || "")} · ${escapeHtml(data.target_role)}</p>
  ${milestones.length ? milestones.map((item) => `<div class="milestone"><span class="milestone-week">WEEK ${item.week}</span><p><strong>${escapeHtml(item.focus)}</strong> — ${escapeHtml(item.task)}</p></div>`).join("") : '<p class="micro-copy">No milestones are available for this period.</p>'}
  <div class="roadmap-extra"><strong>Suggested learning topics</strong>${asArray(data.learning_topics).map((item) => `<p><b>${escapeHtml(item.topic)}:</b> ${asArray(item.resources).map(escapeHtml).join(" · ")}</p>`).join("") || '<p>Choose a target role to prioritize learning topics.</p>'}</div>
  <div class="roadmap-extra"><strong>Portfolio project prompts</strong>${asArray(data.portfolio_projects).map((item) => `<p>${escapeHtml(item)}</p>`).join("")}</div>
  <p class="micro-copy">${escapeHtml(data.disclaimer)}</p>`;
}

document.querySelector("#roadmap-content").addEventListener("click", (event) => {
  const button = event.target.closest("[data-period]");
  if (button && roadmapData) {
    document.querySelector("#roadmap-content").innerHTML = renderRoadmap(roadmapData, button.dataset.period);
  }
});

document.querySelector("#char-count").textContent = `${resumeText.value.length.toLocaleString()} / 50,000`;
resumeText.addEventListener("input", () => {
  if (fileInput.files.length) {
    fileInput.value = "";
    fileName.textContent = "";
  }
  document.querySelector("#char-count").textContent = `${resumeText.value.length.toLocaleString()} / 50,000`;
});
fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "";
});
["dragover", "dragenter"].forEach((eventName) => dropzone.addEventListener(eventName, (event) => {
  event.preventDefault();
  dropzone.classList.add("active");
}));
["dragleave", "drop"].forEach((eventName) => dropzone.addEventListener(eventName, (event) => {
  event.preventDefault();
  dropzone.classList.remove("active");
}));
dropzone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (!file) return;
  if (!/\.(pdf|docx)$/i.test(file.name)) {
    notify("Choose a PDF or DOCX resume.");
    return;
  }
  const transfer = new DataTransfer();
  transfer.items.add(file);
  fileInput.files = transfer.files;
  fileName.textContent = file.name;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = resumeText.value.trim();
  const file = fileInput.files[0];
  if (!file && text.length < 50) {
    notify("Upload a PDF/DOCX or paste at least 50 characters of resume text.");
    return;
  }
  const role = document.querySelector("#target-role").value;
  const button = form.querySelector('button[type="submit"]');
  setLoading(button, true, "Analyzing resume");
  document.querySelector("#insights-empty").innerHTML = '<span class="empty-art">✦</span><h3>Reading your resume evidence</h3><div class="skeleton" style="width:min(360px,75vw)"></div><div class="skeleton" style="width:min(260px,60vw)"></div>';
  try {
    let response;
    if (file) {
      const body = new FormData();
      body.append("file", file);
      if (role) body.append("target_role", role);
      response = await requestJson("/api/intelligence/file", { method: "POST", body });
      currentResumeText = "";
    } else {
      currentResumeText = text;
      response = await requestJson("/api/intelligence", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: text, target_role: role || null }),
      });
    }
    renderIntelligence(response);
    notify("Resume analysis is ready.", "success");
  } catch (error) {
    document.querySelector("#insights-empty").innerHTML = '<span class="empty-art">✧</span><h3>Your insights will take shape here</h3><p>Analyze a resume to see evidence-based career insights.</p><a class="text-link" href="#resume">Try again <span>→</span></a>';
    emptyInsights.hidden = false;
    content.hidden = true;
    notify(error.message);
  } finally {
    setLoading(button, false, "Analyze my resume");
  }
});

document.querySelector("#match-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!latestAnalysis) {
    notify("Analyze your resume before comparing it with a job description.");
    return;
  }
  const description = document.querySelector("#job-description").value.trim();
  if (description.length < 50) {
    notify("Paste at least 50 characters from the job description.");
    return;
  }
  const button = document.querySelector("#match-button");
  setLoading(button, true, "Comparing text");
  try {
    let result;
    const file = fileInput.files[0];
    if (file) {
      const body = new FormData();
      body.append("file", file);
      body.append("job_description", description);
      result = await requestJson("/api/job-match/file", { method: "POST", body });
    } else {
      result = await requestJson("/api/job-match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: currentResumeText, job_description: description }),
      });
    }
    renderMatch(result);
  } catch (error) {
    notify(error.message);
  } finally {
    setLoading(button, false, "Compare with this role");
  }
});

function renderMatch(data) {
  const result = document.querySelector("#match-result");
  result.innerHTML = `<div class="match-scoreline"><span class="match-score">${clampScore(data.score)}%</span><div><h3>Text compatibility</h3><p>${escapeHtml(data.mode)} · not a hiring prediction</p></div></div>
    <div class="bar-track"><span class="bar-fill" style="width:${clampScore(data.score)}%"></span></div>
    <div class="result-section"><strong>Matching skills</strong><div class="chip-list">${asArray(data.matched_skills).map((skill) => `<span class="skill-chip soft-chip">${escapeHtml(skill)}</span>`).join("") || '<span class="micro-copy">No catalogued skill overlap detected.</span>'}</div></div>
    <div class="result-section"><strong>Missing listed skills</strong><div class="chip-list">${asArray(data.missing_skills).map((skill) => `<span class="skill-chip">${escapeHtml(skill)}</span>`).join("") || '<span class="micro-copy">No missing catalogued skills detected.</span>'}</div></div>
    <div class="result-section"><strong>Relevant resume evidence</strong><p>${asArray(data.relevant_experience.evidence).map(escapeHtml).join(" · ") || "No directly relevant experience lines detected."}</p></div>
    <div class="result-section"><strong>Keyword compatibility · ${clampScore(data.keyword_compatibility.score)}%</strong><p>${asArray(data.keyword_compatibility.matched_terms).map(escapeHtml).join(", ") || "No shared terms detected."}</p></div>
    <div class="result-section"><strong>Role-specific recommendations</strong>${asArray(data.role_recommendations).map((item) => `<p><b>${escapeHtml(item.role)}:</b> ${escapeHtml(item.recommendation)}${item.missing_skills.length ? ` Missing evidence for: ${escapeHtml(item.missing_skills.join(", "))}.` : ""}</p>`).join("")}</div>
    <div class="result-section"><strong>Suggestions</strong><ul>${renderList(data.suggestions)}</ul></div>
    <div class="result-section"><strong>How this score is calculated</strong><p>${escapeHtml(data.calculation)}</p></div>`;
}

document.querySelector("#generate-interview").addEventListener("click", () => {
  if (!latestAnalysis) {
    notify("Analyze a resume first to generate tailored questions.");
    return;
  }
  const questions = asArray(window.careerQuestions);
  if (!questions.length) {
    notify("Interview questions are unavailable. Analyze your resume again.");
    return;
  }
  document.querySelector("#interview-content").innerHTML = questions.map((item) => `<article class="question-card"><span class="question-type">${escapeHtml(item.type)}</span><strong>${escapeHtml(item.question)}</strong><p><b>Suggested structure:</b> ${escapeHtml(item.answer_structure)}</p><p>${escapeHtml(item.why)}</p></article>`).join("");
});

document.querySelector("#rewrite-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const bullet = document.querySelector("#bullet-input").value.trim();
  if (bullet.length < 10) {
    notify("Enter an existing resume bullet with at least 10 characters.");
    return;
  }
  const button = event.currentTarget.querySelector('button[type="submit"]');
  setLoading(button, true, "Refining wording");
  try {
    const result = await requestJson("/api/rewrite-bullet", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bullet }),
    });
    document.querySelector("#rewrite-result").innerHTML = `${asArray(result.versions).map((item) => `<div class="rewrite-version"><span>${escapeHtml(item.style)}</span><p>${escapeHtml(item.text)}</p></div>`).join("")}<p class="rewrite-note">${escapeHtml(result.metric_prompt)} ${escapeHtml(result.note)}</p>`;
  } catch (error) {
    notify(error.message);
  } finally {
    setLoading(button, false, "Show grounded rewrite");
  }
});

const firstFile = document.querySelector("#first-version");
const secondFile = document.querySelector("#second-version");
firstFile.addEventListener("change", () => {
  document.querySelector("#first-name").textContent = firstFile.files[0]?.name || "Choose file";
});
secondFile.addEventListener("change", () => {
  document.querySelector("#second-name").textContent = secondFile.files[0]?.name || "Choose file";
});
document.querySelector("#compare-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!firstFile.files[0] || !secondFile.files[0]) {
    notify("Select both resume versions to compare.");
    return;
  }
  const button = document.querySelector("#compare-button");
  setLoading(button, true, "Comparing versions");
  try {
    const body = new FormData();
    body.append("first_file", firstFile.files[0]);
    body.append("second_file", secondFile.files[0]);
    const result = await requestJson("/api/compare", { method: "POST", body });
    renderComparison(result);
    notify("Resume versions compared.", "success");
  } catch (error) {
    notify(error.message);
  } finally {
    setLoading(button, false, "Compare versions");
  }
});

function renderDiffPills(items, removed = false) {
  const values = asArray(items);
  return values.length
    ? `<div class="diff-pills">${values.map((item) => `<span class="diff-pill ${removed ? "removed" : ""}">${escapeHtml(item)}</span>`).join("")}</div>`
    : '<p>No detected changes.</p>';
}

function renderContentChanges(items) {
  const values = asArray(items);
  return values.length
    ? `<ul class="content-diff">${values.map((line) => `<li>${escapeHtml(line)}</li>`).join("")}</ul>`
    : "<p>No line-level text changes detected.</p>";
}

function renderComparison(data) {
  const result = document.querySelector("#compare-result");
  result.hidden = false;
  const change = Number(data.ats_change);
  const changeLabel = change > 0 ? `+${change}` : String(change);
  result.innerHTML = `<div class="compare-summary"><h3>Version comparison</h3><span class="change-score">${changeLabel} ATS checklist points</span></div>
    <div class="compare-columns"><div class="compare-column"><strong>Earlier · ${clampScore(data.first.ats_score)}%</strong><p>${data.first.characters.toLocaleString()} characters · ${asArray(data.first.sections).length} sections</p><p>Detected skills: ${asArray(data.first.skills).map(escapeHtml).join(", ") || "None"}</p></div><div class="compare-column"><strong>Updated · ${clampScore(data.second.ats_score)}%</strong><p>${data.second.characters.toLocaleString()} characters · ${asArray(data.second.sections).length} sections</p><p>Detected skills: ${asArray(data.second.skills).map(escapeHtml).join(", ") || "None"}</p></div></div>
    <div class="compare-columns"><div class="compare-column"><strong>Added skills and sections</strong>${renderDiffPills([...asArray(data.added_skills), ...asArray(data.added_sections).map((item) => `${item} section`)])}</div><div class="compare-column"><strong>Removed skills and sections</strong>${renderDiffPills([...asArray(data.removed_skills), ...asArray(data.removed_sections).map((item) => `${item} section`)], true)}</div></div>
    <div class="compare-columns"><div class="compare-column"><strong>Added content</strong>${renderContentChanges(data.added_content)}</div><div class="compare-column"><strong>Removed content</strong>${renderContentChanges(data.removed_content)}</div></div>
    <p class="micro-copy">${escapeHtml(data.summary)}</p>`;
}

exportButton.addEventListener("click", async () => {
  if (!latestAnalysis) {
    notify("Analyze a resume before exporting a report.");
    return;
  }
  exportButton.disabled = true;
  exportButton.textContent = "Preparing PDF…";
  try {
    const response = await fetch("/api/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(latestAnalysis),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "The report could not be generated.");
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "elevix-report.pdf";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    notify("PDF report downloaded.", "success");
  } catch (error) {
    notify(error.message);
  } finally {
    exportButton.disabled = false;
    exportButton.textContent = "⇩ Export PDF";
  }
});

const themeButton = document.querySelector("#theme-toggle");
function setTheme(theme) {
  document.body.dataset.theme = theme;
  const light = theme === "light";
  themeButton.setAttribute("aria-label", `Switch to ${light ? "dark" : "light"} mode`);
  document.querySelector("#theme-label").textContent = `${light ? "Dark" : "Light"} mode`;
  document.querySelector("#theme-icon").textContent = light ? "☾" : "☼";
  localStorage.setItem("elevix-theme", theme);
}
setTheme(localStorage.getItem("elevix-theme") || localStorage.getItem("careerlens-theme") || "dark");
themeButton.addEventListener("click", () => setTheme(document.body.dataset.theme === "light" ? "dark" : "light"));
document.querySelector("#settings-theme").addEventListener("click", () => themeButton.click());

const sidebar = document.querySelector("#sidebar");
const scrim = document.querySelector("#sidebar-scrim");
const menuToggle = document.querySelector("#menu-toggle");
function closeSidebar() {
  sidebar.classList.remove("open");
  scrim.hidden = true;
  menuToggle.setAttribute("aria-expanded", "false");
}
menuToggle.addEventListener("click", () => {
  const opening = !sidebar.classList.contains("open");
  sidebar.classList.toggle("open", opening);
  scrim.hidden = !opening;
  menuToggle.setAttribute("aria-expanded", String(opening));
});
scrim.addEventListener("click", closeSidebar);
document.querySelectorAll(".side-nav a, .settings-link").forEach((link) => {
  link.addEventListener("click", () => {
    document.querySelectorAll(".side-nav .nav-link").forEach((item) => item.classList.toggle("active", item === link));
    closeSidebar();
  });
});
const sectionObserver = new IntersectionObserver((entries) => {
  const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
  if (!visible) return;
  const activeHref = `#${visible.target.id}`;
  document.querySelectorAll(".side-nav .nav-link").forEach((link) => link.classList.toggle("active", link.getAttribute("href") === activeHref));
}, { rootMargin: "-15% 0px -70% 0px", threshold: [0, .1, .3] });
document.querySelectorAll("main > section[id]").forEach((section) => sectionObserver.observe(section));
