import sqlite3
import json
import re
import os
from enum import Enum
from typing import List, Dict, Any


class DataType(Enum):
    INTEGER = "integer"
    REAL = "real"
    CHAR = "char"
    STRING = "string"
    ENUM = "enum"
    EMAIL = "email"


class Database:
    def __init__(self, name: str):
        self.name = name
        self.connection = None
        self.tables = []
        self.enum_definitions = {}

    def connect(self):
        """Підключення до бази даних"""
        try:
            if not os.path.exists('databases'):
                os.makedirs('databases')

            db_path = f"databases/{self.name}.db"
            self.connection = sqlite3.connect(db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row

            print(f"✅ Підключено до бази даних: {db_path}")
            return True
        except Exception as e:
            print(f"❌ Помилка підключення: {e}")
            return False

    def disconnect(self):
        """Відключення від бази даних"""
        if self.connection:
            self.connection.close()
            print("✅ Відключено від бази даних")

    def define_enum(self, enum_name: str, values: List[str]):
        """Визначення перелічуваного типу"""
        if not enum_name or not values:
            raise ValueError("Enum name and values cannot be empty")

        cleaned_values = [str(value).strip() for value in values if str(value).strip()]
        self.enum_definitions[enum_name] = cleaned_values
        print(f"✅ Перелічуваний тип '{enum_name}' визначено: {cleaned_values}")
        return True

    def create_table(self, table_name: str, fields: Dict[str, Dict]):
        """Створення таблиці"""
        if not table_name or not fields:
            raise ValueError("Table name and fields cannot be empty")

        if not self.connection:
            raise ValueError("Database not connected")

        cursor = self.connection.cursor()

        try:
            # Формування SQL запиту - використовуємо тільки поля з словника, не додаємо зайвий id
            field_definitions = []
            for field_name, field_info in fields.items():
                field_definitions.append(f"{field_name} TEXT")

            # Додаємо PRIMARY KEY окремо
            create_query = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(field_definitions)})"
            print(f"📝 Виконуємо запит: {create_query}")

            cursor.execute(create_query)
            self.connection.commit()

            # Додавання інформації про таблицю
            table_info = {
                'name': table_name,
                'fields': fields
            }
            self.tables.append(table_info)

            print(f"✅ Таблицю '{table_name}' створено успішно")
            return True

        except sqlite3.Error as e:
            print(f"❌ SQLite помилка: {e}")
            self.connection.rollback()
            raise Exception(f"Помилка бази даних: {e}")

    def add_row(self, table_name: str, data: Dict[str, Any]):
        """Додавання рядка"""
        if not self._validate_row_data(table_name, data):
            raise ValueError("Invalid data for table")

        cursor = self.connection.cursor()

        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = [str(value) for value in data.values()]

            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            cursor.execute(insert_query, values)
            self.connection.commit()

            row_id = cursor.lastrowid
            print(f"✅ Рядок додано успішно (ID: {row_id})")
            return row_id

        except sqlite3.Error as e:
            print(f"❌ Помилка додавання рядка: {e}")
            self.connection.rollback()
            raise

    def get_rows(self, table_name: str):
        """Отримання всіх рядків таблиці"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            result = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                result.append(row_dict)

            print(f"✅ Отримано {len(result)} рядків з таблиці '{table_name}'")
            return result

        except sqlite3.Error as e:
            print(f"❌ Помилка отримання даних: {e}")
            return []

    def update_row(self, table_name: str, row_id: int, data: Dict[str, Any]):
        """Редагування рядка"""
        if not self._validate_row_data(table_name, data):
            raise ValueError("Invalid data for table")

        cursor = self.connection.cursor()

        try:
            set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
            values = [str(value) for value in data.values()]
            values.append(row_id)

            update_query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
            cursor.execute(update_query, values)
            self.connection.commit()

            success = cursor.rowcount > 0
            if success:
                print(f"✅ Рядок з ID {row_id} оновлено")
            return success

        except sqlite3.Error as e:
            print(f"❌ Помилка оновлення рядка: {e}")
            self.connection.rollback()
            raise

    def delete_row(self, table_name: str, row_id: int):
        """Видалення рядка"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (row_id,))
            self.connection.commit()

            success = cursor.rowcount > 0
            if success:
                print(f"✅ Рядок з ID {row_id} видалено")
            return success

        except sqlite3.Error as e:
            print(f"❌ Помилка видалення рядка: {e}")
            self.connection.rollback()
            raise

    def _validate_email(self, email: str) -> bool:
        """Валідація email адреси"""
        if not isinstance(email, str) or not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _validate_enum(self, value: str, enum_name: str) -> bool:
        """Валідація перелічуваного типу"""
        if enum_name not in self.enum_definitions:
            return False
        return value in self.enum_definitions[enum_name]

    def _validate_row_data(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Валідація даних рядка"""
        table_info = next((table for table in self.tables if table['name'] == table_name), None)
        if not table_info:
            print(f"❌ Таблиця '{table_name}' не знайдена")
            return False

        for field_name, value in data.items():
            if field_name not in table_info['fields']:
                print(f"❌ Поле '{field_name}' не існує в таблиці '{table_name}'")
                return False

            field_info = table_info['fields'][field_name]
            field_type = field_info['type']

            if not value and field_type != DataType.INTEGER and field_type != DataType.REAL:
                continue

            try:
                if field_type == DataType.INTEGER:
                    if value:
                        int(value)
                elif field_type == DataType.REAL:
                    if value:
                        float(value)
                elif field_type == DataType.CHAR:
                    if value and (not isinstance(value, str) or len(value) != 1):
                        return False
                elif field_type == DataType.EMAIL:
                    if value and not self._validate_email(value):
                        return False
                elif field_type == DataType.ENUM:
                    if value:
                        enum_name = field_info.get('enum_name')
                        if not enum_name or not self._validate_enum(value, enum_name):
                            return False
            except (ValueError, TypeError):
                return False

        return True

    def intersect_tables(self, table1_name: str, table2_name: str, common_fields: List[str]) -> str:
        """Перетин двох таблиць по спільним полям"""
        print(f"🔍 Виконуємо перетин таблиць '{table1_name}' і '{table2_name}' по полях: {common_fields}")

        try:
            table1_data = self.get_rows(table1_name)
            table2_data = self.get_rows(table2_name)

            result_table_name = f"intersect_{table1_name}_{table2_name}"

            table1_info = next((table for table in self.tables if table['name'] == table1_name), None)
            result_fields = {}

            for field in common_fields:
                if table1_info and field in table1_info['fields']:
                    result_fields[field] = table1_info['fields'][field]

            self.create_table(result_table_name, result_fields)

            common_rows = []
            for row1 in table1_data:
                for row2 in table2_data:
                    match = True
                    for field in common_fields:
                        if row1.get(field) != row2.get(field):
                            match = False
                            break

                    if match:
                        common_data = {field: row1[field] for field in common_fields}
                        if common_data not in common_rows:
                            common_rows.append(common_data)

            for row_data in common_rows:
                self.add_row(result_table_name, row_data)

            print(f"✅ Перетин завершено. Створено таблицю '{result_table_name}' з {len(common_rows)} рядками")
            return result_table_name

        except Exception as e:
            print(f"❌ Помилка перетину таблиць: {e}")
            raise

    def save_to_disk(self, filename: str):
        """Збереження структури бази даних на диск"""
        try:
            database_info = {
                'name': self.name,
                'tables': self.tables,
                'enum_definitions': self.enum_definitions
            }

            serializable_info = json.loads(
                json.dumps(database_info, default=lambda x: x.value if isinstance(x, Enum) else str(x)))

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_info, f, indent=2, ensure_ascii=False)

            print(f"💾 Базу даних збережено у файл: {filename}")
            return True

        except Exception as e:
            print(f"❌ Помилка збереження: {e}")
            raise

    def load_from_disk(self, filename: str):
        """Завантаження структури бази даних з диску"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                database_info = json.load(f)

            self.name = database_info['name']
            self.enum_definitions = database_info.get('enum_definitions', {})

            self.tables = []
            for table_info in database_info['tables']:
                restored_table = {
                    'name': table_info['name'],
                    'fields': {}
                }

                for field_name, field_data in table_info['fields'].items():
                    restored_table['fields'][field_name] = {
                        'type': DataType(field_data['type']),
                        'enum_name': field_data.get('enum_name')
                    }

                self.tables.append(restored_table)

            print(f"📂 Базу даних завантажено з файлу: {filename}")
            return True

        except Exception as e:
            print(f"❌ Помилка завантаження: {e}")
            raise