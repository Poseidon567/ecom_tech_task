
import uvicorn
from fastapi import FastAPI, Depends, File, UploadFile, status, HTTPException
from pydantic import BaseModel, field_validator
import asyncpg
from datetime import datetime, date
import csv
import io

#Модель данных для валидации входных данных
class Grade(BaseModel):
    date: str
    group_name: str
    name: str
    grade: str

    
    @field_validator('date')
    def validate_date(cls, v):
        try:
            # Проверяем формат даты DD.MM.YYYY
            datetime.strptime(v, '%d.%m.%Y')
            return v
        except ValueError:
            raise ValueError('Дата должна быть в формате DD.MM.YYYY')

    @field_validator('grade')
    def validate_grade(cls, v):
        # Проверяем, что оценка это цифра от 2 до 5
        if v not in ['2', '3', '4', '5']:
            raise ValueError('Оценка должна быть цифрой от 2 до 5')
        return v
    
    def to_db_date(self):
        """Конвертируем строку в объект datetime.date"""
        day, month, year = map(int, self.date.split('.'))
        return date(year, month, day)  # Возвращаем объект date


app = FastAPI()

#Строка подключения
DATABASE_URL = "postgresql://myuser:mypassword@192.168.1.77:5432/mydatabase"

#Соединение с базой данных
async def get_db_connection():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()

#Загрузка файла с оценками студентов через POST 
@app.post("/upload-grades", status_code = status.HTTP_201_CREATED)
async def create_item(uploaded_file: UploadFile, db: asyncpg.Connection = Depends(get_db_connection)):
    file = uploaded_file.file
    filename = uploaded_file.filename
    # Проверяем расширение файла
    if not filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Файл должен быть в формате CSV"
        )
    try:
        content = file.read()
        content_str = content.decode('utf-8')
        csv_file = io.StringIO(content_str)
        csv_reader = csv.reader(csv_file, delimiter=';')
        headers = next(csv_reader, None)
        
        students = set()
        added_rows = 0
        async with db.transaction():
            for row_num, row in enumerate(csv_reader, start=2):
                # Проверяем, что строка содержит достаточно данных
                if len(row) < 4:
                    continue
                
                date_str = row[0].strip()
                group_name = row[1].strip()
                name = row[2].strip()
                grade_str = row[3].strip()

                try:
                    # Валидируем данные с помощью Pydantic
                    grade_data = Grade(
                        date=date_str,
                        group_name=group_name,
                        name=name,
                        grade=grade_str
                    )
                    
                    db_date = grade_data.to_db_date() 
                    
                    await db.execute('''
                        INSERT INTO student_grades (date, group_name, name, grade)
                        VALUES ($1, $2, $3, $4)
                    ''', db_date, grade_data.group_name, grade_data.name, int(grade_data.grade))
                    
                    added_rows += 1
                    students.add(grade_data.name)
                except Exception as e:
                    continue
        return {"status": "ok", "records_loaded": added_rows, "students": len(students)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Ошибка обработки файла: {str(e)}"
        )
    return {"message": "ok"}
    

#Возвращает ФИО студентов, у которых оценка 2 встречается больше n раз.
@app.get("/students/more-than-{number}-twos")
async def get_more_grades(number: int, db: asyncpg.Connection = Depends(get_db_connection)):
    rows = await db.fetch('''
            SELECT name, count(grade) as twos FROM student_grades
            where grade = 2
            group by name
            having count(grade) > $1
        ''', number)
    grades = []
    for row in rows:
        grades.append({"full_name":row["name"] , "count_twos":row["twos"]})
    return grades

#Возвращает ФИО студентов, у которых оценка 2 встречается меньше n раз.
@app.get("/students/less-than-{number}-twos")
async def get_less_grades(number: int, db: asyncpg.Connection = Depends(get_db_connection)):
    rows = await db.fetch('''
            SELECT name, count(grade) as twos FROM student_grades
            where grade = 2
            group by name
            having count(grade) < $1
        ''', number)
    grades = []
    for row in rows:
        grades.append({"full_name":row["name"] , "count_twos":row["twos"]})
    return grades



if __name__ == "__main__":
    # Обратите внимание: имя файла передается как строка
    uvicorn.run("main_api:app", host="127.0.0.1", port=8000, reload=True)
