# tests/test_endpoints.py
import unittest
from urllib.parse import urlparse
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.widget import WidgetConfig
from app.models.bookmark import Bookmark

class TestEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = create_app("dev")
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            
            # Создаем тестового пользователя
            usr = User(u_name="testuser")
            usr.set_pass("password")
            usr.ai_key = "saved_api_key"
            db.session.add(usr)
            db.session.commit()
            self.usr_id = usr.id

            # Добавляем один виджет
            w = WidgetConfig(usr_id=usr.id, w_tip="weather", is_act=True, x=0, y=0, w=3, h=3)
            db.session.add(w)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_healthz(self):
        res = self.client.get("/api/v1/healthz")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {"status": "ok"})

    def test_bookmark_validation(self):
        with self.app.app_context():
            with self.client.session_transaction() as sess:
                sess["_user_id"] = str(self.usr_id)
                sess["_fresh"] = True

            res = self.client.post("/api/v1/bookmarks", json={
                "title": "Google",
                "url": "https://google.com"
            })
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.json["success"])

            res = self.client.post("/api/v1/bookmarks", json={
                "title": "Google",
                "url": "not-a-url"
            })
            self.assertEqual(res.status_code, 400)
            self.assertIn("Неверный формат URL", res.json["error"])

    def test_lock_grid_validation(self):
        with self.app.app_context():
            with self.client.session_transaction() as sess:
                sess["_user_id"] = str(self.usr_id)
                sess["_fresh"] = True

            res = self.client.patch("/api/v1/user/lock-grid", json={
                "is_grid_locked": True
            })
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.json["is_grid_locked"])

            res = self.client.patch("/api/v1/user/lock-grid", json={
                "is_grid_locked": "false"
            })
            self.assertEqual(res.status_code, 400)
            self.assertIn("должен быть типа boolean", res.json["error"])

    def test_save_grid_coordinates(self):
        with self.app.app_context():
            with self.client.session_transaction() as sess:
                sess["_user_id"] = str(self.usr_id)
                sess["_fresh"] = True

            res = self.client.patch("/api/v1/widgets/save-grid", json={
                "items": [
                    {"widget_type": "weather", "x": 15, "y": -5, "w": 25, "h": 0}
                ]
            })
            self.assertEqual(res.status_code, 200)

            # Проверяем, что координаты были отсечены границами (x: 11, y: 0, w: 12, h: 1)
            w = WidgetConfig.query.filter_by(usr_id=self.usr_id, w_tip="weather").first()
            self.assertEqual(w.x, 11)
            self.assertEqual(w.y, 0)
            self.assertEqual(w.w, 12)
            self.assertEqual(w.h, 1)

    def test_settings_preserves_api_key(self):
        with self.app.app_context():
            with self.client.session_transaction() as sess:
                sess["_user_id"] = str(self.usr_id)
                sess["_fresh"] = True

            # Отправляем форму настроек с пустым ключом
            res = self.client.post("/settings", data={
                "weather_city": "Москва",
                "ai_api_key": "",
                "crypto_tracking": "bitcoin,ethereum",
                "currency_tracking": "USD,EUR"
            })
            self.assertEqual(res.status_code, 302)

            # Ключ не должен измениться
            usr = User.query.get(self.usr_id)
            self.assertEqual(usr.ai_key, "saved_api_key")

            # Отправляем новый ключ
            res = self.client.post("/settings", data={
                "weather_city": "Москва",
                "ai_api_key": "new_api_key",
                "crypto_tracking": "bitcoin,ethereum",
                "currency_tracking": "USD,EUR"
            })
            self.assertEqual(res.status_code, 302)

            # Ключ должен обновиться
            db.session.refresh(usr)
            self.assertEqual(usr.ai_key, "new_api_key")

    def test_settings_limits_lists(self):
        with self.app.app_context():
            with self.client.session_transaction() as sess:
                sess["_user_id"] = str(self.usr_id)
                sess["_fresh"] = True

            # Отправляем больше 10 криптовалют и валют
            res = self.client.post("/settings", data={
                "weather_city": "Москва",
                "crypto_tracking": "1,2,3,4,5,6,7,8,9,10,11,12",
                "currency_tracking": "1,2,3,4,5,6,7,8,9,10,11,12"
            })
            self.assertEqual(res.status_code, 302)

            usr = User.query.get(self.usr_id)
            self.assertEqual(usr.crypto_lst, "1,2,3,4,5,6,7,8,9,10")
            self.assertEqual(usr.val_lst, "1,2,3,4,5,6,7,8,9,10")

    def test_background_customization_settings(self):
        with self.app.app_context():
            with self.client.session_transaction() as sess:
                sess["_user_id"] = str(self.usr_id)
                sess["_fresh"] = True

            res = self.client.post("/settings", data={
                "bg_sz": "contain",
                "bg_ps": "top"
            })
            self.assertEqual(res.status_code, 302)

            usr = User.query.get(self.usr_id)
            self.assertEqual(usr.bg_sz, "contain")
            self.assertEqual(usr.bg_ps, "top")

    def test_free_layout_mode_scaling(self):
        with self.app.app_context():
            # Наш изначальный виджет: x=0, y=0, w=3, h=3
            w = WidgetConfig.query.filter_by(usr_id=self.usr_id, w_tip="weather").first()
            self.assertEqual(w.x, 0)
            self.assertEqual(w.w, 3)

            with self.client.session_transaction() as sess:
                sess["_user_id"] = str(self.usr_id)
                sess["_fresh"] = True

            # Переключаем в свободный режим
            res = self.client.post("/settings", data={
                "is_fr": "true"
            })
            self.assertEqual(res.status_code, 302)

            # Проверяем масштаб: x*10, w*10, y*5.8, h*5.8 - 0.8
            db.session.refresh(w)
            self.assertEqual(w.x, 0)
            self.assertEqual(w.w, 30)
            self.assertEqual(w.y, 0)
            self.assertEqual(w.h, 17) # 3 * 5.8 - 0.8 = 16.6 -> 17

            # Проверяем сохранение координат в свободном режиме
            res = self.client.patch("/api/v1/widgets/save-grid", json={
                "items": [
                    {"widget_type": "weather", "x": 50, "y": 80, "w": 40, "h": 25}
                ]
            })
            self.assertEqual(res.status_code, 200)
            db.session.refresh(w)
            self.assertEqual(w.x, 50)
            self.assertEqual(w.y, 80)
            self.assertEqual(w.w, 40)
            self.assertEqual(w.h, 25)

            # Переключаем обратно в сетку
            res = self.client.post("/settings", data={
                "is_fr": "false"
            })
            self.assertEqual(res.status_code, 302)

            # Проверяем обратный масштаб (деление): x//10, w//10, y/5.8, (h+0.8)/5.8
            db.session.refresh(w)
            self.assertEqual(w.x, 5) # 50 // 10
            self.assertEqual(w.y, 14) # round(80 / 5.8) = 14
            self.assertEqual(w.w, 4) # 40 // 10
            self.assertEqual(w.h, 4) # round((25 + 0.8) / 5.8) = 4

    def test_default_widgets_scaled_in_free_layout_mode(self):
        with self.app.app_context():
            # Создаем пользователя и переключаем его в свободный режим ДО вызова _prover_wid_def
            usr = User(u_name="free_user", is_fr=True)
            usr.set_pass("password")
            db.session.add(usr)
            db.session.commit()
            
            # Вызываем _prover_wid_def для этого пользователя
            from app.blueprints.dashboard import _chk_wid_def
            _chk_wid_def(usr.id)
            
            # Проверяем, что созданный виджет имеет отмасштабированные координаты (например, it_news)
            w = WidgetConfig.query.filter_by(usr_id=usr.id, w_tip="it_news").first()
            self.assertIsNotNone(w)
            self.assertEqual(w.x, 0)
            self.assertEqual(w.w, 30)
            self.assertEqual(w.y, 0)
            self.assertEqual(w.h, 34) # max(1, round(6 * 5.8 - 0.8)) = 34

if __name__ == "__main__":
    unittest.main()
