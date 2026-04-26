const app = document.getElementById("app");
const roleBadge = document.getElementById("roleBadge");

const state = {
  role: "resident",
  screen: "home",
};

function setRole(role) {
  state.role = role;
  roleBadge.textContent = role === "resident" ? "Жилец" : "Староста";
  render();
}

function nav(screen) {
  state.screen = screen;
  render();
}

function screenHome() {
  return `
    <div class="block">
      <h3>Главная</h3>
      <p class="muted">Корпус 3, этаж 4, комната 418. Сегодня есть 2 важных действия.</p>
      <div class="chip">Дежурство: завтра</div>
      <div class="chip">1 новая заявка на этаже</div>
    </div>

    <div class="row">
      <button data-nav="duties" class="primary">Мои дежурства</button>
      <button data-nav="issues" class="primary">Заявки</button>
      <button data-nav="announcements">Объявления</button>
      <button data-nav="polls">Голосования</button>
    </div>

    <div class="row" style="margin-top: 8px;">
      <button data-nav="profile">Профиль</button>
      ${
        state.role === "resident"
          ? `<button data-action="switch-role">Режим старосты</button>`
          : `<button data-nav="headman">Панель старосты</button>`
      }
    </div>
  `;
}

function screenDuties() {
  return `
    <div class="block">
      <h3>Мои дежурства</h3>
      <p class="muted">Следующее дежурство: 24 апреля, 19:00-21:00</p>
      <button data-nav="duty-details">Открыть чек-лист дежурства</button>
    </div>
    <button data-nav="home">Назад на главную</button>
  `;
}

function screenDutyDetails() {
  return `
    <div class="block">
      <h3>Чек-лист дежурства</h3>
      <p class="muted">1) Кухня 2) Коридор 3) Санузел 4) Вынос мусора</p>
      <button class="primary" data-alert="Дежурство отмечено, фото прикреплено.">Отметить выполнение + фото</button>
    </div>
    <button data-nav="duties">Назад к дежурствам</button>
  `;
}

function screenIssues() {
  return `
    <div class="block">
      <h3>Заявки</h3>
      <p>
        <span class="status status-progress">В работе</span>
        Не работает душ на 4 этаже
      </p>
      <button data-nav="issue-details">Открыть заявку</button>
    </div>
    <div class="row">
      <button class="primary" data-nav="issue-create">Создать заявку</button>
      <button data-nav="home">Назад на главную</button>
    </div>
  `;
}

function screenIssueCreate() {
  return `
    <div class="block">
      <h3>Новая заявка</h3>
      <p class="muted">Категория: Сантехника</p>
      <p class="muted">Описание: Протечка в душевой кабине №2</p>
      <button class="primary" data-alert="Заявка создана со статусом: Новая">Отправить заявку</button>
    </div>
    <button data-nav="issues">Назад к заявкам</button>
  `;
}

function screenIssueDetails() {
  return `
    <div class="block">
      <h3>Детали заявки #214</h3>
      <p><span class="status status-progress">В работе</span></p>
      <p class="muted">Ответственный: комендант корпуса</p>
      <p class="muted">Последнее обновление: сегодня, 12:40</p>
    </div>
    <button data-nav="issues">Назад к заявкам</button>
  `;
}

function screenAnnouncements() {
  return `
    <div class="block">
      <h3>Объявления</h3>
      <p><strong>Важно:</strong> 25 апреля отключение воды с 14:00 до 18:00.</p>
      <p class="muted">Опубликовано комендантом.</p>
    </div>
    <button data-nav="home">Назад на главную</button>
  `;
}

function screenPolls() {
  return `
    <div class="block">
      <h3>Голосования</h3>
      <p>Покупаем микроволновку в общую кухню?</p>
      <div class="row">
        <button data-alert="Голос 'За' отправлен">За</button>
        <button data-alert="Голос 'Против' отправлен">Против</button>
      </div>
    </div>
    <button data-nav="home">Назад на главную</button>
  `;
}

function screenProfile() {
  return `
    <div class="block">
      <h3>Профиль</h3>
      <p class="muted">Иван Иванов, комната 418</p>
      <p class="muted">Уведомления: включены</p>
      <button data-action="switch-role">Режим старосты</button>
    </div>
    <button data-nav="home">Назад на главную</button>
  `;
}

function screenHeadman() {
  return `
    <div class="block">
      <h3>Панель старосты</h3>
      <p class="muted">Управление только по вашему этажу</p>
    </div>
    <div class="row">
      <button data-nav="headman-duty">График дежурств</button>
      <button data-nav="headman-issues">Модерация заявок</button>
      <button data-nav="headman-ann">Создать объявление</button>
      <button data-nav="headman-poll">Создать голосование</button>
    </div>
    <div style="margin-top: 8px;">
      <button data-action="switch-to-resident">Вернуться в режим жильца</button>
    </div>
  `;
}

function screenHeadmanDuty() {
  return `
    <div class="block">
      <h3>График дежурств этажа</h3>
      <p class="muted">Пн: 411, Вт: 412, Ср: 413, Чт: 414, Пт: 415</p>
      <button class="primary" data-alert="График обновлен и отправлен жильцам">Сохранить и разослать</button>
    </div>
    <button data-nav="headman">Назад в панель старосты</button>
  `;
}

function screenHeadmanIssues() {
  return `
    <div class="block">
      <h3>Модерация заявок</h3>
      <p><span class="status status-new">Новая</span> Перегорела лампа в коридоре</p>
      <div class="row">
        <button data-alert="Назначено в работу">Взять в работу</button>
        <button data-alert="Отклонено с комментарием">Отклонить</button>
      </div>
    </div>
    <button data-nav="headman">Назад в панель старосты</button>
  `;
}

function screenHeadmanAnnouncement() {
  return `
    <div class="block">
      <h3>Новое объявление</h3>
      <p class="muted">Текст: Проверка пожарной безопасности в 20:00</p>
      <button class="primary" data-alert="Объявление опубликовано">Опубликовать</button>
    </div>
    <button data-nav="headman">Назад в панель старосты</button>
  `;
}

function screenHeadmanPoll() {
  return `
    <div class="block">
      <h3>Новое голосование</h3>
      <p class="muted">Вопрос: Нужен ли кулер на этаже?</p>
      <button class="primary" data-alert="Голосование создано">Создать</button>
    </div>
    <button data-nav="headman">Назад в панель старосты</button>
  `;
}

function getScreenHtml() {
  switch (state.screen) {
    case "duties":
      return screenDuties();
    case "duty-details":
      return screenDutyDetails();
    case "issues":
      return screenIssues();
    case "issue-create":
      return screenIssueCreate();
    case "issue-details":
      return screenIssueDetails();
    case "announcements":
      return screenAnnouncements();
    case "polls":
      return screenPolls();
    case "profile":
      return screenProfile();
    case "headman":
      return screenHeadman();
    case "headman-duty":
      return screenHeadmanDuty();
    case "headman-issues":
      return screenHeadmanIssues();
    case "headman-ann":
      return screenHeadmanAnnouncement();
    case "headman-poll":
      return screenHeadmanPoll();
    case "home":
    default:
      return screenHome();
  }
}

function bindEvents() {
  app.querySelectorAll("[data-nav]").forEach((button) => {
    button.addEventListener("click", () => nav(button.dataset.nav));
  });

  app.querySelectorAll("[data-alert]").forEach((button) => {
    button.addEventListener("click", () => {
      alert(button.dataset.alert);
    });
  });

  app.querySelectorAll("[data-action='switch-role']").forEach((button) => {
    button.addEventListener("click", () => {
      setRole("headman");
      nav("headman");
    });
  });

  app.querySelectorAll("[data-action='switch-to-resident']").forEach((button) => {
    button.addEventListener("click", () => {
      setRole("resident");
      nav("home");
    });
  });
}

function render() {
  app.innerHTML = getScreenHtml();
  bindEvents();
}

render();
