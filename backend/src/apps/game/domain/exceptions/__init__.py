class DomainException(Exception):
    """Базовое исключение для доменного слоя"""
    pass


class InvalidScoreException(DomainException):
    """Исключение при невалидных очках"""
    pass


class GameRuleViolationException(DomainException):
    """Исключение при нарушении игровых правил"""
    pass

