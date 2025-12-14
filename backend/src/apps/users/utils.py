from typing import Optional

def get_client_ip(request) -> Optional[str]:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

def get_user_agent(request) -> str:
    return request.META.get("HTTP_USER_AGENT", "")

def apply_answer_points(user, question, is_correct: bool):
    delta = question.points if is_correct else -question.points
    user.add_points(delta)
    user.save(update_fields=["total_points"])


def award_winners(users):
    users = list(users)
    if not users:
        return
    max_score = max(u.total_points for u in users)
    winners = [u for u in users if u.total_points == max_score]
    for w in winners:
        w.total_wins += 1
        w.save(update_fields=["total_wins"])
