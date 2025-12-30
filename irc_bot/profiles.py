import json
from pathlib import Path
from typing import Dict, Optional

ALLOWED_KEYS = {"age", "gender", "position", "orientation", "location", "limits", "kinks", "seeking", "bio"}


class ProfileStore:
    def __init__(self, path: str = "profiles.json") -> None:
        self.path = Path(path)
        self._data: Dict[str, Dict] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._data = {}
        else:
            self._data = {}
        self._loaded = True

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_profile(self, nick: str) -> Optional[Dict]:
        self._ensure_loaded()
        return self._data.get(nick)

    def clear_profile(self, nick: str) -> None:
        self._ensure_loaded()
        if nick in self._data:
            del self._data[nick]
            self._save()

    def update_profile(self, nick: str, updates: Dict[str, str]) -> Dict:
        self._ensure_loaded()
        profile = dict(self._data.get(nick) or {})
        for k, v in updates.items():
            if k not in ALLOWED_KEYS:
                continue
            if k == "age":
                try:
                    profile[k] = int(v)
                except Exception:
                    profile[k] = v  # store as-is if not int
            else:
                profile[k] = v
        self._data[nick] = profile
        self._save()
        return profile

    @staticmethod
    def parse_updates(tokens: list[str]) -> Dict[str, str]:
        updates: Dict[str, str] = {}
        for t in tokens:
            if "=" not in t:
                continue
            k, v = t.split("=", 1)
            k = k.strip().lower()
            v = v.strip()
            if k in ALLOWED_KEYS:
                updates[k] = v
        return updates
