let token = null;
let groupId = null;

async function login() {
  const auth = window.supabase.auth;
  const { data, error } = await auth.signInWithOAuth({ provider: 'google' });
  if (error) alert(error.message);
}

window.supabase.auth.onAuthStateChange((event, session) => {
  if (session) {
    token = session.access_token;
    document.getElementById("login").style.display = "none";
    document.getElementById("app").style.display = "block";
  }
});

async function createGroup() {
  const name = document.getElementById("group-name").value;
  const res = await fetch("/create-group", {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/x-www-form-urlencoded" },
    body: `name=${encodeURIComponent(name)}`
  });
  const data = await res.json();
  groupId = data.group_id;
  showGroup();
}

function showGroup() {
  document.getElementById("create").style.display = "none";
  document.getElementById("group").style.display = "block";
  document.getElementById("group-title").textContent = document.getElementById("group-name").value;
  document.getElementById("share-link").textContent = location.href + "group/" + groupId;
  loadParticipants();
}

async function addParticipant() {
  const name = document.getElementById("p-name").value;
  const email = document.getElementById("p-email").value;
  await fetch("/add-participant", {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/x-www-form-urlencoded" },
    body: `group_id=${groupId}&name=${name}&email=${email}`
  });
  document.getElementById("p-name").value = "";
  document.getElementById("p-email").value = "";
  loadParticipants();
}

async function loadParticipants() {
  const res = await fetch(`/group/${groupId}`);
  const data = await res.json();
  const list = document.getElementById("participants");
  list.innerHTML = "";
  data.participants.forEach(p => {
    const li = document.createElement("li");
    li.textContent = `${p.name} (${p.email})`;
    if (p.target_id) li.textContent += ` → ???`;
    list.appendChild(li);
  });
  document.getElementById("launch-btn").style.display = data.participants.length >= 3 ? "block" : "none";
}

async function launch() {
  await fetch(`/launch/${groupId}`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}` }
  });
  alert("Тайный Санта запущен! Письма отправлены.");
}