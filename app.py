from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_materials.db'
db = SQLAlchemy(app)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('index.html', projects=projects)

@app.route('/project/<int:project_id>')
def project_details(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_details.html', project=project)

@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.json
    new_project = Project(
        title=data['title'],
        prompt=data['prompt']
    )
    db.session.add(new_project)
    db.session.commit()
    return jsonify({
        'id': new_project.id,
        'title': new_project.title,
        'prompt': new_project.prompt,
        'created_at': new_project.created_at.isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True)
