import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
from collections import defaultdict

class EnhancedOneRScammerDetector:
    def __init__(self, rejection_threshold=0.7):
        self.rejection_threshold = rejection_threshold
        self.rules = {}
        self.price_ranges = {
            'scammer': (0, 5),
            'borderline': (5, 13),
            'legitimate': (13, float('inf'))
        }
        self.is_fitted = False
        
    def _get_price_category(self, price):
        if price <= self.price_ranges['scammer'][1]:
            return 'scammer', 0.95
        elif price >= self.price_ranges['legitimate'][0]:
            return 'legitimate', 0.95
        else:
            return 'borderline', 0.5
            
    def _calculate_confidence(self, price, is_new):
        category, base_confidence = self._get_price_category(price)
        
        # Aggiorniamo i calcoli della confidenza basandoci sulle statistiche del training
        if hasattr(self, 'price_stats'):
            if category == 'scammer':
                # Confronta con la distribuzione degli scammer nel training
                z_score = abs((price - self.price_stats['scammer']['mean']) / self.price_stats['scammer']['std'])
                base_confidence = max(0.5, min(0.95, 1 - (z_score * 0.1)))
            elif category == 'legitimate':
                z_score = abs((price - self.price_stats['legitimate']['mean']) / self.price_stats['legitimate']['std'])
                base_confidence = max(0.5, min(0.95, 1 - (z_score * 0.1)))
        
        if category == 'borderline':
            if is_new:
                confidence = 0.85
                prediction = 1
            else:
                confidence = 0.4
                prediction = -1
            
            distance_to_scammer = abs(price - self.price_ranges['scammer'][1])
            distance_to_legitimate = abs(price - self.price_ranges['legitimate'][0])
            
            if distance_to_scammer < distance_to_legitimate:
                confidence = min(confidence + 0.1, 0.95)
            else:
                confidence = max(confidence - 0.1, 0.05)
        else:
            prediction = 1 if category == 'scammer' else 0
            confidence = base_confidence
            
            if category == 'scammer' and price < 2:
                confidence = 0.99
            elif category == 'legitimate' and price > 20:
                confidence = 0.99
                
        return prediction, confidence
        
    def fit(self, X, y):
        """
        Fit del modello sui dati di training
        """
        self.price_stats = {
            'scammer': {
                'mean': X.loc[y == 1, 'avg_price'].mean(),
                'std': X.loc[y == 1, 'avg_price'].std()
            },
            'legitimate': {
                'mean': X.loc[y == 0, 'avg_price'].mean(),
                'std': X.loc[y == 0, 'avg_price'].std()
            }
        }
        
        # Analisi della distribuzione dei prezzi per categoria
        print("\nStatistiche di training:")
        print("\nDistribuzione dei prezzi:")
        for category in ['scammer', 'legitimate']:
            stats = self.price_stats[category]
            print(f"{category.capitalize()} - Media: {stats['mean']:.2f}, STD: {stats['std']:.2f}")
        
        # Analisi della distribuzione nuovo/usato
        self.new_used_stats = {
            'scammer': {
                'new': np.sum((y == 1) & X['is_new']),
                'used': np.sum((y == 1) & ~X['is_new'])
            },
            'legitimate': {
                'new': np.sum((y == 0) & X['is_new']),
                'used': np.sum((y == 0) & ~X['is_new'])
            }
        }
        
        print("\nDistribuzione nuovo/usato:")
        for category, stats in self.new_used_stats.items():
            print(f"{category.capitalize()} - Nuovo: {stats['new']}, Usato: {stats['used']}")
        
        self.is_fitted = True
        return self

    def predict(self, X):
        """
        Effettua predizioni su nuovi dati
        """
        if not self.is_fitted:
            raise Exception("Il modello deve essere prima addestrato con fit()")
            
        predictions = []
        confidences = []
        detailed_results = []
        
        for idx, row in X.iterrows():
            price = row['avg_price']
            is_new = row['is_new']
            
            prediction, confidence = self._calculate_confidence(price, is_new)
            
            predictions.append(prediction)
            confidences.append(confidence)
            
            category, _ = self._get_price_category(price)
            detailed_results.append({
                'price': price,
                'is_new': is_new,
                'category': category,
                'prediction': prediction,
                'confidence': confidence
            })
            
        self.detailed_results = pd.DataFrame(detailed_results)
        return np.array(predictions), np.array(confidences)

def prepare_synthetic_data(n_samples=1000):
    """
    Prepara dati sintetici per test
    """
    data = {
        'avg_price': [],
        'is_new': [],
        'is_scammer': []
    }
    
    # Genera dati per scammer
    n_scammers = int(n_samples * 0.3)  # 30% scammer
    for _ in range(n_scammers):
        if np.random.random() < 0.1:  # 10% borderline
            price = np.random.uniform(5, 13)
        else:
            price = np.random.uniform(1, 5)
        is_new = np.random.choice([True, False], p=[0.8, 0.2])
        
        data['avg_price'].append(price)
        data['is_new'].append(is_new)
        data['is_scammer'].append(1)
    
    # Genera dati per venditori legittimi
    n_legitimate = n_samples - n_scammers
    for _ in range(n_legitimate):
        if np.random.random() < 0.1:  # 10% borderline
            price = np.random.uniform(5, 13)
        else:
            price = np.random.uniform(13, 50)
        is_new = np.random.choice([True, False], p=[0.2, 0.8])
        
        data['avg_price'].append(price)
        data['is_new'].append(is_new)
        data['is_scammer'].append(0)
    
    return pd.DataFrame(data)

def evaluate_model_with_split(include_real_samples=True):
    """
    Valuta il modello con train/test split e casi reali
    """
    # Prepara i dati sintetici
    df = prepare_synthetic_data()
    
    # Aggiungi casi reali verificati. dallo scraping prima e check manualmente poi hai identificato in maniera univoca casi di scammer/non_scammer
    if include_real_samples:
        real_samples = pd.DataFrame({
            'avg_price': [
                3.00,    # Scammer verificato - prezzo molto basso, nuovo con scatola, sigillati
                38.50,   # Legittimo verificato - prezzo normale, usato; in particolare era un collezionista con due pezzi a 110
                2.50,    # Scammer verificato - prezzo basso, nuovo e sigillato
                30.00,   # Legittimo verificato - prezzo medio, usato, altro collezionista
                7.99,    # Scammer verificato - prezzo borderline ma nuovo
                120.00,  # Legittimo verificato - prezzo alto, usato, pochi pezzi ma molto expensive
                4.00,    # Scammer verificato - prezzo molto basso, nuovo, tantissimi allo stesso prezzo
                90.00    # Legittimo verificato - prezzo alto, usato
            ],
            'is_new': [
                True,   # Scammer
                False,  # Legittimo
                True,   # Scammer
                False,  # Legittimo
                True,   # Scammer
                False,  # Legittimo
                True,   # Scammer
                False   # Legittimo
            ],
            'is_scammer': [1, 0, 1, 0, 1, 0, 1, 0]          #label, i campioni sopra sono tutti etichettati, questi aggiunti ai casi sintetici. Generalmente corrisponde all'ultima colonna nelle tabelle, dove appunto c'è la label dei rispettivi campioni per l'addestramento
        })
        df = pd.concat([df, real_samples], ignore_index=True)
    
    # Dividi in train e test
    X = df[['avg_price', 'is_new']]
    y = df['is_scammer']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Addestra e valuta il modello
    detector = EnhancedOneRScammerDetector(rejection_threshold=0.7)
    detector.fit(X_train, y_train)
    predictions, confidences = detector.predict(X_test)
    
    # Stampa risultati
    print("\nRisultati sul test set:")
    valid_mask = predictions != -1
    print("\nReport di classificazione (esclusi i casi rejected):")
    print(classification_report(y_test[valid_mask], predictions[valid_mask]))
    
    # Statistiche sui casi rejected
    rejected_mask = predictions == -1
    n_rejected = np.sum(rejected_mask)
    print(f"\nCasi rejected nel test set: {n_rejected} ({n_rejected/len(predictions)*100:.2f}%)")
    
    if n_rejected > 0:
        rejected_data = X_test[rejected_mask]
        print("\nAnalisi dei casi rejected:")
        print(f"Prezzo medio: {rejected_data['avg_price'].mean():.2f}")
        print(f"% Nuovo: {(rejected_data['is_new'].sum()/n_rejected*100):.2f}%")
    
    # Crea visualizzazioni
    plot_results(detector, X_test, y_test, predictions, confidences)
    
    return detector

def plot_results(detector, X_test, y_test, predictions, confidences):
    """
    Crea visualizzazioni dei risultati
    """
    plt.figure(figsize=(15, 10))
    
    # Subplot 1: Scatter plot dei prezzi vs confidenza
    plt.subplot(2, 2, 1)
    colors = np.where(predictions == 1, 'red', np.where(predictions == 0, 'green', 'gray'))
    plt.scatter(X_test['avg_price'], confidences, c=colors, alpha=0.6)
    plt.axvline(x=5, color='gray', linestyle='--', alpha=0.5)
    plt.axvline(x=13, color='gray', linestyle='--', alpha=0.5)
    plt.fill_between([5, 13], 0, 1, color='yellow', alpha=0.1)
    plt.xlabel('Prezzo')
    plt.ylabel('Confidenza')
    plt.title('Distribuzione Prezzi vs Confidenza')
    
    # Subplot 2: Confusion Matrix
    plt.subplot(2, 2, 2)
    valid_mask = predictions != -1
    cm = confusion_matrix(y_test[valid_mask], predictions[valid_mask])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Matrice di Confusione')
    plt.ylabel('Label Vera')
    plt.xlabel('Label Predetta')
    
    # Subplot 3: Distribuzione dei prezzi per categoria
    plt.subplot(2, 2, 3)
    sns.boxplot(x=y_test, y=X_test['avg_price'])
    plt.axhline(y=5, color='r', linestyle='--', alpha=0.5)
    plt.axhline(y=13, color='r', linestyle='--', alpha=0.5)
    plt.xlabel('Categoria (0=Legitimo, 1=Scammer)')
    plt.ylabel('Prezzo')
    plt.title('Distribuzione dei Prezzi per Categoria')
    
    # Subplot 4: Stato nuovo/usato per categoria
    plt.subplot(2, 2, 4)
    data = pd.DataFrame({
        'Categoria': ['Scammer', 'Scammer', 'Legitimo', 'Legitimo'],
        'Stato': ['Nuovo', 'Usato', 'Nuovo', 'Usato'],
        'Conteggio': [
            sum((y_test == 1) & (X_test['is_new'])),
            sum((y_test == 1) & (~X_test['is_new'])),
            sum((y_test == 0) & (X_test['is_new'])),
            sum((y_test == 0) & (~X_test['is_new']))
        ]
    })
    sns.barplot(x='Categoria', y='Conteggio', hue='Stato', data=data)
    plt.title('Distribuzione Nuovo/Usato per Categoria')
    
    plt.tight_layout()
    plt.show()

def test_new_samples(detector, samples):
    """
    Testa il modello su nuovi campioni
    """
    if not isinstance(samples, pd.DataFrame):
        samples = pd.DataFrame(samples)
    
    predictions, confidences = detector.predict(samples)
    
    results = []
    for i, (pred, conf) in enumerate(zip(predictions, confidences)):
        status = "Rejected" if pred == -1 else ("Scammer" if pred == 1 else "Legitimate")
        results.append({
            'Sample': i + 1,
            'Price': samples.iloc[i]['avg_price'],
            'Is New': samples.iloc[i]['is_new'],
            'Prediction': status,
            'Confidence': f"{conf:.2%}"
        })
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    # Addestra e valuta il modello
    detector = evaluate_model_with_split()
    
    # Test su casi reali aggiuntivi. Sono GROUND TRUTH che ho checkato tramite scraping prima e manualmente dopo. Rispetto a riga 187, NON c'è più la label ma riportate solo le 2 rispettivi feature. 
    print("\nTest su casi reali aggiuntivi:")
    real_test_cases = {
        'avg_price': [                          #fase INFERENZA: confronti le predizioni con le ground truth e vedi se matchano!
            4.50,    # scammer
            199.99,  # legittimo            in particolare "cat life series" modello raro da collezione
            8.99,    # Caso borderline
            25.00    # legittimo
        ],
        'is_new': [
            True,    # Nuovo a prezzo bassissimo
            False,   # Usato a prezzo alto
            True,    # Nuovo a prezzo borderline
            False    # Usato a prezzo medio
        ]
    }
    
    results = test_new_samples(detector, real_test_cases)
    print(results)