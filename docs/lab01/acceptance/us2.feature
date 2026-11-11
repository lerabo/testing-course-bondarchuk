Feature: Adding a new student (US-2)
  As an administrator, I want to add a new student
  so that the student can log in and see their grades.

  Background:
    Given the administrator is logged in

  Scenario: Administrator adds a student who can then log in
    When the administrator creates a student with full name "Olena Kovalenko", email "o.kovalenko@uni.edu.ua", group "KNIT-63M" and admission year 2025
    Then the student appears in the list of group "KNIT-63M"
    And the student can log in with "o.kovalenko@uni.edu.ua"
    And the student's dashboard shows an empty list of grades

  Scenario: Email that differs only in letter case is rejected as a duplicate
    Given a student with email "o.kovalenko@uni.edu.ua" exists
    When the administrator creates a student with email "O.Kovalenko@uni.edu.ua"
    Then the system rejects the request with the message "Email is already in use"
    And no new student is created

  Scenario: Non-university email is rejected
    When the administrator creates a student with email "olena@gmail.com"
    Then the system rejects the request with a message that a university email is required
    And no new student is created

  Scenario: Teacher cannot add a student
    Given the teacher is logged in instead of the administrator
    When the teacher sends POST /api/students with valid student data
    Then the system responds with status 403
    And no new student is created
