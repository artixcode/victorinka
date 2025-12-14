from rest_framework import permissions


class IsRoomHost(permissions.BasePermission):
    """
    Разрешение: только хост комнаты может выполнять действие
    """

    message = "Только хост комнаты может выполнить это действие"

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'host'):
            return obj.host == request.user
        elif hasattr(obj, 'room'):
            return obj.room.host == request.user
        return False


class IsGameParticipant(permissions.BasePermission):
    """
    Разрешение: только участник игры может выполнять действие
    """

    message = "Только участники игры могут выполнить это действие"

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'room'):
            room = obj.room
        elif hasattr(obj, 'session'):
            room = obj.session.room
        else:
            return False

        # Проверяем, что пользователь в списке участников комнаты
        return room.participants.filter(user=request.user).exists()


class CanAnswerQuestion(permissions.BasePermission):
    """
    Разрешение: пользователь может ответить на вопрос
    """

    message = "Невозможно ответить на этот вопрос"

    def has_object_permission(self, request, view, obj):
        """
        Проверяем условия для ответа на вопрос:
        1. Раунд активен
        2. Пользователь - участник игры
        3. Пользователь еще не ответил на этот вопрос
        """
        if obj.status != obj.Status.ACTIVE:
            self.message = "Раунд не активен"
            return False

        if not obj.session.room.participants.filter(user=request.user).exists():
            self.message = "Вы не являетесь участником этой игры"
            return False

        if obj.answers.filter(user=request.user).exists():
            self.message = "Вы уже ответили на этот вопрос"
            return False

        return True

