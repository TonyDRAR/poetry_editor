class FileService:
    def read(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Erreur lecture fichier: {e}")
            return ""

    def write(self, path: str, content: str) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Erreur ecriture fichier: {e}")
            return False
