# Configuration du connecteur MCP data.gouv.fr sur Claude Desktop (Windows)

## Prérequis

- [Node.js](https://nodejs.org/) installé (v18+ recommandé)
- `mcp-remote` installé globalement :

```bash
npm install -g mcp-remote
```

## Configuration

Fichier : `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "datagouv": {
      "command": "npx",
      "args": ["mcp-remote", "https://mcp.data.gouv.fr/mcp"]
    }
  }
}
```

## Problème connu : serveur MCP non chargé

Si le serveur datagouv apparaît dans la liste mais ne se connecte pas (pas de handshake, outils non disponibles), vérifier le paramètre `isUsingBuiltInNodeForMcp` dans le même fichier de config.

### Cause

Claude Desktop embarque son propre Node.js. Quand `isUsingBuiltInNodeForMcp` est à `true` (valeur par défaut), il utilise ce Node interne qui ne voit pas les paquets npm installés globalement sur le Node système (comme `mcp-remote`).

### Fix

Ajouter à la racine du fichier de config :

```json
{
  "isUsingBuiltInNodeForMcp": false,
  "mcpServers": {
    "datagouv": {
      "command": "npx",
      "args": ["mcp-remote", "https://mcp.data.gouv.fr/mcp"]
    }
  }
}
```

### Vérification

Après redémarrage de Claude Desktop, le serveur doit afficher :
- Nom : `data.gouv.fr MCP server`
- Version : `1.26.0` (ou supérieure)
- 9 outils disponibles : `search_datasets`, `search_dataservices`, `get_dataset_info`, `list_dataset_resources`, `get_resource_info`, `query_resource_data`, `get_dataservice_info`, `get_dataservice_openapi_spec`, `get_metrics`

## Outils disponibles

| Outil | Usage |
|---|---|
| `search_datasets` | Recherche de jeux de données par mots-clés |
| `list_dataset_resources` | Liste les fichiers (CSV, JSON...) d'un dataset |
| `query_resource_data` | Requête tabulaire sur un CSV/XLSX sans téléchargement |
| `get_resource_info` | Métadonnées d'un fichier (taille, format, URL) |
| `get_dataset_info` | Métadonnées d'un dataset (description, licence, dates) |
| `get_metrics` | Statistiques de téléchargement/consultation |
| `search_dataservices` | Recherche d'APIs tierces référencées |
| `get_dataservice_info` | Détail d'une API tierce |
| `get_dataservice_openapi_spec` | Spécification OpenAPI d'une API tierce |

## Note sur les gros fichiers

L'outil `query_resource_data` utilise l'API tabulaire de data.gouv.fr, qui ne fonctionne pas sur tous les CSV (notamment les fichiers volumineux). Dans ce cas, utiliser `get_resource_info` pour récupérer l'URL directe du fichier et le télécharger via `pd.read_csv(url)`.
