from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from app.auth.models import Base
from app.main import app, get_db

client = TestClient(app)


DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

machine_digest_file = "test_machine_digest_file.txt"


def override_get_db():
    database = TestingSessionLocal()
    yield database
    database.close()


app.dependency_overrides[get_db] = override_get_db


Base.metadata.create_all(bind=engine)


def test_generate_license():
    response = client.post("/generate_license", data={
        "company_name": "Test Company",
        "product_name": "Test Product",
        "lic_num": 999,
        "exp_time": "11-11-1111",
        "lic_file_name": "Test License"},
        files={
            "machine_digest_file": open(machine_digest_file, 'rb')
        })

    assert response.status_code == 200
    assert response.json() == {
        'status': 'success',
        'message': 'Лицензия C:/Users/f.nasibov/PycharmProjects/fastApiProject1/app/files/licenses/Test License.txt создана'
    }


def test_all_licenses():
    response = client.get(f'/all_licenses')

    assert response.status_code == 200
    assert response.json() == {
        'status': 'success',
        'all_licenses': None
    }


def test_find_license():
    id = 1
    response = client.get(f"/license/{id}")

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": None
    }


def test_delete_license():
    id = 1
    response = client.delete("/delete_license", params={"id": id})

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == id


Base.metadata.drop_all(bind=engine)
