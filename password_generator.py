import tkinter as tk
from tkinter import ttk, messagebox, font
import random
import string
import json
import os
from datetime import datetime


# ───────────────────────── Константы ─────────────────────────
HISTORY_FILE = "history.json"
MIN_LENGTH   = 4
MAX_LENGTH   = 64

COLORS = {
    "bg":           "#1e1e2e",
    "sidebar":      "#181825",
    "card":         "#313244",
    "accent":       "#cba6f7",
    "accent_hover": "#b4a0e8",
    "danger":       "#f38ba8",
    "danger_hover": "#e07090",
    "success":      "#a6e3a1",
    "warning":      "#f9e2af",
    "text":         "#cdd6f4",
    "text_dim":     "#6c7086",
    "border":       "#45475a",
    "input_bg":     "#45475a",
    "green":        "#a6e3a1",
    "yellow":       "#f9e2af",
    "red":          "#f38ba8",
}

# Уровни стойкости пароля
STRENGTH_LEVELS = [
    (25,  "Очень слабый",  "#f38ba8"),
    (50,  "Слабый",        "#fab387"),
    (75,  "Средний",       "#f9e2af"),
    (90,  "Сильный",       "#a6e3a1"),
    (100, "Очень сильный", "#89dceb"),
]


# ───────────────────────── Генератор ─────────────────────────
class PasswordGenerator:
    """Логика генерации паролей и подсчёта стойкости."""

    CHAR_SETS = {
        "uppercase": string.ascii_uppercase,    # A-Z
        "lowercase": string.ascii_lowercase,    # a-z
        "digits":    string.digits,             # 0-9
        "symbols":   "!@#$%^&*()_+-=[]{}|;':\",./<>?",
    }

    def generate(
        self,
        length: int,
        use_upper: bool,
        use_lower: bool,
        use_digits: bool,
        use_symbols: bool,
    ) -> str:
        """Генерирует пароль по заданным параметрам."""
        # ── Собираем пул символов ──
        pool = ""
        required = []

        if use_upper:
            pool += self.CHAR_SETS["uppercase"]
            required.append(random.choice(self.CHAR_SETS["uppercase"]))
        if use_lower:
            pool += self.CHAR_SETS["lowercase"]
            required.append(random.choice(self.CHAR_SETS["lowercase"]))
        if use_digits:
            pool += self.CHAR_SETS["digits"]
            required.append(random.choice(self.CHAR_SETS["digits"]))
        if use_symbols:
            pool += self.CHAR_SETS["symbols"]
            required.append(random.choice(self.CHAR_SETS["symbols"]))

        if not pool:
            raise ValueError("Выберите хотя бы один тип символов!")

        # ── Гарантируем наличие каждого выбранного типа ──
        remaining = length - len(required)
        password_chars = required + [random.choice(pool) for _ in range(remaining)]

        # ── Перемешиваем ──
        random.shuffle(password_chars)
        return "".join(password_chars)

    def strength(
        self,
        password: str,
        use_upper: bool,
        use_lower: bool,
        use_digits: bool,
        use_symbols: bool,
    ) -> tuple[int, str, str]:
        """
        Возвращает: (score 0-100, label, color)
        Алгоритм учитывает длину + разнообразие символов.
        """
        score = 0
        length = len(password)

        # Длина (макс 40 баллов)
        score += min(40, int(length / MAX_LENGTH * 40))

        # Типы символов (по 15 баллов каждый)
        if use_upper   and any(c in self.CHAR_SETS["uppercase"] for c in password): score += 15
        if use_lower   and any(c in self.CHAR_SETS["lowercase"] for c in password): score += 15
        if use_digits  and any(c in self.CHAR_SETS["digits"]    for c in password): score += 15
        if use_symbols and any(c in self.CHAR_SETS["symbols"]   for c in password): score += 15

        score = min(score, 100)

        for threshold, label, color in STRENGTH_LEVELS:
            if score <= threshold:
                return score, label, color

        return score, "Очень сильный", "#89dceb"


# ───────────────────────── История ─────────────────────────
class HistoryManager:
    """Загрузка и сохранение истории паролей в JSON."""

    def __init__(self, filepath: str = HISTORY_FILE):
        self.filepath = filepath
        self.records: list[dict] = []
        self.load()

    def load(self) -> None:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.records = []

    def save(self) -> None:
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except IOError as e:
            messagebox.showerror("Ошибка сохранения", str(e))

    def add(self, record: dict) -> None:
        self.records.insert(0, record)   # новые сверху
        if len(self.records) > 100:      # лимит истории
            self.records = self.records[:100]
        self.save()

    def clear(self) -> None:
        self.records = []
        self.save()


# ───────────────────────── GUI ─────────────────────────
class PasswordApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.generator = PasswordGenerator()
        self.history   = HistoryManager()

        self._setup_window()
        self._build_ui()
        self._refresh_history()

    # ══════════════ Настройка окна ══════════════
    def _setup_window(self) -> None:
        self.title("🔐 Random Password Generator")
        self.geometry("860x680")
        self.minsize(700, 540)
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)

        # Центрирование
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 860) // 2
        y = (self.winfo_screenheight() - 680) // 2
        self.geometry(f"860x680+{x}+{y}")

        # Шрифты
        self.fnt_title  = font.Font(family="Segoe UI", size=18, weight="bold")
        self.fnt_header = font.Font(family="Segoe UI", size=12, weight="bold")
        self.fnt_body   = font.Font(family="Segoe UI", size=11)
        self.fnt_pass   = font.Font(family="Consolas",  size=16, weight="bold")
        self.fnt_small  = font.Font(family="Segoe UI", size=9)

        # Стиль ttk (таблица)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=COLORS["card"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["card"],
            rowheight=28,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["sidebar"],
            foreground=COLORS["accent"],
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Treeview", background=[("selected", COLORS["accent"])])

    # ══════════════ Построение UI ══════════════
    def _build_ui(self) -> None:
        self._build_header()

        # Основная зона — две колонки
        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(fill="both", expand=True, padx=16, pady=8)

        main.columnconfigure(0, weight=0, minsize=280)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        left  = tk.Frame(main, bg=COLORS["bg"])
        right = tk.Frame(main, bg=COLORS["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right.grid(row=0, column=1, sticky="nsew")

        self._build_controls(left)
        self._build_result(left)
        self._build_history(right)

        self._build_footer()

    # ────────── Заголовок ──────────
    def _build_header(self) -> None:
        hdr = tk.Frame(self, bg=COLORS["sidebar"], pady=14)
        hdr.pack(fill="x")

        tk.Label(
            hdr, text="🔐 Random Password Generator",
            bg=COLORS["sidebar"], fg=COLORS["accent"],
            font=self.fnt_title,
        ).pack(side="left", padx=20)

        tk.Label(
            hdr, text="Python · tkinter · random",
            bg=COLORS["sidebar"], fg=COLORS["text_dim"],
            font=self.fnt_small,
        ).pack(side="right", padx=20)

    # ────────── Панель настроек ──────────
    def _build_controls(self, parent: tk.Frame) -> None:
        card = self._card(parent, "⚙️  Параметры")

        # ── Ползунок длины ──
        tk.Label(
            card, text="Длина пароля:",
            bg=COLORS["card"], fg=COLORS["text"], font=self.fnt_body,
        ).pack(anchor="w", pady=(0, 2))

        slider_row = tk.Frame(card, bg=COLORS["card"])
        slider_row.pack(fill="x")

        self.length_var = tk.IntVar(value=16)
        self.lbl_len = tk.Label(
            slider_row, text="16",
            bg=COLORS["card"], fg=COLORS["accent"],
            font=self.fnt_header, width=3,
        )
        self.lbl_len.pack(side="right")

        slider = tk.Scale(
            slider_row,
            from_=MIN_LENGTH, to=MAX_LENGTH,
            orient="horizontal",
            variable=self.length_var,
            command=self._on_slider,
            bg=COLORS["card"], fg=COLORS["text"],
            troughcolor=COLORS["border"],
            activebackground=COLORS["accent"],
            highlightthickness=0, bd=0,
            sliderrelief="flat",
        )
        slider.pack(side="left", fill="x", expand=True)

        # Метки min/max
        minmax = tk.Frame(card, bg=COLORS["card"])
        minmax.pack(fill="x")
        tk.Label(minmax, text=f"мин: {MIN_LENGTH}", bg=COLORS["card"],
                 fg=COLORS["text_dim"], font=self.fnt_small).pack(side="left")
        tk.Label(minmax, text=f"макс: {MAX_LENGTH}", bg=COLORS["card"],
                 fg=COLORS["text_dim"], font=self.fnt_small).pack(side="right")

        tk.Frame(card, bg=COLORS["border"], height=1).pack(fill="x", pady=10)

        # ── Чекбоксы ──
        tk.Label(
            card, text="Набор символов:",
            bg=COLORS["card"], fg=COLORS["text"], font=self.fnt_body,
        ).pack(anchor="w", pady=(0, 6))

        self.chk_vars = {}
        checkboxes = [
            ("uppercase", "A–Z  Прописные буквы",  True),
            ("lowercase", "a–z  Строчные буквы",   True),
            ("digits",    "0–9  Цифры",             True),
            ("symbols",   "!@#  Спецсимволы",       False),
        ]

        for key, label, default in checkboxes:
            var = tk.BooleanVar(value=default)
            self.chk_vars[key] = var
            chk = tk.Checkbutton(
                card, text=label,
                variable=var,
                command=self._on_option_change,
                bg=COLORS["card"], fg=COLORS["text"],
                selectcolor=COLORS["input_bg"],
                activebackground=COLORS["card"],
                activeforeground=COLORS["accent"],
                font=self.fnt_body, bd=0, cursor="hand2",
            )
            chk.pack(anchor="w", pady=2)

        tk.Frame(card, bg=COLORS["border"], height=1).pack(fill="x", pady=10)

        # ── Кнопка генерации ──
        self._btn(
            card, "🔑  Сгенерировать пароль",
            self._generate,
            COLORS["accent"], COLORS["accent_hover"],
        ).pack(fill="x", ipady=4)

    # ────────── Результат ──────────
    def _build_result(self, parent: tk.Frame) -> None:
        card = self._card(parent, "🔑  Сгенерированный пароль")

        # Поле пароля
        pass_frame = tk.Frame(
            card, bg=COLORS["input_bg"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        pass_frame.pack(fill="x", pady=(0, 8))

        self.pass_var = tk.StringVar(value="Нажмите «Сгенерировать»")
        pass_entry = tk.Entry(
            pass_frame,
            textvariable=self.pass_var,
            font=self.fnt_pass,
            bg=COLORS["input_bg"], fg=COLORS["accent"],
            insertbackground=COLORS["accent"],
            relief="flat", bd=8,
            state="readonly",
            readonlybackground=COLORS["input_bg"],
        )
        pass_entry.pack(fill="x")

        # Кнопки под полем
        btn_row = tk.Frame(card, bg=COLORS["card"])
        btn_row.pack(fill="x", pady=(0, 10))

        self._btn(
            btn_row, "📋 Копировать",
            self._copy,
            COLORS["success"], "#8fd898",
            small=True,
        ).pack(side="left", padx=(0, 6))

        self._btn(
            btn_row, "🔄 Ещё раз",
            self._generate,
            COLORS["warning"], "#e8d09e",
            small=True,
        ).pack(side="left")

        # ── Индикатор стойкости ──
        tk.Label(
            card, text="Стойкость пароля:",
            bg=COLORS["card"], fg=COLORS["text_dim"], font=self.fnt_small,
        ).pack(anchor="w")

        self.strength_bar_bg = tk.Frame(
            card, bg=COLORS["border"], height=8,
        )
        self.strength_bar_bg.pack(fill="x", pady=(2, 4))

        self.strength_bar = tk.Frame(self.strength_bar_bg, height=8, bg=COLORS["text_dim"])
        self.strength_bar.place(relx=0, rely=0, relwidth=0, relheight=1)

        self.lbl_strength = tk.Label(
            card, text="—",
            bg=COLORS["card"], fg=COLORS["text_dim"],
            font=self.fnt_small,
        )
        self.lbl_strength.pack(anchor="w")

    # ────────── История ──────────
    def _build_history(self, parent: tk.Frame) -> None:
        card = self._card(parent, "📋  История паролей", expand=True)

        # Таблица
        columns = ("password", "length", "strength", "created_at")
        self.tree = ttk.Treeview(
            card, columns=columns,
            show="headings", selectmode="browse",
        )

        headings = {
            "password":   ("Пароль",      220),
            "length":     ("Длина",        50),
            "strength":   ("Стойкость",    90),
            "created_at": ("Дата/время",  130),
        }
        for col, (title, width) in headings.items():
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="center" if col != "password" else "w")

        # Скролл
        scroll = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Строка управления историей
        ctrl = tk.Frame(parent, bg=COLORS["bg"])
        ctrl.pack(fill="x", pady=(6, 0))

        self.lbl_count = tk.Label(
            ctrl, text="Записей: 0",
            bg=COLORS["bg"], fg=COLORS["text_dim"], font=self.fnt_small,
        )
        self.lbl_count.pack(side="left")

        self._btn(
            ctrl, "🗑 Очистить историю",
            self._clear_history,
            COLORS["danger"], COLORS["danger_hover"],
            small=True,
        ).pack(side="right")

        # Копировать по двойному клику
        self.tree.bind("<Double-1>", self._copy_from_history)

    # ────────── Футер ──────────
    def _build_footer(self) -> None:
        footer = tk.Frame(self, bg=COLORS["sidebar"], pady=6)
        footer.pack(fill="x", side="bottom")
        tk.Label(
            footer,
            text=f"💾 История сохраняется в: {os.path.abspath(HISTORY_FILE)}   |   "
                 "Двойной клик по строке — скопировать пароль",
            bg=COLORS["sidebar"], fg=COLORS["text_dim"], font=self.fnt_small,
        ).pack()

    # ══════════════ Логика ══════════════
    def _generate(self) -> None:
        length     = self.length_var.get()
        use_upper  = self.chk_vars["uppercase"].get()
        use_lower  = self.chk_vars["lowercase"].get()
        use_digits = self.chk_vars["digits"].get()
        use_sym    = self.chk_vars["symbols"].get()

        # ── Валидация ──
        if not any([use_upper, use_lower, use_digits, use_sym]):
            messagebox.showwarning(
                "Нет символов",
                "Выберите хотя бы один тип символов!"
            )
            return

        if not (MIN_LENGTH <= length <= MAX_LENGTH):
            messagebox.showwarning(
                "Некорректная длина",
                f"Длина должна быть от {MIN_LENGTH} до {MAX_LENGTH} символов."
            )
            return

        try:
            password = self.generator.generate(
                length, use_upper, use_lower, use_digits, use_sym
            )
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return

        # Показываем пароль
        self.pass_var.set(password)

        # Обновляем индикатор стойкости
        score, label, color = self.generator.strength(
            password, use_upper, use_lower, use_digits, use_sym
        )
        self._update_strength(score, label, color)

        # Добавляем в историю
        record = {
            "password":   password,
            "length":     length,
            "strength":   label,
            "created_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "options": {
                "uppercase": use_upper,
                "lowercase": use_lower,
                "digits":    use_digits,
                "symbols":   use_sym,
            }
        }
        self.history.add(record)
        self._refresh_history()

    def _copy(self) -> None:
        pwd = self.pass_var.get()
        if pwd and pwd != "Нажмите «Сгенерировать»":
            self.clipboard_clear()
            self.clipboard_append(pwd)
            messagebox.showinfo("Скопировано", "Пароль скопирован в буфер обмена!")

    def _copy_from_history(self, _event=None) -> None:
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], "values")
            if values:
                self.clipboard_clear()
                self.clipboard_append(values[0])
                messagebox.showinfo("Скопировано", "Пароль скопирован в буфер обмена!")

    def _clear_history(self) -> None:
        if not self.history.records:
            messagebox.showinfo("История пуста", "Нечего очищать.")
            return
        if messagebox.askyesno(
            "Подтверждение",
            f"Удалить все {len(self.history.records)} записей из истории?",
        ):
            self.history.clear()
            self._refresh_history()

    def _refresh_history(self) -> None:
        """Перерисовка таблицы истории."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        for rec in self.history.records:
            self.tree.insert("", "end", values=(
                rec["password"],
                rec["length"],
                rec["strength"],
                rec["created_at"],
            ))

        self.lbl_count.config(text=f"Записей: {len(self.history.records)}")

    def _update_strength(self, score: int, label: str, color: str) -> None:
        """Обновляет полосу стойкости."""
        rel = score / 100
        self.strength_bar.place(relwidth=rel)
        self.strength_bar.config(bg=color)
        self.lbl_strength.config(text=f"{label}  ({score}/100)", fg=color)

    def _on_slider(self, value) -> None:
        self.lbl_len.config(text=str(int(float(value))))

    def _on_option_change(self) -> None:
        pass   # можно добавить live-preview

    # ══════════════ Вспомогательные ══════════════
    def _card(
        self, parent: tk.Widget, title: str, expand: bool = False
    ) -> tk.Frame:
        """Создаёт карточку с заголовком и возвращает внутренний Frame."""
        outer = tk.Frame(parent, bg=COLORS["bg"])
        outer.pack(fill="both", expand=expand, pady=(0, 10))

        tk.Label(
            outer, text=title,
            bg=COLORS["bg"], fg=COLORS["text_dim"],
            font=self.fnt_small,
        ).pack(anchor="w", pady=(0, 3))

        inner = tk.Frame(
            outer, bg=COLORS["card"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            padx=14, pady=12,
        )
        inner.pack(fill="both", expand=expand)
        return inner

    def _btn(
        self, parent, text: str, cmd,
        color: str, hover: str, small: bool = False,
    ) -> tk.Label:
        f = self.fnt_small if small else self.fnt_body
        btn = tk.Label(
            parent, text=text,
            bg=color, fg=COLORS["sidebar"],
            font=f, cursor="hand2",
            padx=10, pady=4 if small else 8,
            relief="flat",
        )
        btn.bind("<Button-1>", lambda _: cmd())
        btn.bind("<Enter>",    lambda _, w=btn, c=hover: w.config(bg=c))
        btn.bind("<Leave>",    lambda _, w=btn, c=color: w.config(bg=c))
        return btn


# ───────────────────────── Точка входа ─────────────────────────
if __name__ == "__main__":
    app = PasswordApp()
    app.mainloop()
