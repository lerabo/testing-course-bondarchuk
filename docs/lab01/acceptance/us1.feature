Feature: Grading and ECTS grade calculation (US-1)
  As a teacher, I want to enter a student's points for a course
  so that the system determines the ECTS grade automatically.

  Background:
    Given the teacher is logged in
    And student "Ivan Petrenko" is enrolled in the teacher's course "Software Testing"

  Scenario Outline: ECTS grade is derived from the total score
    When the teacher enters <score> points for the student
    Then the student's dashboard shows grade "<grade>"

    Examples:
      | score | grade |
      | 100   | A     |
      | 90    | A     |
      | 89    | B     |
      | 82    | B     |
      | 81    | C     |
      | 75    | C     |
      | 74    | D     |
      | 67    | D     |
      | 66    | E     |
      | 60    | E     |
      | 59    | FX    |
      | 35    | FX    |
      | 34    | F     |
      | 0     | F     |

  Scenario Outline: Score outside the allowed range or not an integer is rejected
    When the teacher enters <score> points for the student
    Then the system rejects the request with a message about the allowed range 0-100
    And the student's grade remains unchanged

    Examples:
      | score |
      | -1    |
      | 101   |
      | 50.5  |

  Scenario: Teacher corrects a grade within 14 days and the change is logged
    Given the teacher entered 58 points for the student 3 days ago
    When the teacher changes the score to 61 points
    Then the student's dashboard shows grade "E"
    And the change log contains the teacher, the time, old value 58 and new value 61

  Scenario: Teacher cannot change a grade after 14 days
    Given the teacher entered 58 points for the student 15 days ago
    When the teacher tries to change the score to 61 points
    Then the system rejects the request with a message about the correction period
    And the student's score remains 58
