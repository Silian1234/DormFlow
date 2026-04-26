from __future__ import annotations

from functools import partial
from pathlib import Path

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget
from kivy.utils import platform

from dormflow.api_client import ApiError, DormFlowApiClient, default_api_base_url, normalize_base_url
from dormflow.api_service import RemoteDormFlowService
from dormflow.models import DutyStatus, IssueStatus, UserRole
from dormflow.services import DormFlowService
from dormflow.session import SessionStore


class RootManager(ScreenManager):
    pass


class AuthScreen(Screen):
    pass


class HomeScreen(Screen):
    pass


class DutiesScreen(Screen):
    pass


class DutyDetailScreen(Screen):
    pass


class IssuesScreen(Screen):
    pass


class IssueCreateScreen(Screen):
    pass


class IssueDetailScreen(Screen):
    pass


class AnnouncementsScreen(Screen):
    pass


class PollsScreen(Screen):
    pass


class ProfileScreen(Screen):
    pass


class HeadmanHomeScreen(Screen):
    pass


class HeadmanDutiesScreen(Screen):
    pass


class HeadmanIssuesScreen(Screen):
    pass


class HeadmanAnnouncementScreen(Screen):
    pass


class HeadmanPollScreen(Screen):
    pass


class DormFlowAppMixin:
    service: DormFlowService | RemoteDormFlowService | None = None
    session_store: SessionStore
    api_client: DormFlowApiClient | None = None
    selected_duty_id: str | None = None
    selected_issue_id: str | None = None

    _BACK_ROUTES = {
        "duties": "home",
        "duty_detail": "duties",
        "issues": "home",
        "issue_create": "issues",
        "issue_detail": "issues",
        "announcements": "home",
        "polls": "home",
        "profile": "home",
        "headman_home": "home",
        "headman_duties": "headman_home",
        "headman_issues": "headman_home",
        "headman_announcement": "headman_home",
        "headman_poll": "headman_home",
    }

    def bootstrap_session(self) -> None:
        session = self.session_store.load()
        auth_screen = self.root.get_screen("auth")
        auth_screen.ids.api_url_input.text = session.get("base_url") or default_api_base_url()
        self.server_settings_open = False
        self.set_auth_mode("login", "Введите email и пароль для входа")
        token = session.get("token")
        if not token:
            self.root.current = "auth"
            return
        self._set_auth_status("Проверяю сохраненную сессию...")
        try:
            self._start_session(session["base_url"], token, persist=False)
        except ApiError as exc:
            self.session_store.clear()
            self.service = None
            self.api_client = None
            self.root.current = "auth"
            self._set_auth_status(f"Сессия сброшена: {exc.message}")

    def set_auth_mode(self, mode: str, status_text: str | None = None) -> None:
        if mode not in {"login", "register"}:
            return
        self.auth_mode = mode
        if status_text is None:
            status_text = (
                "Введите email и пароль для входа"
                if mode == "login"
                else "Заполните данные и создайте аккаунт"
            )
        self._set_auth_status(status_text)

    def toggle_server_settings(self) -> None:
        self.server_settings_open = not self.server_settings_open

    def submit_auth_form(self) -> None:
        if self.auth_mode == "register":
            self.register_from_form()
            return
        self.login_from_form()

    def login_from_form(self) -> None:
        screen = self.root.get_screen("auth")
        base_url = normalize_base_url(screen.ids.api_url_input.text)
        email = screen.ids.email_input.text.strip()
        password = screen.ids.password_input.text
        if not email or not password:
            self._set_auth_status("Введите email и пароль")
            return
        self._set_auth_status("Выполняю вход...")
        try:
            client = DormFlowApiClient(base_url)
            data = client.login(email, password)
            self._start_session(base_url, data["token"])
            screen.ids.password_input.text = ""
        except ApiError as exc:
            self._set_auth_status(exc.message)

    def register_from_form(self) -> None:
        screen = self.root.get_screen("auth")
        base_url = normalize_base_url(screen.ids.api_url_input.text)
        email = screen.ids.email_input.text.strip()
        password = screen.ids.password_input.text
        name = screen.ids.name_input.text.strip()
        building = screen.ids.building_input.text.strip()
        floor = screen.ids.floor_input.text.strip()
        room = screen.ids.room_input.text.strip()
        headman_code = screen.ids.headman_code_input.text.strip()
        if not all([email, password, name, building, floor, room]):
            self._set_auth_status("Для регистрации заполните email, пароль, ФИО, корпус, этаж и комнату")
            return
        self._set_auth_status("Создаю аккаунт...")
        try:
            client = DormFlowApiClient(base_url)
            data = client.register(
                email=email,
                password=password,
                name=name,
                building=building,
                floor=floor,
                room=room,
                headman_code=headman_code,
            )
            self._start_session(base_url, data["token"])
            screen.ids.password_input.text = ""
            screen.ids.headman_code_input.text = ""
        except ApiError as exc:
            self._set_auth_status(exc.message)

    def logout(self) -> None:
        if self.api_client is not None and self.api_client.token:
            try:
                self.api_client.logout()
            except ApiError:
                pass
        base_url = self.api_client.base_url if self.api_client is not None else default_api_base_url()
        self.session_store.clear()
        self.service = None
        self.api_client = None
        screen = self.root.get_screen("auth")
        screen.ids.api_url_input.text = base_url
        self.set_auth_mode("login", "Вы вышли. Для продолжения войдите в аккаунт")
        self.root.current = "auth"

    def _start_session(self, base_url: str, token: str, *, persist: bool = True) -> None:
        client = DormFlowApiClient(base_url, token)
        service = RemoteDormFlowService(client)
        self.api_client = client
        self.service = service
        if persist:
            self.session_store.save(base_url, token)
        self.root.current = "home"
        self.refresh_all()
        self._set_auth_status("")

    def _set_auth_status(self, message: str) -> None:
        if self.root is None or not self.root.has_screen("auth"):
            return
        self.root.get_screen("auth").ids.auth_status_label.text = message

    def _require_service(self) -> DormFlowService | RemoteDormFlowService | None:
        if self.service is None:
            self.root.current = "auth"
            self._set_auth_status("Сначала войдите в аккаунт")
            return None
        return self.service

    def _run_api_action(self, action, default=None):
        try:
            return action()
        except PermissionError as exc:
            self._notify(str(exc))
        except ApiError as exc:
            if exc.status_code == 401:
                self.session_store.clear()
                self.service = None
                self.api_client = None
                self.root.current = "auth"
                self._set_auth_status("Сессия истекла. Войдите снова")
            else:
                self._notify(exc.message)
        return default

    def nav(self, screen_name: str) -> None:
        if screen_name != "auth" and self.service is None:
            self.root.current = "auth"
            self._set_auth_status("Сначала войдите в аккаунт")
            return
        service = self._require_service() if screen_name != "auth" else None
        if screen_name.startswith("headman_") and service is not None and service.get_profile().role != UserRole.HEADMAN:
            self._notify("Доступно только в режиме старосты")
            return
        self.root.current = screen_name
        if screen_name == "duties":
            self.refresh_duties()
        if screen_name == "issues":
            self.refresh_issues()
        if screen_name == "announcements":
            self.refresh_announcements()
        if screen_name == "polls":
            self.refresh_polls()
        if screen_name == "headman_issues":
            self.refresh_headman_issues()

    def refresh_all(self) -> None:
        if self.service is None:
            return
        if isinstance(self.service, RemoteDormFlowService):
            result = self._run_api_action(self.service.refresh, default=False)
            if result is False:
                return
        self.refresh_home()
        self.refresh_profile()
        self.refresh_duties()
        self.refresh_issues()
        self.refresh_announcements()
        self.refresh_polls()
        self.refresh_headman_issues()

    def toggle_role(self) -> None:
        self._notify("Роль назначается сервером при регистрации. Переключение на клиенте отключено")

    def go_back(self) -> bool:
        target = self._BACK_ROUTES.get(self.root.current)
        if target is None:
            return True
        self.nav(target)
        return True

    def handle_back_key(self, key: int) -> bool:
        if key not in (27, 1001):
            return False
        return self.go_back()

    def handle_android_back(self, key: int) -> bool:
        return self.handle_back_key(key)

    def go_headman_home(self) -> None:
        service = self._require_service()
        if service is None:
            return
        if service.get_profile().role != UserRole.HEADMAN:
            self._notify("Сначала включите режим старосты")
            return
        self.nav("headman_home")

    def refresh_home(self) -> None:
        service = self._require_service()
        if service is None:
            return
        screen = self.root.get_screen("home")
        profile = service.get_profile()
        duties_pending = len([item for item in service.list_duties() if item.status == DutyStatus.PENDING])
        issues_open = len([item for item in service.list_issues() if item.status != IssueStatus.DONE])
        screen.ids.greeting_label.text = profile.name
        screen.ids.meta_label.text = f"комната {profile.room} · {profile.building}, этаж {profile.floor}"
        duties_text = self._plural_ru(duties_pending, "дежурство", "дежурства", "дежурств")
        issues_text = self._plural_ru(issues_open, "заявка", "заявки", "заявок")
        screen.ids.summary_label.text = f"В фокусе: {duties_pending} {duties_text} и {issues_open} {issues_text}"
        screen.ids.role_label.text = (
            "Режим: Староста" if profile.role == UserRole.HEADMAN else "Режим: Жилец"
        )
        screen.ids.room_chip.text = f"комната {profile.room}"
        screen.ids.logout_button.text = "Выйти из аккаунта"
        screen.ids.headman_button.disabled = profile.role != UserRole.HEADMAN

    def refresh_profile(self) -> None:
        service = self._require_service()
        if service is None:
            return
        profile = service.get_profile()
        screen = self.root.get_screen("profile")
        screen.ids.profile_name.text = profile.name
        screen.ids.profile_place.text = f"{profile.building}, этаж {profile.floor}, комната {profile.room}\n{profile.email}"
        screen.ids.profile_role.text = (
            "Староста этажа" if profile.role == UserRole.HEADMAN else "Жилец"
        )

    def refresh_duties(self) -> None:
        service = self._require_service()
        if service is None:
            return
        screen = self.root.get_screen("duties")
        container = screen.ids.duties_container
        container.clear_widgets()
        for duty in service.list_duties():
            status = "Выполнено" if duty.status == DutyStatus.DONE else "Ожидает"
            text = f"[b]{duty.title}[/b]\n{duty.date_label}\n{status}"
            button = Factory.ListCardButton(text=text, height=dp(112))
            button.bind(on_release=partial(self.open_duty, duty.duty_id))
            container.add_widget(button)

    def open_duty(self, duty_id: str, *_: Widget) -> None:
        service = self._require_service()
        if service is None:
            return
        duty = service.find_duty(duty_id)
        if duty is None:
            self._notify("Дежурство не найдено")
            return
        self.selected_duty_id = duty_id
        screen = self.root.get_screen("duty_detail")
        screen.ids.duty_title.text = duty.title
        screen.ids.duty_time.text = duty.date_label
        screen.ids.duty_scope.text = duty.room_scope
        screen.ids.duty_checklist.text = "\n".join([f"• {item}" for item in duty.checklist])
        screen.ids.duty_status.text = (
            "Статус: Выполнено" if duty.status == DutyStatus.DONE else "Статус: Ожидает выполнения"
        )
        screen.ids.duty_done_button.disabled = duty.status == DutyStatus.DONE
        self.nav("duty_detail")

    def complete_selected_duty(self) -> None:
        service = self._require_service()
        if service is None:
            return
        if not self.selected_duty_id:
            self._notify("Выберите дежурство")
            return
        if self._run_api_action(lambda: service.mark_duty_done(self.selected_duty_id), default=False):
            self.refresh_duties()
            self.open_duty(self.selected_duty_id)
            self.refresh_home()
            self._notify("Дежурство отмечено как выполненное")

    def create_duty_from_form(self) -> None:
        service = self._require_service()
        if service is None:
            return
        if service.get_profile().role != UserRole.HEADMAN:
            self._notify("График дежурств создает только староста")
            return
        screen = self.root.get_screen("headman_duties")
        title = screen.ids.duty_title_input.text.strip()
        date_label = screen.ids.duty_date_input.text.strip()
        room_scope = screen.ids.duty_scope_input.text.strip()
        raw_checklist = screen.ids.duty_checklist_input.text.strip()
        checklist = [item.strip() for item in raw_checklist.split("\n") if item.strip()]
        if not title or not date_label or not room_scope or not checklist:
            self._notify("Заполните название, время, зону и чек-лист")
            return
        created = self._run_api_action(
            lambda: service.create_duty(
                title=title,
                date_label=date_label,
                room_scope=room_scope,
                checklist=checklist,
            )
        )
        if created is None:
            return
        screen.ids.duty_title_input.text = ""
        screen.ids.duty_date_input.text = ""
        screen.ids.duty_scope_input.text = ""
        screen.ids.duty_checklist_input.text = ""
        self.refresh_duties()
        self.refresh_home()
        self._notify("Дежурство опубликовано")

    def refresh_issues(self) -> None:
        service = self._require_service()
        if service is None:
            return
        screen = self.root.get_screen("issues")
        container = screen.ids.issues_container
        container.clear_widgets()
        for issue in service.list_issues():
            status = self._issue_status_ru(issue.status)
            text = f"[b]{issue.title}[/b]\nКатегория: {issue.category} · {status}"
            button = Factory.ListCardButton(text=text)
            button.bind(on_release=partial(self.open_issue, issue.issue_id))
            container.add_widget(button)

    def open_issue(self, issue_id: str, *_: Widget) -> None:
        service = self._require_service()
        if service is None:
            return
        issue = service.find_issue(issue_id)
        if issue is None:
            self._notify("Заявка не найдена")
            return
        self.selected_issue_id = issue_id
        screen = self.root.get_screen("issue_detail")
        screen.ids.issue_title.text = issue.title
        screen.ids.issue_status.text = f"Статус: {self._issue_status_ru(issue.status)}"
        screen.ids.issue_meta.text = f"Категория: {issue.category} · Автор: {issue.created_by}"
        screen.ids.issue_description.text = issue.description
        can_moderate = service.get_profile().role == UserRole.HEADMAN
        screen.ids.issue_status_button.disabled = issue.status == IssueStatus.DONE or not can_moderate
        if issue.status == IssueStatus.NEW:
            screen.ids.issue_status_button.text = "Перевести в работу" if can_moderate else "Доступно старосте"
        elif issue.status == IssueStatus.IN_PROGRESS:
            screen.ids.issue_status_button.text = "Закрыть заявку" if can_moderate else "Доступно старосте"
        else:
            screen.ids.issue_status_button.text = "Заявка закрыта"
        self.nav("issue_detail")

    def advance_issue_status(self) -> None:
        service = self._require_service()
        if service is None:
            return
        if service.get_profile().role != UserRole.HEADMAN:
            self._notify("Статусы заявок меняет только староста")
            return
        if not self.selected_issue_id:
            self._notify("Выберите заявку")
            return
        issue = self._run_api_action(lambda: service.move_issue_status(self.selected_issue_id))
        if issue is None:
            self._notify("Заявка не найдена")
            return
        self.refresh_issues()
        self.refresh_headman_issues()
        self.refresh_home()
        self.open_issue(issue.issue_id)
        self._notify("Статус заявки обновлен")

    def create_issue_from_form(self) -> None:
        service = self._require_service()
        if service is None:
            return
        screen = self.root.get_screen("issue_create")
        title = screen.ids.issue_title_input.text.strip()
        description = screen.ids.issue_description_input.text.strip()
        category = screen.ids.issue_category_input.text.strip() or "Другое"
        if not title or not description:
            self._notify("Заполните название и описание заявки")
            return
        created = self._run_api_action(lambda: service.create_issue(title=title, description=description, category=category))
        if created is None:
            return
        screen.ids.issue_title_input.text = ""
        screen.ids.issue_description_input.text = ""
        screen.ids.issue_category_input.text = ""
        self.refresh_issues()
        self.refresh_headman_issues()
        self.refresh_home()
        self.nav("issues")
        self._notify("Заявка создана")

    def refresh_announcements(self) -> None:
        service = self._require_service()
        if service is None:
            return
        screen = self.root.get_screen("announcements")
        container = screen.ids.announcements_container
        container.clear_widgets()
        for item in service.list_announcements():
            text = f"[b]{item.title}[/b]\n{item.body}\nАвтор: {item.author}"
            container.add_widget(Factory.CardLabel(text=text, height=dp(136)))

    def create_announcement_from_form(self) -> None:
        service = self._require_service()
        if service is None:
            return
        screen = self.root.get_screen("headman_announcement")
        title = screen.ids.ann_title_input.text.strip()
        body = screen.ids.ann_body_input.text.strip()
        if not title or not body:
            self._notify("Заполните заголовок и текст объявления")
            return
        created = self._run_api_action(lambda: service.create_announcement(title=title, body=body))
        if created is None:
            return
        screen.ids.ann_title_input.text = ""
        screen.ids.ann_body_input.text = ""
        self.refresh_announcements()
        self._notify("Объявление опубликовано")

    def refresh_polls(self) -> None:
        service = self._require_service()
        if service is None:
            return
        screen = self.root.get_screen("polls")
        container = screen.ids.polls_container
        container.clear_widgets()
        polls = service.list_polls()
        if not polls:
            container.add_widget(Factory.EmptyState(text="Голосований пока нет"))
            return
        for poll in polls:
            container.add_widget(Factory.SectionLabel(text=poll.question))
            for index, option in enumerate(poll.options):
                caption = f"{option.text} ({option.votes})"
                button = Factory.PollOptionButton(text=caption)
                button.bind(on_release=partial(self.vote_poll, poll.poll_id, index))
                container.add_widget(button)

    def vote_poll(self, poll_id: str, option_index: int, *_: Widget) -> None:
        service = self._require_service()
        if service is None:
            return
        ok = self._run_api_action(lambda: service.vote(poll_id=poll_id, option_index=option_index), default=False)
        if not ok:
            self._notify("Голос уже отдан или некорректный вариант")
            return
        self.refresh_polls()
        self._notify("Голос принят")

    def create_poll_from_form(self) -> None:
        service = self._require_service()
        if service is None:
            return
        screen = self.root.get_screen("headman_poll")
        question = screen.ids.poll_question_input.text.strip()
        raw_options = screen.ids.poll_options_input.text.strip()
        options = [item.strip() for item in raw_options.split("\n") if item.strip()]
        if not question or len(options) < 2:
            self._notify("Введите вопрос и минимум 2 варианта")
            return
        try:
            created = self._run_api_action(lambda: service.create_poll(question=question, options=options))
            if created is None:
                return
        except ValueError as exc:
            self._notify(str(exc))
            return
        screen.ids.poll_question_input.text = ""
        screen.ids.poll_options_input.text = ""
        self.refresh_polls()
        self._notify("Голосование создано")

    def refresh_headman_issues(self) -> None:
        service = self._require_service()
        if service is None:
            return
        screen = self.root.get_screen("headman_issues")
        container = screen.ids.headman_issues_container
        container.clear_widgets()
        for issue in service.list_issues():
            status = self._issue_status_ru(issue.status)
            text = f"[b]{issue.title}[/b]\n{status} · {issue.room_scope}"
            button = Factory.ListCardButton(text=text)
            button.bind(on_release=partial(self.open_issue, issue.issue_id))
            container.add_widget(button)

    @staticmethod
    def _issue_status_ru(status: IssueStatus) -> str:
        mapping = {
            IssueStatus.NEW: "Новая",
            IssueStatus.IN_PROGRESS: "В работе",
            IssueStatus.DONE: "Закрыта",
        }
        return mapping[status]

    @staticmethod
    def _plural_ru(value: int, one: str, few: str, many: str) -> str:
        if value % 10 == 1 and value % 100 != 11:
            return one
        if 2 <= value % 10 <= 4 and not 12 <= value % 100 <= 14:
            return few
        return many

    @staticmethod
    def _notify(text: str) -> None:
        content = Label(text=text)
        popup = Popup(title="DormFlow", content=content, size_hint=(0.78, 0.32), auto_dismiss=True)
        popup.open()


def create_app():
    from kivy.app import App

    class DormFlowApp(App, DormFlowAppMixin):
        auth_mode = StringProperty("login")
        server_settings_open = BooleanProperty(False)

        def build(self):
            self.title = "DormFlow"
            storage_dir = Path(self.user_data_dir)
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.session_store = SessionStore(storage_dir / "session.json")
            self.service = None
            self.api_client = None
            if platform != "ios":
                Window.bind(on_keyboard=self._handle_keyboard)
            return Builder.load_file(str(Path(__file__).with_name("ui.kv")))

        def on_start(self):
            self.bootstrap_session()

        def on_pause(self):
            return True

        def on_resume(self):
            Clock.schedule_once(self._refresh_after_resume, 0.5)

        def _refresh_after_resume(self, *_):
            self.refresh_all()
            self.root.do_layout()
            self.root.canvas.ask_update()
            Window.canvas.ask_update()

        def _handle_keyboard(self, _window, key, *_args):
            return self.handle_back_key(key)

    return DormFlowApp()
