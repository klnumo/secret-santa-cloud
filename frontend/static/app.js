// Простая проверка email на клиенте (необязательно)
function validateEmail(email) {
  return email.includes("@") && email.split("@")[1].includes(".");
}

// Пример для формы (если хочешь)
document.addEventListener("DOMContentLoaded", () => {
  const forms = document.querySelectorAll("form");
  forms.forEach(form => {
    form.addEventListener("submit", (e) => {
      const email = form.querySelector('input[type="email"]');
      if (email && !validateEmail(email.value)) {
        e.preventDefault();
        alert("Email должен содержать @ и точку!");
      }
    });
  });
});