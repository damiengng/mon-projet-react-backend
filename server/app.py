from flask import Flask, request, jsonify
import os
import shutil
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///organizer.db'
db = SQLAlchemy(app)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    path = db.Column(db.String(255))

# Nouvelle route pour trier les fichiers
@app.route('/sort_files', methods=['POST'])
def sort_files():
    File.query.delete()
    data = request.get_json()
    chemin_source = data.get('chemin_source')
    chemin_destination = data.get('chemin_destination')

    print("Chemin source:", chemin_source)
    print("Chemin destination:", chemin_destination)

    if not chemin_source or not chemin_destination:
        return jsonify({'erreur': 'Les chemins source et destination sont nécessaires'}), 400

    extensions = {
        'texte': ['.txt'],
        'pdf': ['.pdf'],
        'image': ['.png', '.gif', '.jpeg', '.jpg'],
        'html': ['.html', '.htm']
    }

    for dossier_parent, dossiers, fichiers in os.walk(chemin_source):
        for fichier in fichiers:
            chemin_fichier_source = os.path.join(dossier_parent, fichier)

            # Vérifier si le fichier existe avant de le traiter
            if not os.path.exists(chemin_fichier_source):
                print(f"Le fichier {chemin_fichier_source} n'existe pas. Ignoré.")
                continue

            _, extension = os.path.splitext(fichier)
            dossier_destination = None

            for dossier, exts in extensions.items():
                if extension.lower() in exts:
                    dossier_destination = dossier
                    break

            if dossier_destination is None:
                continue

            chemin_dossier_destination = os.path.join(chemin_destination, dossier_destination)
            os.makedirs(chemin_dossier_destination, exist_ok=True)

            shutil.move(chemin_fichier_source, os.path.join(chemin_dossier_destination, fichier))

            # Vérifier si le fichier existe après le déplacement
            chemin_fichier_destination = os.path.join(chemin_dossier_destination, fichier)
            if not os.path.exists(chemin_fichier_destination):
                print(f"Le fichier {chemin_fichier_destination} n'existe pas après le déplacement. Ignoré.")
                continue

            file_data = {
                'name': fichier,
                'size': os.path.getsize(chemin_fichier_destination),  # Utilise le chemin destination
                'file_type': dossier_destination,
                'path': chemin_fichier_source,

            }
            db.session.add(File(**file_data))
            db.session.commit()

    return jsonify({'message': 'Fichiers triés avec succès'}), 200


# Nouvelle route pour obtenir les données
@app.route('/api/get_files', methods=['GET'])
def get_files():
    files = File.query.all()
    files_data = [{'name': file.name, 'size': file.size, 'file_type': file.file_type, 'path': file.path} for file in files]
    return jsonify(files_data)

@app.route('/clean_database', methods=['POST'])
def clean_database():
    File.query.delete()
    db.session.commit()
    return jsonify({'message': 'Base de données nettoyée avec succès'}), 200


if __name__ == '__main__':
    app.run(debug=True)

