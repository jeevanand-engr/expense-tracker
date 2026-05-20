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
    app_env = os.getenv('APP_ENV')
    if not app_env:
        raise ValueError("APP_ENV environment variable is not set!")
    return jsonify({'status': 'ok', 'version': '2.0', 'env': app_env})

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

@app.route('/')
def home():
    expenses = Expense.query.all()
    total = sum(e.amount for e in expenses)
    rows = ''.join([f"<tr><td>{e.id}</td><td>{e.title}</td><td>₹{e.amount}</td><td>{e.category}</td><td><a href='/expenses/{e.id}/delete'>Delete</a></td></tr>" for e in expenses])
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Expense Tracker</title>
        <style>
            body {{ font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }}
            h1 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
            th {{ background: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background: #f2f2f2; }}
            form {{ margin-top: 20px; }}
            input {{ padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }}
            button {{ padding: 8px 16px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }}
            .total {{ font-size: 20px; font-weight: bold; margin-top: 20px; color: #333; }}
        </style>
    </head>
    <body>
        <h1>💰 Expense Tracker</h1>
        <form action="/expenses/add" method="POST">
            <input name="title" placeholder="Title" required>
            <input name="amount" type="number" placeholder="Amount" required>
            <input name="category" placeholder="Category">
            <button type="submit">Add Expense</button>
        </form>
        <table>
            <tr><th>ID</th><th>Title</th><th>Amount</th><th>Category</th><th>Action</th></tr>
            {rows}
        </table>
        <div class="total">Total: ₹{total}</div>
    </body>
    </html>
    """

@app.route('/expenses/add', methods=['POST'])
def add_expense_form():
    from flask import request
    title = request.form.get('title')
    amount = float(request.form.get('amount'))
    category = request.form.get('category', 'Other')
    e = Expense(title=title, amount=amount, category=category)
    db.session.add(e)
    db.session.commit()
    from flask import redirect
    return redirect('/')

@app.route('/expenses/<int:expense_id>/delete')
def delete_expense_ui(expense_id):
    e = Expense.query.get_or_404(expense_id)
    db.session.delete(e)
    db.session.commit()
    from flask import redirect
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
