import unittest
import os
from database import Database, DataType


class TestDatabaseSystem(unittest.TestCase):

    def setUp(self):
        """Підготовка до тестування"""
        self.test_db_name = "test_db"
        self.db = Database(self.test_db_name)
        self.db.connect()

    def tearDown(self):
        """Очищення після тестування"""
        if self.db.connection:
            self.db.disconnect()
        # Видалення тестових файлів
        if os.path.exists(f"databases/{self.test_db_name}.db"):
            os.remove(f"databases/{self.test_db_name}.db")
        if os.path.exists("test_save.json"):
            os.remove("test_save.json")

    def test_1_create_database_and_tables(self):
        """Тест 1: Створення бази даних, таблиць з усіма типами даних"""
        # Визначення enum типів
        self.db.define_enum('department', ['IT', 'HR', 'Finance'])
        self.db.define_enum('status', ['active', 'inactive'])

        # Створення таблиці з усіма типами даних
        fields = {
            'name': {'type': DataType.STRING},
            'age': {'type': DataType.INTEGER},
            'salary': {'type': DataType.REAL},
            'grade': {'type': DataType.CHAR},
            'email': {'type': DataType.EMAIL},
            'department': {'type': DataType.ENUM, 'enum_name': 'department'},
            'status': {'type': DataType.ENUM, 'enum_name': 'status'}
        }

        # Створення таблиці
        result = self.db.create_table('employees', fields)
        self.assertTrue(result)

        # Перевірка, що таблиця додана до списку
        table_names = [table['name'] for table in self.db.tables]
        self.assertIn('employees', table_names)

        print("✅ Тест 1 пройдено: База даних і таблиці створені")

    def test_2_data_validation_and_crud_operations(self):
        """Тест 2: Валідація даних та CRUD операції"""
        # Створення простої таблиці для тестування
        fields = {
            'name': {'type': DataType.STRING},
            'age': {'type': DataType.INTEGER},
            'email': {'type': DataType.EMAIL}
        }
        self.db.create_table('users', fields)

        # Тест валідації - валідні дані
        valid_data = {'name': 'John Doe', 'age': '25', 'email': 'john@example.com'}
        row_id = self.db.add_row('users', valid_data)
        self.assertIsNotNone(row_id)

        # Тест валідації - невалідний email
        invalid_data = {'name': 'Jane Doe', 'age': '30', 'email': 'invalid-email'}
        with self.assertRaises(ValueError):
            self.db.add_row('users', invalid_data)

        # Тест читання даних
        rows = self.db.get_rows('users')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['name'], 'John Doe')

        # Тест оновлення даних
        update_success = self.db.update_row('users', row_id,
                                            {'name': 'John Updated', 'age': '26', 'email': 'john@company.com'})
        self.assertTrue(update_success)

        # Перевірка оновлення
        rows = self.db.get_rows('users')
        self.assertEqual(rows[0]['name'], 'John Updated')

        # Тест видалення даних
        delete_success = self.db.delete_row('users', row_id)
        self.assertTrue(delete_success)

        # Перевірка видалення
        rows = self.db.get_rows('users')
        self.assertEqual(len(rows), 0)

        print("✅ Тест 2 пройдено: Валідація та CRUD операції працюють")

    def test_3_table_intersection_individual(self):
        """Тест 3: Індивідуальна операція - перетин таблиць"""
        # Визначення enum
        self.db.define_enum('dept', ['IT', 'HR'])

        # Створення двох таблиць зі спільними полями
        fields1 = {
            'emp_name': {'type': DataType.STRING},
            'department': {'type': DataType.ENUM, 'enum_name': 'dept'}
        }
        fields2 = {
            'proj_name': {'type': DataType.STRING},
            'department': {'type': DataType.ENUM, 'enum_name': 'dept'}
        }

        self.db.create_table('employees', fields1)
        self.db.create_table('projects', fields2)

        # Додавання даних
        self.db.add_row('employees', {'emp_name': 'John', 'department': 'IT'})
        self.db.add_row('employees', {'emp_name': 'Jane', 'department': 'HR'})
        self.db.add_row('employees', {'emp_name': 'Bob', 'department': 'IT'})

        self.db.add_row('projects', {'proj_name': 'Website', 'department': 'IT'})
        self.db.add_row('projects', {'proj_name': 'HR System', 'department': 'HR'})
        self.db.add_row('projects', {'proj_name': 'Mobile App', 'department': 'IT'})

        # Виконання перетину таблиць
        result_table = self.db.intersect_tables('employees', 'projects', ['department'])

        # Перевірка результату
        rows = self.db.get_rows(result_table)
        self.assertEqual(len(rows), 2)  # Два унікальні відділи

        # Перевірка вмісту
        departments = [row['department'] for row in rows]
        self.assertIn('IT', departments)
        self.assertIn('HR', departments)

        print("✅ Тест 3 пройдено: Перетин таблиць працює")

    def test_4_save_and_load_database(self):
        """Тест 4: Збереження та завантаження бази даних (додатковий)"""
        # Створення тестової структури
        self.db.define_enum('status', ['active', 'inactive'])
        fields = {
            'name': {'type': DataType.STRING},
            'status': {'type': DataType.ENUM, 'enum_name': 'status'}
        }
        self.db.create_table('test_table', fields)

        # Додавання тестових даних
        self.db.add_row('test_table', {'name': 'Test User', 'status': 'active'})

        # Збереження
        self.db.save_to_disk('test_save.json')
        self.assertTrue(os.path.exists('test_save.json'))

        # Завантаження в новий об'єкт
        new_db = Database('loaded_db')
        new_db.load_from_disk('test_save.json')

        # Перевірка, що структура збережена
        self.assertEqual(len(new_db.tables), 1)
        self.assertEqual(new_db.tables[0]['name'], 'test_table')

        # Перевірка enum definitions
        self.assertIn('status', new_db.enum_definitions)
        self.assertEqual(new_db.enum_definitions['status'], ['active', 'inactive'])

        # Очищення
        if os.path.exists("databases/loaded_db.db"):
            os.remove("databases/loaded_db.db")

        print("✅ Тест 4 пройдено: Збереження/завантаження працює")


def run_tests():
    """Запуск тестів з детальним виводом"""
    print("🚀 ЗАПУСК ТЕСТІВ СИСТЕМИ УПРАВЛІННЯ БАЗАМИ ДАНИХ")
    print("=" * 60)
    print("📋 Умова: 3+ тести, один для індивідуальної операції")
    print("=" * 60)

    # Створюємо test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDatabaseSystem)

    # Запускаємо тести
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 60)
    print("📊 РЕЗУЛЬТАТИ ТЕСТУВАННЯ:")
    print(f"✅ Успішних тестів: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Провалених тестів: {len(result.failures)}")
    print(f"⚠️  Тестів з помилками: {len(result.errors)}")

    if result.wasSuccessful():
        print("🎉 ВСІ ТЕСТИ ПРОЙДЕНО УСПІШНО!")
        print("📝 Система відповідає вимогам:")
        print("   • Підтримка типів: integer, real, char, string, enum, email ✓")
        print("   • Створення БД та таблиць ✓")
        print("   • Валідація даних ✓")
        print("   • CRUD операції ✓")
        print("   • Перетин таблиць (індивідуальна операція) ✓")
        print("   • Збереження/завантаження ✓")
    else:
        print("💥 Є ПРОБЛЕМИ З ТЕСТАМИ!")

    return result.wasSuccessful()


if __name__ == '__main__':
    run_tests()