const SUPABASE_URL = 'https://твой-проект.supabase.co';  // Замени на свой из Supabase
const SUPABASE_ANON_KEY = 'твой-anon-key';  // Из Supabase

let token = localStorage.getItem('token');
let groupId = null;

// Инициализация Supabase SDK в браузере
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Проверяем токен из URL после OAuth
function checkOAuthCallback() {
  const hash = window.location.hash.substring(1);
  if (hash) {
    const params = new URLSearchParams(hash);
    token = params.get('access_token');
    if (token) {
      localStorage.setItem('token', token);
      // Удаляем hash из URL
      window.history.replaceState({}, document.title, window.location.pathname);
      // Обновляем UI
      updateUI();
    }
  }
}

// Обновляем UI в зависимости от токена
function updateUI() {
  if (token) {
    document.getElementById("login").style.display = "none";
    document.getElementById("app").style.display = "block";
    loadParticipants();  // Если группа уже есть
  } else {
    document.getElementById("login").style.display = "block";
    document.getElementById("app").style.display = "none";
  }
}

// Логин через Google
async function login() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.origin  // Редирект обратно на этот сайт
    }
  });
  if (error) alert(error.message);
}

// Создать группу
async function createGroup() {
  const name = document.getElementById("group-name").value;
  const res = await fetch("/create-group", {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/x-www-form-urlencoded" },
    body: `name=${encodeURIComponent(name)}`
  });
  if (res.ok) {
    const data = await res.json();
    groupId = data.group_id;
    showGroup();
  } else {
    alert("Ошибка создания группы");
  }
}

// Показать группу
function showGroup() {
  document.getElementById("create").style.display = "none";
  document.getElementById("group").style.display = "block";
  document.getElementById("group-title").textContent = document.getElementById("group-name").value;
  document.getElementById("share-link").textContent = window.location.origin + "/group/" + groupId;
  loadParticipants();
}

// Добавить участника
async function addParticipant() {
  const name = document.getElementById("p-name").value;
  const email = document.getElementById("p-email").value;
  const res = await fetch("/add-participant", {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/x-www-form-urlencoded" },
    body: `group_id=${groupId}&name=${encodeURIComponent(name)}&email=${encodeURIComponent(email)}`
  });
  if (res.ok) {
    document.getElementById("p-name").value = "";
    document.getElementById("p-email").value = "";
    loadParticipants();
  } else {
    alert("Ошибка добавления участника");
  }
}

// Загрузить участников
async function loadParticipants() {
  const res = await fetch(`/group/${groupId}`);
  if (res.ok) {
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
}

// Запустить жеребьёвку
async function launch() {
  const res = await fetch(`/launch/${groupId}`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (res.ok) {
    alert("Тайный Санта запущен! Письма отправлены.");
    loadParticipants();  // Обновить список
  } else {
    alert("Ошибка запуска");
  }
}

// Инициализация
checkOAuthCallback();
updateUI();

// Слушатель на изменения auth (для Supabase SDK)
supabase.auth.onAuthStateChange((event, session) => {
  if (session) {
    token = session.access_token;
    localStorage.setItem('token', token);
    updateUI();
  } else {
    token = null;
    localStorage.removeItem('token');
    updateUI();
  }
});
