/* ---------- LOADING HELPERS ---------- */
function startLoading(buttonId) {
  const btn = document.getElementById(buttonId);
  if (!btn) return;

  const text = btn.querySelector(".btn-text");
  const loader = btn.querySelector(".loader");

  if (text) text.classList.add("hidden");
  if (loader) loader.classList.remove("hidden");

  btn.disabled = true;
}

function stopLoading(buttonId) {
  const btn = document.getElementById(buttonId);
  if (!btn) return;

  const text = btn.querySelector(".btn-text");
  const loader = btn.querySelector(".loader");

  if (text) text.classList.remove("hidden");
  if (loader) loader.classList.add("hidden");

  btn.disabled = false;
}




/* ---------- INIT ---------- */
function loadSubjects() {
  const subjects = JSON.parse(localStorage.getItem("subjects")) || [];
  const faculty = JSON.parse(localStorage.getItem("faculty")) || [];
  const list = document.getElementById("subjectList");

  document.getElementById("facultyCount").innerText = faculty.length;
  document.getElementById("subjectCount").innerText = subjects.length;

  list.innerHTML = "";

  subjects.forEach((s, i) => {
    const div = document.createElement("div");
    div.className = "subject-row";

    div.innerHTML = `
      <div>
        <strong>${s.subject}</strong><br>
        Faculty:
        ${
          s.faculty.length > 0
            ? s.faculty.join(", ")
            : "Not Assigned"
        }
      </div>
      <div>
        <button>Assign</button>
        <button class="danger-small">🗑️</button>
      </div>
    `;

    // Assign faculty (MULTIPLE allowed)
    div.querySelector("button").onclick = () => showFaculty(i);

    // Delete subject
    div.querySelector(".danger-small").onclick = () => deleteSubject(i);

    list.appendChild(div);
  });
}

/* ---------- FACULTY ---------- */
function addFaculty() {
  const name = document.getElementById("facultyInput").value.trim();  // Assuming ID is "facultyInput"
  if (!name) return;

  let faculty = JSON.parse(localStorage.getItem("faculty")) || [];
  if (!faculty.includes(name)) faculty.push(name);

  localStorage.setItem("faculty", JSON.stringify(faculty));
  document.getElementById("facultyInput").value = "";
  loadSubjects();
}

function addFacultyFromURL() {
  const url = document.getElementById("URLInput").value.trim();  // Assuming ID is "URLInput"
  if (!url) return;

  startLoading("facultyImportBtn");

  fetch("/api/faculty", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  })
    .then(r => r.json())
    .then(data => {
      let faculty = JSON.parse(localStorage.getItem("faculty")) || [];
      data.forEach(f => {
        if (!faculty.includes(f)) faculty.push(f);
      });
      localStorage.setItem("faculty", JSON.stringify(faculty));
      loadSubjects();
    })
    .catch(err => {
      console.error(err);
      alert("Failed to import faculty");
    })
    .finally(() => stopLoading("facultyImportBtn"));
}

/* ---------- SUBJECT ---------- */
function addSubject() {
  const name = document.getElementById("subjectInput").value.trim();  // Assuming ID is "subjectInput"
  if (!name) return;

  let subjects = JSON.parse(localStorage.getItem("subjects")) || [];
  subjects.push({
    subject: name,
    faculty: [],  // Array for multiple faculty
    theory: 0,    // Hours (will be sent as theory_hours)
    practical: 0, // Hours (will be sent as practical_hours)
    tutorial: 0   // Hours (will be sent as tutorial_hours)
  });

  localStorage.setItem("subjects", JSON.stringify(subjects));
  document.getElementById("subjectInput").value = "";
  loadSubjects();
}

function addSubjectsFromPDF() {
  const file = document.getElementById("PDFInput").files[0];  // Assuming ID is "PDFInput"
  if (!file) return;

  startLoading("subjectImportBtn");

  const fd = new FormData();
  fd.append("pdf", file);

  fetch("/api/syllabus-upload", {
    method: "POST",
    body: fd
  })
    .then(r => r.json())
    .then(data => {
      localStorage.setItem("syllabusRaw", JSON.stringify(data));

      let subjects = JSON.parse(localStorage.getItem("subjects")) || [];

      data.forEach(s => {
        const name =
          typeof s === "string"
            ? s
            : s.name || s.subject || s[0];

        if (!name) return;

        if (!subjects.some(x => x.subject === name)) {
          subjects.push({
            subject: name,
            faculty: [],
            theory: s.theory || 0,      // Hours
            practical: s.practical || 0, // Hours
            tutorial: s.tutorial || 0    // Hours
          });
        }
      });

      localStorage.setItem("subjects", JSON.stringify(subjects));
      loadSubjects();
    })
    .catch(err => {
      console.error(err);
      alert("Failed to parse syllabus PDF");
    })
    .finally(() => stopLoading("subjectImportBtn"));
}

/* ---------- ASSIGN FACULTY ---------- */
function showFaculty(index) {
  const faculty = JSON.parse(localStorage.getItem("faculty")) || [];
  const select = document.createElement("select");

  select.innerHTML =
    `<option value="">Select Faculty</option>` +
    faculty.map(f => `<option value="${f}">${f}</option>`).join("");

  select.onchange = function () {
    if (!this.value) return;
    assignFaculty(index, this.value);
    this.remove();
  };

  document
    .getElementById("subjectList")
    .children[index]
    .appendChild(select);
}

function assignFaculty(index, name) {
  let subjects = JSON.parse(localStorage.getItem("subjects")) || [];

  if (!subjects[index].faculty.includes(name)) {
    subjects[index].faculty.push(name);
  }

  localStorage.setItem("subjects", JSON.stringify(subjects));
  loadSubjects();
}

/* ---------- DELETE SUBJECT ---------- */
function deleteSubject(index) {
  if (!confirm("Delete this subject?")) return;

  let subjects = JSON.parse(localStorage.getItem("subjects")) || [];
  subjects.splice(index, 1);

  localStorage.setItem("subjects", JSON.stringify(subjects));
  loadSubjects();
}

/* ---------- UTILS ---------- */
function clearAllData() {
  localStorage.clear();
  loadSubjects();
}

function goBack() {
  window.location.href = "/dashboard";
}

window.onload = loadSubjects;

/* ---------- SEND TO BACKEND ---------- */
/* ---------- SEND TO BACKEND ---------- */
function sendDataToBackend() {
  const subjectsUI = JSON.parse(localStorage.getItem("subjects")) || [];
  const syllabusRaw = JSON.parse(localStorage.getItem("syllabusRaw")) || [];
  const config = JSON.parse(localStorage.getItem("timetableConfig"));

  if (!config) {
    alert("Timetable configuration missing");
    return;
  }

  // Filter out subjects with no faculty (skip them entirely, no alert)
  const validSubjectsUI = subjectsUI.filter(s => s.faculty.length > 0);

  // Check for subjects with no hours (still alert, as hours are required)
  const invalidSubjects = validSubjectsUI.filter(s => s.theory_hours === 0 && s.practical_hours === 0 && s.tutorial_hours === 0);
  if (invalidSubjects.length > 0) {
    alert(`Some subjects have no hours assigned (theory, practical, or tutorial): ${invalidSubjects.map(s => s.subject).join(", ")}. Please assign hours before sending.`);
    return;
  }

  const payload = {
    timetableConfig: {
      startTime: config.startTime,
      endTime: config.endTime,
      noOfDiv: config.noOfDiv,
      workingDays: config.workingDays,
      lectureDuration: config.lectureDuration,
      practicalDuration: config.practicalDuration,
      labCount: config.labCount,
     practicalBatches: config.practicalBatches || 1,
      lunchBreak: config.lunchBreak,
      shortBreak: config.shortBreak,
      shortBreakCount: config.shortBreakCount,
      periodsPerDay: config.periodsPerDay
    },

    subjects: validSubjectsUI.map(ui => {
      const raw =
        syllabusRaw.find(
          r => (r.name || r.subject || r[0]) === ui.subject
        ) || {};

      return {
        subject: ui.subject,
        faculty: ui.faculty,  // Array of faculty names

        // Send hours (backend converts to periods)
        theory_hours: raw.theory_hours ?? 0,
      practical_hours: raw.practical_hours ?? 0,
      tutorial_hours: raw.tutorial_hours ?? 0
      };
    })
  };

  fetch("/api/process-data", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload)
})
  .then(res => res.json())
  .then(data => {
    console.log("Backend response:", data);

    if (data.status === "error") {
      alert(`Timetable generation failed: ${data.message}`);
      return;
    }

    if (data.redirect) {
      // THIS is the missing step
      window.location.href = data.redirect;
      return;
    }

    alert("Timetable generated, but no redirect provided.");
  })
  .catch(err => {
    console.error(err);
    alert("Failed to send data or generate timetable");
  });

}
function goChatBot() {
  window.location.href = "/chatbot";
}