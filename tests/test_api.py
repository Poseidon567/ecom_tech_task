import pytest
import io

#Параметризированный тест аналитической первой ручки API,
# которая возвращает ФИО студентов, у которых оценка 2 встречается больше n раз.
@pytest.mark.parametrize("number, status",[
    (2, 200),
    (-1, 200),
    ("string", 422)
])
def test_get_grades_more(client, number, status):
    response = client.get(f"/students/more-than-{number}-twos")
    assert response.status_code == status

#Параметризированный тест аналитической первой ручки API,
# которая возвращает ФИО студентов, у которых оценка 2 встречается меньше n раз.
@pytest.mark.parametrize("number, status",[
    (2, 200),
    (-1, 200),
    ("string", 422)
])
def test_get_grades_less(client, number, status):
    response = client.get(f"/students/less-than-{number}-twos")
    assert response.status_code == status
    
#Параметризированный тест загрузки файла с оценками студентов
@pytest.mark.parametrize("content, rows, students" , [
    ("Дата;Номер группы;ФИО;Оценка\n11.03.2025;101Б;Курочкин Антон Влк;4\n18.09.2024;102Б;Москвичев Андрей;4", 2, 2),
    ("Дата;Номер группы;ФИО;Оценка\n11.03.2025;101Б;Курочкин Антон Влк;4\n18.09.2024;102Б;Москвичев Андрей;fg", 1, 1)
    ])
def test_upload_grades(client, content, rows, students):
    csv_bytes = content.encode('utf-8')
    files = {
        'uploaded_file': ('grades.csv', io.BytesIO(csv_bytes), 'text/csv')
    }
    
    response = client.post("/upload-grades", files=files)
    
    assert response.status_code == 201
    data = response.json()
    assert data["records_loaded"] == rows
    assert  data["students"] == students
    

