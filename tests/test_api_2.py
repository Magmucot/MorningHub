from app import create_app
from app.models.user import User

app = create_app()
with app.test_client() as client:
    with app.app_context():
        u = User.query.first()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(u.id)
    r = client.get("/api/v1/widgets/game-news")
    print(r.status_code)
    print(r.text[:500])
