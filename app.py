from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
from sqlalchemy import JSON  # Используем для списков

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///access.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
admin = Admin(app, name='Admin Panel', template_mode='bootstrap3')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    serial = db.Column(db.String(50), unique=True, nullable=False)
    access = db.Column(JSON, nullable=False)  # Доступные комнаты
    taken_keys = db.Column(JSON, nullable=False, default=lambda: [])  # Взятые ключи

    def __repr__(self):
        return f'<User {self.fullname}>, SN: {self.serial}'


class UserAdminView(ModelView):
    column_list = ['id', 'fullname', 'serial', 'access', 'taken_keys']
    column_searchable_list = ['fullname', 'serial']
    column_filters = ['serial']
    form_edit_rules = ['fullname', 'serial', 'access', 'taken_keys']
    form_create_rules = ['fullname', 'serial', 'access', 'taken_keys']

    def on_model_change(self, form, model, is_created):
        if is_created:
            print(f"Создан новый пользователь: {model.fullname}")


admin.add_view(UserAdminView(User, db.session))

@app.route('/issue_key', methods=['POST'])
def issue_key():
    try:
        if not request.is_json:
            return jsonify({"error": "Запрос должен быть в формате JSON"}), 400

        data = request.get_json()

        required_fields = ['serial', 'key']
        if not all(field in data for field in required_fields):
            missing = [field for field in required_fields if field not in data]
            return jsonify({
                "error": f"Отсутствуют обязательные поля: {', '.join(missing)}"
            }), 400

        serial = data['serial']
        key = data['key']

        if not isinstance(serial, str) or not isinstance(key, (str, int)):
            return jsonify({
                "error": "Серийный номер должен быть строкой, а ключ - строкой или числом"
            }), 400

        if not serial.strip() or not str(key).strip():
            return jsonify({
                "error": "Поля не могут быть пустыми или содержать только пробелы"
            }), 400

        user = User.query.filter_by(serial=serial).first()
        if not user:
            return jsonify({
                "error": "Пользователь с указанным серийным номером не найден"
            }), 404

        if str(key) not in map(str, user.access):
            return jsonify({
                "error": "У пользователя нет прав доступа к этому ключу",
                "access": False
            }), 403

        taken_keys = user.taken_keys if user.taken_keys else []
        if str(key) in map(str, taken_keys):
            return jsonify({
                "error": "Данный ключ уже выдан этому пользователю"
            }), 400

        taken_keys.append(key)
        user.taken_keys = taken_keys

        try:
            db.session.commit()
            return jsonify({
                "message": f"Ключ '{key}' успешно выдан пользователю {user.fullname}",
                "access": True
            }), 200
        except Exception as db_error:
            db.session.rollback()
            print(f"Ошибка базы данных: {str(db_error)}")
            return jsonify({
                "error": "Ошибка при сохранении данных в базе"
            }), 500

    except Exception as e:
        print(f"Системная ошибка при выдаче ключа: {str(e)}")
        return jsonify({
            "error": "Внутренняя ошибка сервера"
        }), 500


@app.route('/return_key', methods=['POST'])
def return_key():
    try:
        if not request.is_json:
            return jsonify({"error": "Запрос должен быть в формате JSON"}), 400

        data = request.get_json()

        required_fields = ['serial', 'key']
        if not all(field in data for field in required_fields):
            missing = [field for field in required_fields if field not in data]
            return jsonify({
                "error": f"Отсутствуют обязательные поля: {', '.join(missing)}"
            }), 400

        serial = data['serial']
        key = data['key']

        if not isinstance(serial, str) or not isinstance(key, (str, int)):
            return jsonify({
                "error": "Серийный номер должен быть строкой, а ключ - строкой или числом"
            }), 400

        if not serial.strip() or not str(key).strip():
            return jsonify({
                "error": "Поля не могут быть пустыми или содержать только пробелы"
            }), 400

        user = User.query.filter_by(serial=serial).first()
        if not user:
            return jsonify({
                "error": "Пользователь с указанным серийным номером не найден"
            }), 404

        taken_keys = user.taken_keys if user.taken_keys else []
        if str(key) not in map(str, taken_keys):
            return jsonify({
                "error": "Этот ключ не был выдан данному пользователю",
                "access": False
            }), 400

        user.taken_keys = [k for k in taken_keys if str(k) != str(key)]

        try:
            db.session.commit()
            return jsonify({
                "message": f"Ключ '{key}' успешно возвращен от пользователя {user.fullname}",
                "access": True
            }), 200
        except Exception as db_error:
            db.session.rollback()
            print(f"Ошибка базы данных при возврате ключа: {str(db_error)}")
            return jsonify({
                "error": "Ошибка при обновлении данных в базе"
            }), 500

    except Exception as e:
        print(f"Системная ошибка при возврате ключа: {str(e)}")
        return jsonify({
            "error": "Внутренняя ошибка сервера"
        }), 500


if __name__ == '__main__':
    app.run(debug=True)

