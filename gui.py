import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import List

from database import Database, DataType


class DatabaseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Система управління табличними базами даних")
        self.root.geometry("1000x700")

        self.current_db = None
        self.setup_ui()

    def setup_ui(self):
        """Налаштування інтерфейсу користувача"""
        # Верхня панель
        top_frame = ttk.Frame(self.root)
        top_frame.pack(pady=10, padx=10, fill=tk.X)

        ttk.Button(top_frame, text="Створити БД", command=self.create_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Відкрити БД", command=self.open_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Закрити БД", command=self.close_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Визначити Enum", command=self.define_enum_type).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Перетин таблиць", command=self.intersect_tables).pack(side=tk.LEFT, padx=5)

        # Основна область
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Ліва панель для таблиць
        left_frame = ttk.LabelFrame(main_frame, text="Таблиці", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.tables_listbox = tk.Listbox(left_frame, width=25, height=20)
        self.tables_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tables_listbox.bind('<<ListboxSelect>>', self.on_table_select)

        table_buttons_frame = ttk.Frame(left_frame)
        table_buttons_frame.pack(fill=tk.X, pady=5)

        ttk.Button(table_buttons_frame, text="Додати", command=self.create_table).pack(side=tk.LEFT, fill=tk.X,
                                                                                       expand=True, padx=2)
        ttk.Button(table_buttons_frame, text="Видалити", command=self.delete_table).pack(side=tk.LEFT, fill=tk.X,
                                                                                         expand=True, padx=2)
        ttk.Button(table_buttons_frame, text="Оновити", command=self.refresh_tables_list).pack(side=tk.LEFT, fill=tk.X,
                                                                                               expand=True, padx=2)

        # Права панель для даних
        right_frame = ttk.LabelFrame(main_frame, text="Дані таблиці", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Панель керування даними
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Button(control_frame, text="Додати рядок", command=self.add_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Редагувати рядок", command=self.edit_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Видалити рядок", command=self.delete_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Оновити дані", command=self.refresh_table_data).pack(side=tk.LEFT, padx=5)

        # Таблиця для відображення даних
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Додаємо прокрутку
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        self.tree.pack(fill=tk.BOTH, expand=True)

        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        # Статус бар
        self.status_var = tk.StringVar()
        self.status_var.set("Готово до роботи")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_database(self):
        """Створення нової бази даних"""
        db_name = simpledialog.askstring("Створення БД", "Введіть назву бази даних:")
        if db_name:
            try:
                self.current_db = Database(db_name)
                if self.current_db.connect():
                    self.refresh_tables_list()
                    self.status_var.set(f"Базу даних '{db_name}' створено та відкрито")
                    messagebox.showinfo("Успіх", f"Базу даних '{db_name}' створено успішно!")
                else:
                    messagebox.showerror("Помилка", "Не вдалося підключитися до бази даних")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося створити базу даних: {str(e)}")

    def open_database(self):
        """Відкриття існуючої бази даних"""
        db_name = simpledialog.askstring("Відкриття БД", "Введіть назву бази даних:")
        if db_name:
            try:
                self.current_db = Database(db_name)
                if self.current_db.connect():
                    # Отримуємо список таблиць з бази даних
                    cursor = self.current_db.connection.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
                    tables = cursor.fetchall()

                    self.current_db.tables = []
                    for table in tables:
                        # Отримуємо інформацію про поля таблиці
                        cursor.execute(f"PRAGMA table_info({table[0]})")
                        columns = cursor.fetchall()
                        fields = {}
                        for col in columns:
                            if col[1] != 'id':  # Пропускаємо поле id
                                # Для спрощення вважаємо всі поля STRING
                                fields[col[1]] = {'type': DataType.STRING}

                        self.current_db.tables.append({
                            'name': table[0],
                            'fields': fields
                        })

                    self.refresh_tables_list()
                    self.status_var.set(f"Базу даних '{db_name}' відкрито")
                    messagebox.showinfo("Успіх", f"Базу даних '{db_name}' відкрито успішно!")
                else:
                    messagebox.showerror("Помилка", "Не вдалося підключитися до бази даних")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося відкрити базу даних: {str(e)}")

    def close_database(self):
        """Закриття бази даних"""
        if self.current_db:
            self.current_db.disconnect()
            self.current_db = None
            self.tables_listbox.delete(0, tk.END)
            self.clear_data_table()
            self.status_var.set("Базу даних закрито")
            messagebox.showinfo("Інформація", "Базу даних закрито")
        else:
            messagebox.showwarning("Увага", "Немає відкритої бази даних")

    def define_enum_type(self):
        """Визначення нового перелічуваного типу"""
        if not self.current_db:
            messagebox.showwarning("Увага", "Спочатку створіть або відкрийте базу даних")
            return

        enum_name = simpledialog.askstring("Визначення Enum", "Введіть назву перелічуваного типу:")
        if enum_name:
            values_str = simpledialog.askstring("Значення Enum", "Введіть значення через кому:")
            if values_str:
                values = [v.strip() for v in values_str.split(',') if v.strip()]
                try:
                    self.current_db.define_enum(enum_name, values)
                    self.status_var.set(f"Перелічуваний тип '{enum_name}' визначено")
                    messagebox.showinfo("Успіх", f"Перелічуваний тип '{enum_name}' визначено успішно!")
                except Exception as e:
                    messagebox.showerror("Помилка", f"Не вдалося визначити enum: {str(e)}")

    def create_table(self):
        """Створення нової таблиці"""
        if not self.current_db:
            messagebox.showwarning("Увага", "Спочатку створіть або відкрийте базу даних")
            return

        table_name = simpledialog.askstring("Створення таблиці", "Введіть назву таблиці:")
        if table_name:
            fields = self.get_table_fields()
            if fields:
                try:
                    self.current_db.create_table(table_name, fields)
                    self.refresh_tables_list()
                    self.status_var.set(f"Таблицю '{table_name}' створено успішно")
                except Exception as e:
                    messagebox.showerror("Помилка", f"Не вдалося створити таблицю: {str(e)}")

    def get_table_fields(self):
        """Діалог для вибору полів таблиці"""
        fields = {}

        while True:
            field_name = simpledialog.askstring("Додати поле",
                                                "Введіть назву поля (залиште порожнім для завершення):")
            if not field_name:
                break

            field_info = self.ask_field_type()
            if field_info:
                fields[field_name] = field_info

        return fields if fields else None

    def ask_field_type(self):
        """Вибір типу поля"""
        type_window = tk.Toplevel(self.root)
        type_window.title("Вибір типу поля")
        type_window.geometry("400x300")
        type_window.transient(self.root)
        type_window.grab_set()

        selected_type = tk.StringVar(value=DataType.STRING.value)
        enum_var = tk.StringVar()

        # Список визначених enum типів
        enum_types = list(self.current_db.enum_definitions.keys()) if self.current_db else []

        ttk.Label(type_window, text="Оберіть тип поля:", font=('Arial', 10, 'bold')).pack(pady=10)

        # Радіокнопки для типів
        ttk.Radiobutton(type_window, text="Integer (ціле число)",
                        variable=selected_type, value=DataType.INTEGER.value).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(type_window, text="Real (дійсне число)",
                        variable=selected_type, value=DataType.REAL.value).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(type_window, text="Char (один символ)",
                        variable=selected_type, value=DataType.CHAR.value).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(type_window, text="String (рядок)",
                        variable=selected_type, value=DataType.STRING.value).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(type_window, text="Email",
                        variable=selected_type, value=DataType.EMAIL.value).pack(anchor=tk.W, pady=2)

        # Enum тип
        enum_frame = ttk.Frame(type_window)
        enum_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(enum_frame, text="Enum (перелічуваний)",
                        variable=selected_type, value=DataType.ENUM.value).pack(side=tk.LEFT)

        if enum_types:
            enum_combo = ttk.Combobox(enum_frame, textvariable=enum_var, values=enum_types, state="readonly", width=15)
            enum_combo.pack(side=tk.LEFT, padx=5)
            enum_combo.set(enum_types[0])
        else:
            ttk.Label(enum_frame, text="(немає визначених enum)", foreground="gray").pack(side=tk.LEFT, padx=5)

        result = None

        def on_ok():
            nonlocal result
            field_type = DataType(selected_type.get())

            if field_type == DataType.ENUM:
                if not enum_types:
                    messagebox.showwarning("Увага", "Спочатку визначте перелічуваний тип через 'Визначити Enum'")
                    return
                enum_name = enum_var.get()
                if not enum_name:
                    messagebox.showwarning("Увага", "Виберіть перелічуваний тип")
                    return
                result = {'type': field_type, 'enum_name': enum_name}
            else:
                result = {'type': field_type}

            type_window.destroy()

        def on_cancel():
            nonlocal result
            result = None
            type_window.destroy()

        button_frame = ttk.Frame(type_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Скасувати", command=on_cancel).pack(side=tk.RIGHT, padx=10)

        type_window.wait_window()
        return result

    def delete_table(self):
        """Видалення таблиці"""
        if not self.current_db:
            messagebox.showwarning("Увага", "Спочатку створіть або відкрийте базу даних")
            return

        selected = self.tables_listbox.curselection()
        if selected:
            table_name = self.tables_listbox.get(selected[0])
            if messagebox.askyesno("Підтвердження", f"Видалити таблицю '{table_name}'?"):
                try:
                    self.current_db.delete_table(table_name)
                    self.refresh_tables_list()
                    self.clear_data_table()
                    self.status_var.set(f"Таблицю '{table_name}' видалено успішно")
                except Exception as e:
                    messagebox.showerror("Помилка", f"Не вдалося видалити таблицю: {str(e)}")
        else:
            messagebox.showwarning("Увага", "Виберіть таблицю для видалення")

    def on_table_select(self, event):
        """Обробка вибору таблиці"""
        selected = self.tables_listbox.curselection()
        if selected and self.current_db:
            table_name = self.tables_listbox.get(selected[0])
            self.display_table_data(table_name)

    def display_table_data(self, table_name):
        """Відображення даних таблиці"""
        try:
            rows = self.current_db.get_rows(table_name)
            self.clear_data_table()

            if rows:
                # Налаштування колонок
                columns = list(rows[0].keys())
                self.tree['columns'] = columns

                # Заголовки колонок
                self.tree.heading('#0', text='ID')
                self.tree.column('#0', width=50)

                for col in columns:
                    self.tree.heading(col, text=col)
                    self.tree.column(col, width=100)

                # Додавання даних
                for row in rows:
                    values = [row[col] for col in columns]
                    self.tree.insert('', tk.END, text=row.get('id', ''), values=values)

            self.status_var.set(f"Відображено {len(rows)} рядків з таблиці '{table_name}'")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося завантажити дані: {str(e)}")

    def clear_data_table(self):
        """Очищення таблиці даних"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree['columns'] = []

    def refresh_tables_list(self):
        """Оновлення списку таблиць"""
        self.tables_listbox.delete(0, tk.END)
        if self.current_db:
            for table in self.current_db.tables:
                self.tables_listbox.insert(tk.END, table['name'])

    def refresh_table_data(self):
        """Оновлення даних поточної таблиці"""
        selected = self.tables_listbox.curselection()
        if selected and self.current_db:
            table_name = self.tables_listbox.get(selected[0])
            self.display_table_data(table_name)

    def add_row(self):
        """Додавання нового рядка"""
        if not self.current_db:
            messagebox.showwarning("Увага", "Спочатку створіть або відкрийте базу даних")
            return

        selected = self.tables_listbox.curselection()
        if not selected:
            messagebox.showwarning("Увага", "Виберіть таблицю")
            return

        table_name = self.tables_listbox.get(selected[0])
        table_info = next((table for table in self.current_db.tables if table['name'] == table_name), None)

        if table_info:
            data = self.get_row_data(table_info['fields'])
            if data:
                try:
                    row_id = self.current_db.add_row(table_name, data)
                    self.display_table_data(table_name)
                    self.status_var.set(f"Рядок додано успішно (ID: {row_id})")
                    messagebox.showinfo("Успіх", "Рядок додано успішно!")
                except Exception as e:
                    messagebox.showerror("Помилка", f"Не вдалося додати рядок: {str(e)}")

    def edit_row(self):
        """Редагування вибраного рядка - ВИПРАВЛЕНА ВЕРСІЯ"""
        if not self.current_db:
            messagebox.showwarning("Увага", "Спочатку створіть або відкрийте базу даних")
            return

        selected_table = self.tables_listbox.curselection()
        selected_row = self.tree.selection()

        if not selected_table or not selected_row:
            messagebox.showwarning("Увага", "Виберіть таблицю та рядок для редагування")
            return

        table_name = self.tables_listbox.get(selected_table[0])
        row_id = self.tree.item(selected_row[0])['text']

        print(f"🔍 Спроба редагувати рядок з ID: {row_id} в таблиці: {table_name}")

        # Отримуємо поточні дані рядка БЕЗПОСЕРЕДНЬО з бази даних
        current_row = self.current_db.get_row_by_id(table_name, int(row_id))

        if not current_row:
            messagebox.showerror("Помилка", f"Рядок з ID {row_id} не знайдено в таблиці '{table_name}'")
            return

        table_info = next((table for table in self.current_db.tables if table['name'] == table_name), None)
        if not table_info:
            messagebox.showerror("Помилка", f"Інформація про таблицю '{table_name}' не знайдена")
            return

        # Видаляємо ID з даних для редагування
        edit_data = {k: v for k, v in current_row.items() if k != 'id'}

        new_data = self.get_row_data(table_info['fields'], edit_data)
        if new_data:
            try:
                success = self.current_db.update_row(table_name, int(row_id), new_data)
                if success:
                    self.display_table_data(table_name)
                    self.status_var.set(f"Рядок з ID {row_id} успішно оновлено")
                    messagebox.showinfo("Успіх", "Рядок оновлено успішно!")
                else:
                    messagebox.showerror("Помилка", f"Не вдалося оновити рядок з ID {row_id}")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося оновити рядок: {str(e)}")

    def delete_row(self):
        """Видалення вибраного рядка"""
        if not self.current_db:
            messagebox.showwarning("Увага", "Спочатку створіть або відкрийте базу даних")
            return

        selected_table = self.tables_listbox.curselection()
        selected_row = self.tree.selection()

        if not selected_table or not selected_row:
            messagebox.showwarning("Увага", "Виберіть таблицю та рядок для видалення")
            return

        table_name = self.tables_listbox.get(selected_table[0])
        row_id = self.tree.item(selected_row[0])['text']

        print(f"🗑️ Спроба видалити рядок з ID: {row_id} з таблиці: {table_name}")

        if messagebox.askyesno("Підтвердження", f"Видалити рядок з ID {row_id} з таблиці '{table_name}'?"):
            try:
                success = self.current_db.delete_row(table_name, int(row_id))
                if success:
                    self.display_table_data(table_name)
                    self.status_var.set(f"Рядок з ID {row_id} успішно видалено")
                    messagebox.showinfo("Успіх", "Рядок видалено успішно!")
                else:
                    messagebox.showerror("Помилка", f"Рядок з ID {row_id} не знайдено")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося видалити рядок: {str(e)}")

    def get_row_data(self, fields, initial_data=None):
        """Діалог для введення даних рядка"""
        if initial_data is None:
            initial_data = {}

        data_window = tk.Toplevel(self.root)
        data_window.title("Введіть дані рядка")
        data_window.geometry("500x400")
        data_window.transient(self.root)
        data_window.grab_set()

        entries = {}

        ttk.Label(data_window, text="Введіть значення для полів:",
                  font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)

        for i, (field_name, field_info) in enumerate(fields.items(), 1):
            field_type = field_info['type']

            label_text = f"{field_name} ({field_type.value})"
            if field_type == DataType.ENUM:
                enum_name = field_info.get('enum_name')
                enum_values = self.current_db.enum_definitions.get(enum_name, [])
                label_text += f": {', '.join(enum_values)}"

            ttk.Label(data_window, text=label_text).grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)

            if field_type == DataType.ENUM:
                # Випадаючий список для enum
                enum_name = field_info.get('enum_name')
                enum_values = self.current_db.enum_definitions.get(enum_name, [])
                combo = ttk.Combobox(data_window, values=enum_values, state="readonly")
                combo.grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)

                if field_name in initial_data:
                    combo.set(str(initial_data[field_name]))
                elif enum_values:
                    combo.set(enum_values[0])

                entries[field_name] = combo
            else:
                # Звичайне поле вводу для інших типів
                entry = ttk.Entry(data_window, width=30)
                entry.grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)

                if field_name in initial_data:
                    entry.insert(0, str(initial_data[field_name]))

                entries[field_name] = entry

        result_data = None

        def on_ok():
            nonlocal result_data
            result_data = {}
            try:
                for field_name, widget in entries.items():
                    if isinstance(widget, ttk.Combobox):
                        value = widget.get()
                    else:
                        value = widget.get()

                    # Для порожніх значень числових полів встановлюємо 0
                    if not value and fields[field_name]['type'] in [DataType.INTEGER, DataType.REAL]:
                        value = "0"

                    result_data[field_name] = value

                data_window.destroy()
            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка введення: {str(e)}")

        def on_cancel():
            nonlocal result_data
            result_data = None
            data_window.destroy()

        button_frame = ttk.Frame(data_window)
        button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Скасувати", command=on_cancel).pack(side=tk.RIGHT, padx=10)

        data_window.wait_window()
        return result_data

    def intersect_tables(self):
        """Операція перетину таблиць"""
        if not self.current_db:
            messagebox.showwarning("Увага", "Спочатку створіть або відкрийте базу даних")
            return

        if len(self.current_db.tables) < 2:
            messagebox.showwarning("Увага", "Потрібно щонайменше дві таблиці")
            return

        # Діалог вибору таблиць
        table1 = self.ask_table_selection("Виберіть першу таблицю для перетину:")
        if not table1:
            return

        table2 = self.ask_table_selection("Виберіть другу таблицю для перетину:")
        if not table2:
            return

        if table1 == table2:
            messagebox.showwarning("Увага", "Виберіть різні таблиці")
            return

        # Знаходимо спільні поля
        table1_info = next((table for table in self.current_db.tables if table['name'] == table1), None)
        table2_info = next((table for table in self.current_db.tables if table['name'] == table2), None)

        if not table1_info or not table2_info:
            messagebox.showerror("Помилка", "Одна з таблиць не знайдена")
            return

        common_fields = list(set(table1_info['fields'].keys()) & set(table2_info['fields'].keys()))

        if not common_fields:
            messagebox.showwarning("Увага", "Таблиці не мають спільних полів")
            return

        # Діалог вибору полів для перетину
        selected_fields = self.ask_field_selection(common_fields, "Виберіть поля для перетину:")
        if not selected_fields:
            return

        try:
            result_table = self.current_db.intersect_tables(table1, table2, selected_fields)
            self.refresh_tables_list()
            self.status_var.set(f"Створено таблицю перетину: {result_table}")
            messagebox.showinfo("Успіх", f"Перетин таблиць завершено!\nСтворено таблицю: {result_table}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося виконати перетин таблиць: {str(e)}")

    def ask_table_selection(self, title: str) -> str:
        """Діалог вибору таблиці"""
        tables = [table['name'] for table in self.current_db.tables]

        selection_window = tk.Toplevel(self.root)
        selection_window.title(title)
        selection_window.geometry("300x200")
        selection_window.transient(self.root)
        selection_window.grab_set()

        selected_table = tk.StringVar()

        ttk.Label(selection_window, text=title, font=('Arial', 10, 'bold')).pack(pady=10)

        listbox = tk.Listbox(selection_window)
        for table in tables:
            listbox.insert(tk.END, table)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        result = None

        def on_ok():
            nonlocal result
            selection = listbox.curselection()
            if selection:
                result = listbox.get(selection[0])
                selection_window.destroy()
            else:
                messagebox.showwarning("Увага", "Виберіть таблицю")

        def on_cancel():
            nonlocal result
            result = None
            selection_window.destroy()

        button_frame = ttk.Frame(selection_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Скасувати", command=on_cancel).pack(side=tk.RIGHT, padx=10)

        selection_window.wait_window()
        return result

    def ask_field_selection(self, fields: List[str], title: str) -> List[str]:
        """Діалог вибору полів"""
        selection_window = tk.Toplevel(self.root)
        selection_window.title(title)
        selection_window.geometry("300x300")
        selection_window.transient(self.root)
        selection_window.grab_set()

        selected_fields = []

        ttk.Label(selection_window, text=title, font=('Arial', 10, 'bold')).pack(pady=10)

        # Фрейм для чекбоксів
        check_frame = ttk.Frame(selection_window)
        check_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        check_vars = {}
        for field in fields:
            var = tk.BooleanVar(value=True)  # За замовчуванням всі обрані
            check_vars[field] = var
            ttk.Checkbutton(check_frame, text=field, variable=var).pack(anchor=tk.W)

        result = None

        def on_ok():
            nonlocal result
            result = [field for field, var in check_vars.items() if var.get()]
            if not result:
                messagebox.showwarning("Увага", "Виберіть хоча б одне поле")
                return
            selection_window.destroy()

        def on_cancel():
            nonlocal result
            result = None
            selection_window.destroy()

        button_frame = ttk.Frame(selection_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Скасувати", command=on_cancel).pack(side=tk.RIGHT, padx=10)

        selection_window.wait_window()
        return result
