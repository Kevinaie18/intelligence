"""
Module de gestion des métriques de qualité.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Métriques de qualité pour une opération."""
    
    operation: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    retries: int = 0
    input_size: Optional[int] = None
    output_size: Optional[int] = None
    api_calls: int = 0
    api_tokens: int = 0
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    
    def complete(self, success: bool = True, error: Optional[str] = None) -> None:
        """
        Finalise les métriques.
        
        Args:
            success (bool): Succès de l'opération
            error (Optional[str]): Message d'erreur si échec
        """
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error = error
        
    def add_api_call(self, tokens: int = 0) -> None:
        """
        Ajoute un appel API aux métriques.
        
        Args:
            tokens (int): Nombre de tokens utilisés
        """
        self.api_calls += 1
        self.api_tokens += tokens
        
    def add_retry(self) -> None:
        """Incrémente le compteur de retries."""
        self.retries += 1
        
    def add_metric(self, name: str, value: float) -> None:
        """
        Ajoute une métrique personnalisée.
        
        Args:
            name (str): Nom de la métrique
            value (float): Valeur de la métrique
        """
        self.custom_metrics[name] = value
        
    def to_dict(self) -> Dict:
        """
        Convertit les métriques en dictionnaire.
        
        Returns:
            Dict: Métriques au format dictionnaire
        """
        return {
            "operation": self.operation,
            "duration": self.duration,
            "success": self.success,
            "error": self.error,
            "retries": self.retries,
            "input_size": self.input_size,
            "output_size": self.output_size,
            "api_calls": self.api_calls,
            "api_tokens": self.api_tokens,
            "custom_metrics": self.custom_metrics
        }
        
    def to_json(self) -> str:
        """
        Convertit les métriques en JSON.
        
        Returns:
            str: Métriques au format JSON
        """
        return json.dumps(self.to_dict(), indent=2)

class MetricsCollector:
    """Collecteur de métriques."""
    
    def __init__(self, metrics_dir: Path):
        """
        Initialise le collecteur.
        
        Args:
            metrics_dir (Path): Répertoire de stockage des métriques
        """
        self.metrics_dir = metrics_dir
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.current_metrics: Optional[QualityMetrics] = None
        
    def start_operation(self, operation: str) -> QualityMetrics:
        """
        Démarre une nouvelle opération.
        
        Args:
            operation (str): Nom de l'opération
            
        Returns:
            QualityMetrics: Métriques de l'opération
        """
        self.current_metrics = QualityMetrics(operation=operation)
        return self.current_metrics
        
    def save_metrics(self, metrics: QualityMetrics) -> None:
        """
        Sauvegarde les métriques.
        
        Args:
            metrics (QualityMetrics): Métriques à sauvegarder
        """
        if not metrics.end_time:
            metrics.complete()
            
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{metrics.operation}_{timestamp}.json"
        filepath = self.metrics_dir / filename
        
        try:
            with open(filepath, "w") as f:
                f.write(metrics.to_json())
            logger.info(f"Métriques sauvegardées: {filepath}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des métriques: {e}")
            
    def get_metrics_summary(self, operation: Optional[str] = None) -> Dict:
        """
        Génère un résumé des métriques.
        
        Args:
            operation (Optional[str]): Filtre par opération
            
        Returns:
            Dict: Résumé des métriques
        """
        metrics_files = self.metrics_dir.glob("*.json")
        if operation:
            metrics_files = [f for f in metrics_files if f.stem.startswith(operation)]
            
        total_operations = 0
        successful_operations = 0
        total_duration = 0
        total_retries = 0
        total_api_calls = 0
        total_api_tokens = 0
        
        for file in metrics_files:
            try:
                with open(file) as f:
                    metrics = json.load(f)
                    
                total_operations += 1
                if metrics["success"]:
                    successful_operations += 1
                    
                total_duration += metrics.get("duration", 0)
                total_retries += metrics.get("retries", 0)
                total_api_calls += metrics.get("api_calls", 0)
                total_api_tokens += metrics.get("api_tokens", 0)
                
            except Exception as e:
                logger.error(f"Erreur lors de la lecture des métriques {file}: {e}")
                
        return {
            "total_operations": total_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "average_duration": total_duration / total_operations if total_operations > 0 else 0,
            "average_retries": total_retries / total_operations if total_operations > 0 else 0,
            "total_api_calls": total_api_calls,
            "total_api_tokens": total_api_tokens
        }
        
    def cleanup_old_metrics(self, days: int = 30) -> None:
        """
        Nettoie les anciennes métriques.
        
        Args:
            days (int): Âge maximum des métriques en jours
        """
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        for file in self.metrics_dir.glob("*.json"):
            try:
                if file.stat().st_mtime < cutoff_time:
                    file.unlink()
                    logger.info(f"Métriques supprimées: {file}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression des métriques {file}: {e}") 