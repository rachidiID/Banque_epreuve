"""
Script de test pour les endpoints de recommandation
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def get_token(username='etudiant1', password='password123'):
    """Obtenir un token JWT"""
    response = requests.post(f"{BASE_URL}/api/token/", json={
        'username': username,
        'password': password
    })
    if response.status_code == 200:
        return response.json()['access']
    return None

def test_personalized_recommendations(token):
    """Tester les recommandations personnalisées"""
    print("\n" + "="*60)
    print("TEST: Recommandations personnalisées")
    print("="*60)
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f"{BASE_URL}/api/recommendations/personalized/?top_k=5",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Utilisateur: {data['username']} (Niveau: {data['niveau']})")
        print(f"Nombre de recommandations: {data['count']}\n")
        
        for i, rec in enumerate(data['recommendations'][:5], 1):
            print(f"{i}. {rec['titre']}")
            print(f"   Score: {rec['score']:.4f} | {rec['matiere']} | {rec['niveau']}")
    else:
        print(f"Erreur: {response.text}")

def test_similar_epreuves(token, epreuve_id=1):
    """Tester les épreuves similaires"""
    print("\n" + "="*60)
    print("TEST: Épreuves similaires")
    print("="*60)
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f"{BASE_URL}/api/recommendations/similar/?epreuve_id={epreuve_id}&top_k=5",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Épreuve de référence: {data['epreuve_titre']}")
        print(f"Nombre d'épreuves similaires: {data['count']}\n")
        
        for i, sim in enumerate(data['similar_epreuves'][:5], 1):
            print(f"{i}. {sim['titre']}")
            print(f"   Similarité: {sim['similarity_score']:.4f} | {sim['matiere']} | {sim['niveau']}")
    else:
        print(f"Erreur: {response.text}")

def test_model_status(token):
    """Tester le statut du modèle"""
    print("\n" + "="*60)
    print("TEST: Statut du modèle")
    print("="*60)
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f"{BASE_URL}/api/recommendations/status/",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Statut: {data['status']}")
        print(f"Version: {data['model_version']}")
        print(f"Architecture: {data['architecture']}")
        
        if 'metrics' in data:
            metrics = data['metrics']
            print(f"\nMétriques:")
            print(f"  RMSE: {metrics['rmse']:.4f}")
            print(f"  Precision@10: {metrics['precision_at_10']:.4f}")
            print(f"  Recall@10: {metrics['recall_at_10']:.4f}")
    else:
        print(f"Erreur: {response.text}")

def test_stats(token):
    """Tester les statistiques"""
    print("\n" + "="*60)
    print("TEST: Statistiques")
    print("="*60)
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f"{BASE_URL}/api/recommendations/stats/",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        user_stats = data['user_stats']
        print(f"Statistiques utilisateur:")
        print(f"  Total interactions: {user_stats['total_interactions']}")
        print(f"  Épreuves vues: {user_stats['unique_epreuves_viewed']}")
        print(f"  Épreuves téléchargées: {user_stats['unique_epreuves_downloaded']}")
    else:
        print(f"Erreur: {response.text}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Tests des endpoints de recommandation")
    print("="*60)
    
    # Obtenir le token
    print("\n🔑 Authentification...")
    token = get_token()
    
    if not token:
        print("❌ Échec de l'authentification. Assurez-vous que le serveur est lancé.")
        exit(1)
    
    print("✅ Authentification réussie")
    
    # Tests
    test_model_status(token)
    test_personalized_recommendations(token)
    test_similar_epreuves(token, epreuve_id=1)
    test_stats(token)
    
    print("\n" + "="*60)
    print("✅ Tous les tests terminés!")
    print("="*60 + "\n")
