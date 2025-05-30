import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template
import base64
from io import BytesIO
from datetime import datetime
import os
import sys

def generate_jmeter_report():
    try:
        print("🔍 Lecture du fichier results.jtl...")
        if not os.path.exists("results.jtl"):
            raise FileNotFoundError("Le fichier results.jtl n'existe pas")
            
        df = pd.read_csv("results.jtl")

        required_columns = ['success']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Colonne requise manquante: {col}. Colonnes disponibles : {', '.join(df.columns)}")

        print("🧮 Calcul des statistiques...") 
        total_tests = len(df)
        passed = df[df['success'] == True].shape[0]
        failed = df[df['success'] == False].shape[0]
        success_rate = round((passed / total_tests) * 100, 2) if total_tests > 0 else 0
        failure_rate = round((failed / total_tests) * 100, 2) if total_tests > 0 else 0

        print("📊 Génération du graphique...")
        plt.switch_backend('Agg')
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.set_style("whitegrid")
        plt.style.use('ggplot')
        colors = ['#4CAF50', '#F44336']
        ax.pie([passed, failed],
               labels=['Réussis', 'Échoués'],
               autopct='%1.1f%%',
               colors=colors,
               startangle=90,
               wedgeprops={'edgecolor': 'white', 'linewidth': 1})
        ax.set_title('Résultats des Tests', fontsize=14, pad=20)

        print("🖼 Conversion du graphique...")
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close(fig)
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        print("📋 Préparation du tableau des résultats...")
        columns_needed = ['label', 'success', 'responseMessage', 'responseCode', 'elapsed']
        available_cols = [col for col in columns_needed if col in df.columns]
        df_details = df[available_cols].copy()
        df_details['status'] = df_details['success'].apply(lambda x: '✅ Réussi' if x else '❌ Échoué')

        details_html = df_details.to_html(
            index=False,
            classes='results-table',
            justify='center',
            border=0,
            escape=False
        )

        print("📝 Création du rapport HTML...")
        html_template = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Rapport JMeter</title>
    <style>
        :root {
            --success-color: #4CAF50;
            --failure-color: #F44336;
            --primary-color: #2196F3;
            --background-color: #f5f7fa;
            --card-color: #ffffff;
            --text-color: #333333;
            --border-radius: 12px;
            --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
            padding: 20px;
            margin: 0;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .card {
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            padding: 30px;
            margin-bottom: 30px;
        }

        h1, h2 {
            color: var(--primary-color);
            text-align: center;
        }

        .stats-container {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            margin: 30px 0;
        }
        
        .stat-box {
            text-align: center;
            padding: 20px;
            border-radius: var(--border-radius);
            margin: 10px;
            flex: 1;
            min-width: 200px;
            background-color: #f8f9fa;
        }

        .stat-value {
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }

        .success {
            color: var(--success-color);
        }

        .failure {
            color: var(--failure-color);
        }

        .chart-container {
            text-align: center;
            margin: 30px 0;
        }

        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: var(--border-radius);
        }

        .summary {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: var(--border-radius);
            margin-top: 20px;
        }

        .results-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        .results-table th, .results-table td {
            border: 1px solid #ccc;
            padding: 10px;
            text-align: left;
        }

        .results-table th {
            background-color: #f0f0f0;
            color: #333;
        }

        .footer {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>📊 Rapport de Test JMeter</h1>
            <div class="stats-container">
                <div class="stat-box">
                    <div>Tests Exécutés</div>
                    <div class="stat-value">{{ total }}</div>
                    <div>🧪 Total</div>
                </div>
                <div class="stat-box">
                    <div>Taux de Réussite</div>
                    <div class="stat-value success">{{ success }}%</div>
                    <div>✅ Succès</div>
                </div>
                <div class="stat-box">
                    <div>Taux d'Échec</div>
                    <div class="stat-value failure">{{ failure }}%</div>
                    <div>❌ Échecs</div>
                </div>
            </div>

            <div class="chart-container">
                <h2>Répartition des Résultats</h2>
                <img src="data:image/png;base64,{{ img_data }}" alt="Résultats des tests"/>
            </div>

            <div class="summary">
                <h2>Résumé</h2>
                <p>Les tests JMeter ont été exécutés avec succès avec un taux de réussite de {{ success }}%.</p>
                <p>Sur les {{ total }} tests exécutés, {{ passed }} ont réussi et {{ failed }} ont échoué.</p>
                {% if failure_rate == 0 %}
                <p style="color: var(--success-color); font-weight: bold;">🎉 Tous les tests ont réussi !</p>
                {% else %}
                <p style="color: var(--failure-color);">⚠️ Attention : certains tests ont échoué.</p>
                {% endif %}
            </div>
        </div>

        <div class="card">
            <h2>Détails des Tests</h2>
            <p>Ci-dessous la liste complète des tests exécutés avec leurs statuts et messages.</p>
            {{ details_table | safe }}
        </div>

        <div class="footer">
            Rapport généré le {{ date }} | JMeter Test Report
        </div>
    </div>
</body>
</html>
"""

        template = Template(html_template)
        html_content = template.render(
            total=total_tests,
            success=success_rate,
            failure=failure_rate,
            passed=passed,
            failed=failed,
            failure_rate=failure_rate,
            img_data=img_base64,
            details_table=details_html,
            date=datetime.now().strftime("%d/%m/%Y %H:%M")
        )

        output_file = "jmeter_custom_report.html"
        with open(output_file, "w", encoding='utf-8') as f:
            f.write(html_content)

        if not os.path.exists(output_file):
            raise RuntimeError("Le fichier HTML n'a pas pu être créé")

        print(f"✅ Rapport généré avec succès : {output_file}")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport : {str(e)}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = generate_jmeter_report()
    sys.exit(0 if success else 1)
