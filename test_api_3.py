from app import create_app
from app.models.user import User

app = create_app('dev')
app.config['SECRET_KEY'] = 'test-secret'
with app.test_client() as client:
    with app.app_context():
        u = User.query.first()
    if u:
        with client.session_transaction() as sess:
            sess["_user_id"] = str(u.id)
        r = client.get("/settings")
        print("Settings GET:", r.status_code)
        
        r2 = client.get("/api/v1/widgets/game-news")
        print("Game News GET:", r2.status_code)
        if r2.status_code != 200:
             print(r2.text[:500])
    else:
        print("No user found")
