"""Modelos de ML: árbol de decisión (Gini) + K-NN geográfico.

Ambos se entrenan offline (ver application/entrenar_modelos.py) y se
persisten con joblib en infrastructure/../artifacts/. Las clases de acá son
adaptadores finos sobre scikit-learn: la lógica de negocio (qué feature usar,
qué hacer con el resultado) vive en el caso de uso, no aquí.
"""
from pathlib import Path

import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

from src.features.recomendaciones.domain.entities import Obra, TipoKit
from src.features.recomendaciones.domain.ports import (
    ClasificadorTipoKit,
    RecomendadorZona,
)

_ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"
_ARTIFACTS_DIR.mkdir(exist_ok=True)

_PATH_ARBOL = _ARTIFACTS_DIR / "arbol_tipo_kit.joblib"
_PATH_KNN = _ARTIFACTS_DIR / "knn_zona.joblib"


def existen_artefactos() -> bool:
    """False en un contenedor recién levantado que nunca entrenó (filesystem
    efímero: cada redeploy los pierde) — usado para autoentrenar al boot."""
    return _PATH_ARBOL.exists() and _PATH_KNN.exists()


class ArbolTipoKit(ClasificadorTipoKit):
    """Clasifica una obra como 'kit' o 'rendimiento' según categoría + área.

    Usa CART con criterio Gini (sklearn.tree.DecisionTreeClassifier). En el
    sistema actual esto ya se decide con una tabla estática
    (reglas_material.py), así que hoy el árbol básicamente la re-aprende — el
    valor real aparece cuando lleguen categorías nuevas que aún no están en
    esa tabla: el árbol generaliza a partir de patrones de área/zona en vez
    de fallar a "rendimiento" por defecto.
    """

    def __init__(self, max_depth: int = 4) -> None:
        self._max_depth = max_depth
        self._modelo: DecisionTreeClassifier | None = None
        self._encoder_categoria = LabelEncoder()

    def _features(self, categoria: str, area_m2: float) -> np.ndarray:
        cat_id = self._encoder_categoria.transform([categoria])[0]
        return np.array([[cat_id, area_m2]])

    def entrenar(self, obras: list[Obra]) -> float:
        categorias = [o.categoria for o in obras]
        self._encoder_categoria.fit(categorias)
        cat_ids = self._encoder_categoria.transform(categorias)
        areas = np.array([o.area_m2 for o in obras])
        X = np.column_stack([cat_ids, areas])
        y = np.array([o.tipo_kit for o in obras])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        self._modelo = DecisionTreeClassifier(
            criterion="gini", max_depth=self._max_depth, random_state=42
        )
        self._modelo.fit(X_train, y_train)
        return float(self._modelo.score(X_test, y_test))

    def predecir(self, categoria: str, area_m2: float) -> tuple[TipoKit, float]:
        if self._modelo is None:
            self.cargar()
        if categoria not in self._encoder_categoria.classes_:
            # Categoría nunca vista: no hay nada que el árbol pueda inferir de
            # verdad — fallback explícito, no una adivinanza silenciosa.
            return "rendimiento", 0.0
        X = self._features(categoria, area_m2)
        pred = self._modelo.predict(X)[0]
        proba = self._modelo.predict_proba(X)[0]
        clase_idx = list(self._modelo.classes_).index(pred)
        return pred, float(proba[clase_idx])

    def guardar(self) -> None:
        joblib.dump({"modelo": self._modelo, "encoder": self._encoder_categoria}, _PATH_ARBOL)

    def cargar(self) -> None:
        data = joblib.load(_PATH_ARBOL)
        self._modelo = data["modelo"]
        self._encoder_categoria = data["encoder"]


class KnnZona(RecomendadorZona):
    """K-NN geográfico (haversine) filtrado por categoría.

    Se entrena UNA vez sobre todas las obras; al consultar, se pide un pool
    más grande de vecinos (k × 5) y se filtra a la misma categoría — así una
    sola estructura sirve para cualquier categoría sin reentrenar por cada una.
    """

    def __init__(self) -> None:
        self._nn: NearestNeighbors | None = None
        self._obras: list[Obra] = []

    def entrenar(self, obras: list[Obra]) -> None:
        self._obras = obras
        coords_rad = np.radians([[o.lat, o.lng] for o in obras])
        self._nn = NearestNeighbors(metric="haversine", algorithm="ball_tree")
        self._nn.fit(coords_rad)

    def vecinos_mas_cercanos(
        self, *, lat: float, lng: float, categoria: str, k: int
    ) -> list[Obra]:
        if self._nn is None:
            self.cargar()
        punto = np.radians([[lat, lng]])
        pool = min(k * 5, len(self._obras))
        _, idx = self._nn.kneighbors(punto, n_neighbors=pool)
        candidatos = [self._obras[i] for i in idx[0]]
        misma_categoria = [o for o in candidatos if o.categoria == categoria]
        return misma_categoria[:k]

    def guardar(self) -> None:
        joblib.dump({"nn": self._nn, "obras": self._obras}, _PATH_KNN)

    def cargar(self) -> None:
        data = joblib.load(_PATH_KNN)
        self._nn = data["nn"]
        self._obras = data["obras"]
