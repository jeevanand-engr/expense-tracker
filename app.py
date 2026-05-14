from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///expenses.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Expense(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    title    = db.Column(db.String(100), nullable=False)
    amount   = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), default='Other')

    def to_dict(self):
        return {'id': self.id, 'title': self.title, 'amount': self.amount, 'category': self.category}

with app.app_context():
    db.create_all()

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'version': '2.0', 'app': 'expense-tracker'})

@app.route('/expenses', methods=['GET'])
def get_expenses():
    expenses = Expense.query.all()
    return jsonify([e.to_dict() for e in expenses])

@app.route('/expenses', methods=['POST'])
def add_expense():
    data = request.get_json()
    if not data or 'title' not in data or 'amount' not in data:
        return jsonify({'error': 'title and amount are required'}), 400
    e = Expense(title=data['title'], amount=data['amount'], category=data.get('category', 'Other'))
    db.session.add(e)
    db.session.commit()
    return jsonify({'message': 'Expense added', 'expense': e.to_dict()}), 201

@app.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    e = Expense.query.get_or_404(expense_id)
    db.session.delete(e)
    db.session.commit()
    return jsonify({'message': f'Expense {expense_id} deleted'})

@app.route('/expenses/summary', methods=['GET'])
def summary():
    expenses = Expense.query.all()
    total = sum(e.amount for e in expenses)
    by_category = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount
    return jsonify({'total': total, 'by_category': by_category, 'count': len(expenses)})

@app.route('/break', methods=['GET'])
def break_app():
    result = 1 / 0  # Division by zero — causes 500 error
    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
