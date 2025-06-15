"""
Module de gestion des retries et des timeouts.
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Optional, Type, Union
import logging

logger = logging.getLogger(__name__)

class RetryError(Exception):
    """Exception levée après échec de toutes les tentatives."""
    pass

def async_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
    timeout: Optional[float] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable:
    """
    Décorateur pour gérer les retries asynchrones avec timeout.
    
    Args:
        max_retries (int): Nombre maximum de tentatives
        delay (float): Délai initial entre les tentatives en secondes
        backoff (float): Facteur de multiplication du délai
        exceptions (Union[Type[Exception], tuple[Type[Exception], ...]]): 
            Exception(s) à capturer
        timeout (Optional[float]): Timeout global en secondes
        on_retry (Optional[Callable[[Exception, int], None]]): 
            Callback appelé à chaque retry
    
    Returns:
        Callable: Fonction décorée
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    if timeout is not None:
                        return await asyncio.wait_for(
                            func(*args, **kwargs),
                            timeout=timeout
                        )
                    return await func(*args, **kwargs)
                    
                except asyncio.TimeoutError as e:
                    last_exception = e
                    logger.warning(
                        f"Timeout après {timeout}s (tentative {attempt + 1}/{max_retries + 1})"
                    )
                    
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if on_retry:
                            on_retry(e, attempt)
                            
                        logger.warning(
                            f"Erreur: {str(e)} (tentative {attempt + 1}/{max_retries + 1})"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"Échec après {max_retries + 1} tentatives: {str(e)}"
                        )
                        raise RetryError(f"Échec après {max_retries + 1} tentatives") from e
                        
            if last_exception:
                raise RetryError(f"Timeout après {max_retries + 1} tentatives") from last_exception
                
        return wrapper
    return decorator

class TimeoutContext:
    """Contexte de gestion des timeouts."""
    
    def __init__(self, timeout: float):
        """
        Initialise le contexte de timeout.
        
        Args:
            timeout (float): Durée du timeout en secondes
        """
        self.timeout = timeout
        self.start_time = time.time()
        
    def remaining(self) -> float:
        """
        Calcule le temps restant.
        
        Returns:
            float: Temps restant en secondes
        """
        elapsed = time.time() - self.start_time
        return max(0, self.timeout - elapsed)
        
    def check(self) -> None:
        """
        Vérifie si le timeout est dépassé.
        
        Raises:
            asyncio.TimeoutError: Si le timeout est dépassé
        """
        if self.remaining() <= 0:
            raise asyncio.TimeoutError("Timeout dépassé")
            
    async def sleep(self, duration: float) -> None:
        """
        Attend avec vérification du timeout.
        
        Args:
            duration (float): Durée d'attente en secondes
            
        Raises:
            asyncio.TimeoutError: Si le timeout est dépassé pendant l'attente
        """
        if duration > self.remaining():
            raise asyncio.TimeoutError("Timeout dépassé")
        await asyncio.sleep(duration)

def with_timeout(timeout: float) -> Callable:
    """
    Décorateur pour ajouter un timeout à une fonction.
    
    Args:
        timeout (float): Durée du timeout en secondes
        
    Returns:
        Callable: Fonction décorée
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=timeout
            )
        return wrapper
    return decorator 