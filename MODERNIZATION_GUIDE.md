# 🚀 Kyra Bot - Guide de Modernisation v2.0

## 📋 Résumé des Changements

Cette mise à jour modernise le code du bot Discord Kyra avec un code plus propre, maintenable et efficace.

---

## ✨ Quoi de Neuf ?

### 1. **Suppression de Flask/Quart**
- ❌ Supprimé `Quart` des dépendances principales
- ✅ Service webhook `top-gg` déplacé vers dossier séparé : `top-gg-STANDALONE-DEPLOYMENT/`
- 📝 Ce service est maintenant clairement marqué comme indépendant
- 💡 Le bot principal est plus léger sans dépendances web

### 2. **Système de Configuration Centralisé** (`utils/config.py`)
- ✅ Tous les paramètres du bot en un seul endroit
- ✅ Configuration centralisée des emojis avec classes `Colors` et `Emojis`
- ✅ Facile de personnaliser couleurs et emojis
- ✅ Documentation claire pour chaque paramètre

**Exemple d'utilisation :**
```python
from utils.config import Colors, Emojis, BOT_NAME

# Utiliser les couleurs centralisées
embed = discord.Embed(color=Colors.SUCCESS)

# Utiliser les emojis centralisés
await ctx.send(f"{Emojis.SUCCESS} Commande exécutée !")
```

### 3. **Gestionnaire de Base de Données** (`utils/database.py`)
- ✅ Opérations de base de données centralisées
- ✅ Context manager pour connexions sécurisées
- ✅ Méthodes helpers pour opérations courantes
- ✅ Initialisation automatique au démarrage

**Exemple d'utilisation :**
```python
from utils.database import DatabaseManager

# Vérifier si utilisateur a no-prefix
is_np = await DatabaseManager.is_np_user(user_id)

# Ajouter utilisateur no-prefix
await DatabaseManager.add_np_user(user_id)
```

### 4. **Chargement Automatique des Cogs** (`cogs/__init__.py`)
- ✅ Groupes de cogs organisés (commands, events, antinuke, automod, moderation)
- ✅ Belle sortie de chargement avec statuts colorés
- ✅ Plus besoin de `await bot.add_cog()` manuel
- ✅ Facile d'ajouter de nouveaux cogs

### 5. **Main.py Modernisé**
- ✅ Code propre et bien documenté
- ✅ Meilleure gestion d'erreurs
- ✅ Logging de commandes amélioré
- ✅ Gestion d'arrêt gracieuse
- ✅ Initialisation DB au démarrage

### 6. **Classe Bot Core Optimisée** (`core/Olympus.py`)
- ✅ Meilleure organisation du code avec docstrings
- ✅ Gestion des préfixes optimisée avec DatabaseManager
- ✅ Type hints améliorés pour meilleur support IDE
- ✅ Gestionnaires d'événements plus propres

---

## 🎯 Avantages

| Avant | Après |
|--------|-------|
| Chargement manuel des cogs (100+ lignes) | Chargement automatique par groupe |
| Couleurs/emojis en dur partout | Centralisés dans config |
| Accès DB direct éparpillé | DatabaseManager unifié |
| Dépendance Flask/Quart inutilisée | Supprimée (top-gg séparé) |
| Structure de code floue | Bien documenté avec docstrings |
| Configuration mixte | Fichier config unique |

---

## 📚 Guide de Migration

### Pour les Changements Emoji/Couleur

**Avant :**
```python
embed = discord.Embed(color=0x000000)
await ctx.send("✅ Fait !")
```

**Après :**
```python
from utils.config import Colors, Emojis

embed = discord.Embed(color=Colors.SUCCESS)
await ctx.send(f"{Emojis.SUCCESS} Fait !")
```

### Pour les Opérations de Base de Données

**Avant :**
```python
async with aiosqlite.connect('db/np.db') as db:
    cursor = await db.execute("SELECT id FROM np WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    is_np = row is not None
```

**Après :**
```python
from utils.database import DatabaseManager

is_np = await DatabaseManager.is_np_user(user_id)
```

---

## 🚀 Lancer le Bot

### Configuration Initiale

1. **Installer les dépendances :**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurer le fichier `.env` :**
   ```bash
   TOKEN=votre_token_discord_bot
   ```

3. **Configurer le bot :**
   - Éditer `utils/config.py` pour définir owner IDs, liens serveur, etc.
   - Personnaliser couleurs et emojis (optionnel)

4. **Lancer le bot :**
   ```bash
   python main.py
   ```

---

## 📝 Ce Qui Reste Identique

- ✅ Toutes les commandes fonctionnent exactement pareil
- ✅ Structure de base de données inchangée
- ✅ Compatibilité rétroactive maintenue
- ✅ Toutes les fonctionnalités préservées
- ✅ Format des fichiers de configuration (.env, config.yml) inchangé

---

## 🐛 Dépannage

### Erreurs "Module not found"
```bash
pip install -r requirements.txt
```

### Erreurs de base de données
Le bot initialisera automatiquement les BDs au premier lancement.

---

**Profitez de votre bot Kyra modernisé ! 🎉**
