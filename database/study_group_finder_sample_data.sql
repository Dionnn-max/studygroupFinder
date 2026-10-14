USE study_group_finder;

INSERT INTO courses (course_code, course_name)
VALUES
    ('CS 150', 'Introductory Computer Programming'),
    ('CS 160', 'Intermediate Computer Programming'),
    ('CS 210', 'Data Structures'),
    ('CS 240', 'Computer Organization'),
    ('CS 250', 'Introduction to Software Systems'),
    ('CS 370', 'Computer Architecture'),
    ('CS 450', 'Introduction to Artificial Intelligence'),
    ('CS 460', 'Algorithms'),
    ('CS 480', 'Operating Systems'),
    ('CS 503', 'Scientific Database Techniques'),
    ('CS 514', 'Database Theory and Implementation'),
    ('MATH 150', 'Calculus I'),
    ('MATH 151', 'Calculus II'),
    ('MATH 245', 'Discrete Mathematics'),
    ('CS 420', 'Advanced Programming Languages'),
    ('CS 576', 'Computer Networks and Distributed Systems');


SELECT * FROM courses;

-- -----------------------------------------------------
-- Sample students
-- Password values are placeholders for database testing only
-- -----------------------------------------------------

INSERT INTO students
    (student_email, password_hash, first_name, last_name,
     date_of_birth, gender, major, phone_number)
VALUES
    ('alex.rivera@sdsu.edu', 'DEMO_ONLY_NOT_A_REAL_HASH',
     'Alex', 'Rivera', '2003-04-12', 'Male',
     'Computer Science', '619-555-0101'),

    ('maya.chen@sdsu.edu', 'DEMO_ONLY_NOT_A_REAL_HASH',
     'Maya', 'Chen', '2004-08-23', 'Female',
     'Computer Science', NULL),

    ('jordan.lee@sdsu.edu', 'DEMO_ONLY_NOT_A_REAL_HASH',
     'Jordan', 'Lee', '2002-11-05', 'Non-binary',
     'Mathematics', '619-555-0103'),

    ('sofia.martinez@sdsu.edu', 'DEMO_ONLY_NOT_A_REAL_HASH',
     'Sofia', 'Martinez', '2003-02-17', 'Female',
     'Computer Engineering', NULL),

    ('ethan.nguyen@sdsu.edu', 'DEMO_ONLY_NOT_A_REAL_HASH',
     'Ethan', 'Nguyen', '2004-06-30', 'Male',
     NULL, NULL);

SELECT student_id, student_email, first_name, last_name, major
FROM students;

-- -----------------------------------------------------
-- Sample enrollments
-- -----------------------------------------------------

INSERT INTO enrollments (student_id, course_id)
VALUES
    (1, 11),  -- Alex: CS 514
    (1, 9),   -- Alex: CS 480
    (1, 8),   -- Alex: CS 460

    (2, 3),   -- Maya: CS 210
    (2, 11),  -- Maya: CS 514

    (3, 14),  -- Jordan: MATH 245
    (3, 12),  -- Jordan: MATH 150
    (3, 11),  -- Jordan: CS 514

    (4, 7),   -- Sofia: CS 450
    (4, 11),  -- Sofia: CS 514

    (5, 1),   -- Ethan: CS 150
    (5, 3),   -- Ethan: CS 210
    (5, 12);  -- Ethan: MATH 150

SELECT
    students.first_name,
    students.last_name,
    courses.course_code,
    courses.course_name
FROM enrollments
JOIN students
    ON enrollments.student_id = students.student_id
JOIN courses
    ON enrollments.course_id = courses.course_id
ORDER BY students.student_id, courses.course_id;

-- -----------------------------------------------------
-- Sample study groups
-- The creator is also the initial leader
-- -----------------------------------------------------

INSERT INTO study_groups
    (course_id, creator_id, leader_id, group_name, description,
     meeting_format, meeting_location, maximum_capacity)
VALUES
    (11, 1, 1,
     'CS 514 Database Study Group',
     'Review database concepts and work through practice problems.',
     'hybrid', 'Love Library Room 201 and Zoom', 3),

    (3, 2, 2,
     'Data Structures Practice',
     'Practice trees, graphs, sorting, and other data structures.',
     'in_person', 'Love Library Room 220', 4),

    (12, 3, 3,
     'Calculus I Review',
     'Review lectures and prepare for upcoming Calculus I exams.',
     'online', 'Zoom', 4),

    (7, 4, 4,
     'Artificial Intelligence Study Group',
     'Discuss AI concepts and review course materials.',
     'online', 'Discord', 3),

    (1, 5, 5,
     'Intro Programming Help Group',
     'Practice introductory programming exercises together.',
     'in_person', 'Love Library Third Floor', 2);

SELECT
    study_groups.group_id,
    study_groups.group_name,
    courses.course_code,
    students.first_name AS creator,
    study_groups.meeting_format,
    study_groups.maximum_capacity
FROM study_groups
JOIN courses
    ON study_groups.course_id = courses.course_id
JOIN students
    ON study_groups.creator_id = students.student_id;
    
-- -----------------------------------------------------
-- Sample group members
-- Every creator is added as the group's first member
-- -----------------------------------------------------

INSERT INTO group_members (group_id, student_id)
VALUES
    (1, 1),  -- Alex created the CS 514 group
    (1, 2),  -- Maya joined
    (1, 3),  -- Jordan joined; group is now full

    (2, 2),  -- Maya created the CS 210 group
    (2, 5),  -- Ethan joined

    (3, 3),  -- Jordan created the MATH 150 group
    (3, 5),  -- Ethan joined

    (4, 4),  -- Sofia created the CS 450 group

    (5, 5);  -- Ethan created the CS 150 group

SELECT
    study_groups.group_id,
    study_groups.group_name,
    GROUP_CONCAT(
        CONCAT(students.first_name, ' ', students.last_name)
        ORDER BY students.student_id
        SEPARATOR ', '
    ) AS members,
    COUNT(group_members.student_id) AS current_members,
    study_groups.maximum_capacity,
    study_groups.maximum_capacity
        - COUNT(group_members.student_id) AS available_spots,
    CASE
        WHEN COUNT(group_members.student_id)
             >= study_groups.maximum_capacity
        THEN 'Full'
        ELSE 'Open'
    END AS group_status
FROM study_groups
LEFT JOIN group_members
    ON study_groups.group_id = group_members.group_id
LEFT JOIN students
    ON group_members.student_id = students.student_id
GROUP BY
    study_groups.group_id,
    study_groups.group_name,
    study_groups.maximum_capacity
ORDER BY study_groups.group_id;    

-- -----------------------------------------------------
-- Sample group meeting times
-- A group may have multiple recurring meeting times
-- -----------------------------------------------------

INSERT INTO group_meeting_times
    (group_id, day_of_week, start_time, end_time)
VALUES
    (1, 'monday',    '17:00:00', '18:30:00'),
    (1, 'wednesday', '17:00:00', '18:30:00'),

    (2, 'tuesday',   '14:00:00', '15:00:00'),

    (3, 'saturday',  '10:00:00', '11:30:00'),

    (4, 'thursday',  '18:00:00', '19:00:00'),

    (5, 'friday',    '13:00:00', '14:00:00');

SELECT
    study_groups.group_name,
    group_meeting_times.day_of_week,
    group_meeting_times.start_time,
    group_meeting_times.end_time
FROM group_meeting_times
JOIN study_groups
    ON group_meeting_times.group_id = study_groups.group_id
ORDER BY
    group_meeting_times.group_id,
    FIELD(
        group_meeting_times.day_of_week,
        'monday',
        'tuesday',
        'wednesday',
        'thursday',
        'friday',
        'saturday',
        'sunday'
    ),
    group_meeting_times.start_time;
    
-- -----------------------------------------------------
-- Final sample-data verification
-- -----------------------------------------------------

SELECT 'courses' AS table_name, COUNT(*) AS row_count
FROM courses

UNION ALL

SELECT 'students', COUNT(*)
FROM students

UNION ALL

SELECT 'enrollments', COUNT(*)
FROM enrollments

UNION ALL

SELECT 'study_groups', COUNT(*)
FROM study_groups

UNION ALL

SELECT 'group_members', COUNT(*)
FROM group_members

UNION ALL

SELECT 'group_meeting_times', COUNT(*)
FROM group_meeting_times;
