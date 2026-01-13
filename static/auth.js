/* ---------- REGISTER ---------- */
function register() {
  const user = document.getElementById("regUser").value.trim();
  const pass = document.getElementById("regPass").value.trim();
  const msg = document.getElementById("msg");

  if (user === "" || pass === "") {
    msg.innerText = "All fields are required!";
    msg.style.color = "red";
    return;
  }

  localStorage.setItem("tg_user", user);
  localStorage.setItem("tg_pass", pass);

  msg.style.color = "green";
  msg.innerText = "Registration successful! Redirecting...";

  setTimeout(() => {
    window.location.href = "/index";
  }, 1200);
}

/* ---------- LOGIN ---------- */
function login() {
  const user = document.getElementById("loginUser").value.trim();
  const pass = document.getElementById("loginPass").value.trim();
  const msg = document.getElementById("msg");

  const savedUser = localStorage.getItem("tg_user");
  const savedPass = localStorage.getItem("tg_pass");

  if (user === savedUser && pass === savedPass) {
    localStorage.setItem("tg_loggedIn", "true");
    window.location.href = "/dashboard";
  } else {
    msg.innerText = "Invalid username or password!";
    msg.style.color = "red";
  }
}


function togglePassword(btn) {
    const input = btn.previousElementSibling;

    if (input.type === "password") {
        input.type = "text";
        btn.textContent = "Hide";
    } else {
        input.type = "password";
        btn.textContent = "Show";
    }
}



/* ---------- SESSION CHECK ---------- */
function checkAuth() {
  const isLoggedIn = localStorage.getItem("tg_loggedIn");
  if (isLoggedIn !== "true") {
    window.location.href = "/index";
  }
}

/* ---------- LOGOUT ---------- */
function logout() {
  localStorage.removeItem("tg_loggedIn");
  window.location.href = "/index";
}

function goChatBot() {
  window.location.href = "/chatbot";
}