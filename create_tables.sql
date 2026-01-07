

CREATE TABLE student_grades (
	id SERIAL primary key,
	"date" date NOT NULL,
	group_name text NOT NULL,
	"name" text NOT NULL,
	grade int4 NOT NULL
);