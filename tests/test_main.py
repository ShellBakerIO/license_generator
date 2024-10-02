import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
machine_digest_file = "test_machine_digest_file.txt"


def test_main():
    access_token = ""

    def get_all_licenses():
        response = client.get('/all_licenses')
        data = response.json()
        return data["all_licenses"]

    def test_login():
        response = client.post("/token", data={"username": "f.nasibov", "password": f"{os.environ['LDAP_PASSWORD']}"})

        assert response.status_code == 200
        access_token = response.json()["access_token"]
        assert "access_token" in response.json()

    def test_generate_license():
        response = client.post("/generate_license", data={
            "company_name": "Test Company",
            "product_name": "Test Product",
            "lic_num": 999,
            "exp_time": "11-11-1111",
            "lic_file_name": "Test License"},
            files={"machine_digest_file": open(machine_digest_file, 'rb')},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        assert response.json() == {
            'status': 'success',
            'message': 'Лицензия app/files/licenses/Test License.txt создана'
        }

    def test_all_licenses():
        response = client.get('/all_licenses', headers={"Authorization": f"Bearer {access_token}"})

        assert response.status_code == 200
        data = response.json()
        assert data == {
            'status': 'success',
            'all_licenses': data["all_licenses"]
        }

    def test_find_license():
        data = get_all_licenses()
        id = data[-1]['id']
        response = client.get(f"/license/{id}", headers={"Authorization": f"Bearer {access_token}"})

        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": data[-1],
        }

    def test_delete_license():
        data = get_all_licenses()
        id = data[-1]['id']
        license_file_name = data[-1]['lic_file_name']
        response = client.delete("/delete_license", params={"id": id}, headers={"Authorization": f"Bearer {access_token}"})

        assert response.status_code == 200, response.text
        assert response.json() == {
            'status': 'success',
            'message': f'Лицензия id-{id} name-{license_file_name} удалена',
            'license': data[-1]
        }
