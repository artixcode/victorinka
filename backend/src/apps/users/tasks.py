from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_email: str, token: str, user_nickname: str = None):
    """
    Отправить email с токеном восстановления пароля.
    """
    try:
        subject = f'🔐 Восстановление пароля - {settings.SITE_NAME}'

        # Формируем сообщение
        message = f"""
Здравствуйте{f', {user_nickname}' if user_nickname else ''}!

Вы запросили восстановление пароля для вашего аккаунта на {settings.SITE_NAME}.

Ваш токен для восстановления пароля:

{token}

Скопируйте этот токен и используйте его на странице восстановления пароля.

⚠️ ВАЖНО:
• Токен действителен в течение {settings.PASSWORD_RESET_TIMEOUT // 3600} часа(ов)
• Никому не передавайте этот токен
• Если вы не запрашивали восстановление пароля, проигнорируйте это письмо

С уважением,
Команда {settings.SITE_NAME}
        """.strip()

        # HTML версия письма
        html_message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .token-box {{ background: white; padding: 15px; border-left: 4px solid #667eea; 
                             margin: 20px 0; font-family: monospace; font-size: 16px; 
                             word-break: break-all; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; 
                           padding: 15px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">🔐 Восстановление пароля</h2>
                </div>
                <div class="content">
                    <p>Здравствуйте{f', <strong>{user_nickname}</strong>' if user_nickname else ''}!</p>
                    
                    <p>Вы запросили восстановление пароля для вашего аккаунта на 
                       <strong>{settings.SITE_NAME}</strong>.</p>
                    
                    <p>Ваш токен для восстановления пароля:</p>
                    
                    <div class="token-box">
                        <strong>{token}</strong>
                    </div>
                    
                    <p>Скопируйте этот токен и используйте его на странице восстановления пароля.</p>
                    
                    <div class="warning">
                        <strong>⚠️ ВАЖНО:</strong>
                        <ul>
                            <li>Токен действителен в течение {settings.PASSWORD_RESET_TIMEOUT // 3600} часа(ов)</li>
                            <li>Никому не передавайте этот токен</li>
                            <li>Если вы не запрашивали восстановление пароля, проигнорируйте это письмо</li>
                        </ul>
                    </div>
                    
                    <div class="footer">
                        <p>С уважением,<br>
                        Команда {settings.SITE_NAME}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # Отправляем email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"📧 Email с токеном восстановления отправлен на {user_email}")
        return {
            'status': 'success',
            'email': user_email,
            'message': 'Email успешно отправлен'
        }

    except Exception as e:
        logger.error(f"❌ Ошибка отправки email на {user_email}: {e}")

        try:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error(f"❌ Превышено максимальное количество попыток отправки email на {user_email}")
            return {
                'status': 'failed',
                'email': user_email,
                'error': str(e)
            }


@shared_task
def send_welcome_email(user_email: str, user_nickname: str):
    """
    Отправить приветственное письмо новому пользователю.
    """
    try:
        subject = f'🎉 Добро пожаловать в {settings.SITE_NAME}!'

        message = f"""
Здравствуйте, {user_nickname}!

Добро пожаловать в {settings.SITE_NAME} - платформу для проведения интерактивных викторин!

Теперь вы можете:
• Создавать собственные викторины
• Участвовать в играх с друзьями
• Соревноваться в таблице лидеров
• Отслеживать свой прогресс

Начните с создания своей первой викторины или присоединитесь к игре по коду приглашения!

Войти в систему: {settings.FRONTEND_URL}/login

С уважением,
Команда {settings.SITE_NAME}
        """.strip()

        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .greeting {{
                    font-size: 18px;
                    color: #667eea;
                    margin-bottom: 20px;
                }}
                .features {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .feature-item {{
                    padding: 10px 0;
                    border-left: 3px solid #667eea;
                    padding-left: 15px;
                    margin: 10px 0;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px 40px;
                    text-decoration: none;
                    border-radius: 25px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 Добро пожаловать!</h1>
            </div>
            <div class="content">
                <p class="greeting">Здравствуйте, <strong>{user_nickname}</strong>!</p>
                
                <p>Спасибо за регистрацию в <strong>{settings.SITE_NAME}</strong> - платформе для проведения интерактивных викторин!</p>
                
                <div class="features">
                    <h3 style="color: #667eea; margin-top: 0;">Теперь вы можете:</h3>
                    <div class="feature-item">✨ Создавать собственные викторины</div>
                    <div class="feature-item">🎮 Участвовать в играх с друзьями в реальном времени</div>
                    <div class="feature-item">🏆 Соревноваться в таблице лидеров</div>
                    <div class="feature-item">📊 Отслеживать свой прогресс и статистику</div>
                </div>
                
                <p>Начните с создания своей первой викторины или присоединитесь к игре по коду приглашения!</p>
                
                <div style="text-align: center;">
                    <a href="{settings.FRONTEND_URL}/login" class="button">Войти в систему</a>
                </div>
                
                <div class="footer">
                    <p>С уважением,<br>Команда {settings.SITE_NAME}</p>
                    <p style="font-size: 12px; color: #999;">
                        Если вы не регистрировались на нашей платформе, просто проигнорируйте это письмо.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
            html_message=html_message,
        )

        logger.info(f"📧 Приветственное письмо отправлено на {user_email}")

        return {
            'status': 'success',
            'email': user_email,
            'nickname': user_nickname
        }

    except Exception as e:
        logger.error(f"❌ Ошибка отправки приветственного письма на {user_email}: {e}")
        return {
            'status': 'error',
            'email': user_email,
            'error': str(e)
        }

