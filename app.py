from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
from sqlalchemy.dialects.postgresql import JSON  # Для хранения данных как JSON

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///access.db'
app.config['SECRET_KEY'] = 'key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
admin = Admin(app, name='Admin Panel', template_mode='bootstrap3')

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    serial = db.Column(db.String(50), unique=True, nullable=False)
    access = db.Column(JSON, nullable=False)  # Используем JSON для списка

    def __repr__(self):
        return f'<User {self.fullname}>, SN: {self.serial}'

class UserAdminView(ModelView):
    column_list = ['id', 'fullname', 'serial', 'access']
    column_searchable_list = ['fullname', 'serial']
    column_filters = ['serial']
    form_edit_rules = ['fullname', 'serial', 'access']
    form_create_rules = ['fullname', 'serial', 'access']

    def on_model_change(self, form, model, is_created):
        if is_created:
            print(f"Создан новый пользователь: {model.fullname}")

admin.add_view(UserAdminView(User, db.session))

def check_access(serial, rooms):
    user = User.query.filter_by(serial=serial).first()

    if not user:
        return False, "Пользователь не найден"

    # Проверка, что хотя бы одна из запрашиваемых комнат есть в доступе пользователя
    if any(room in user.access for room in rooms):
        return True, "Доступ разрешен"
    else:
        return False, "Доступа нет"

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    serial = data.get('serial')
    rooms = data.get('rooms')

    if not serial or not rooms:
        return jsonify({"error": "Необходимы serial_number и room_number"}), 400

    # Преобразуем комнаты в целые числа, если это необходимо
    access, message = check_access(serial, rooms)
    return jsonify({"access": access, "message": message})

if __name__ == '__main__':
    app.run(debug=True)
