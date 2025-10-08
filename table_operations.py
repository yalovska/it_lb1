from typing import List

from database import Database, DataType


class TableOperations:
    @staticmethod
    def intersect_tables(db: Database, table1: str, table2: str, common_fields: List[str]):
        """Перетин двох таблиць по спільним полям"""
        rows1 = db.get_rows(table1)
        rows2 = db.get_rows(table2)

        # Створення результативної таблиці
        result_table_name = f"intersect_{table1}_{table2}"

        # Визначення полів для результативної таблиці
        result_fields = {}
        for field in common_fields:
            # Використовуємо тип з першої таблиці
            table_info = next((table for table in db.tables if table['name'] == table1), None)
            if table_info and field in table_info['fields']:
                result_fields[field] = table_info['fields'][field]

        # Створення таблиці для результатів
        db.create_table(result_table_name, result_fields)

        # Знаходження спільних рядків
        common_rows = []
        for row1 in rows1:
            for row2 in rows2:
                if all(row1.get(field) == row2.get(field) for field in common_fields):
                    common_data = {field: row1[field] for field in common_fields}
                    common_rows.append(common_data)

        # Додавання спільних рядків
        for row_data in common_rows:
            db.add_row(result_table_name, row_data)

        return result_table_name

    @staticmethod
    def validate_table_structure(db: Database, table_name: str) -> bool:
        """Валідація структури таблиці"""
        table_info = next((table for table in db.tables if table['name'] == table_name), None)
        if not table_info:
            return False

        # Перевірка, чи всі поля мають коректні типи
        for field_type in table_info['fields'].values():
            if field_type not in DataType:
                return False

        return True