Feature: Viewing own grades (US-3)
  As a student, I want to view my grades
  so that I know my current progress.

  Background:
    Given student "Ivan Petrenko" has 92 points in "Software Testing" and 58 points in "Databases"

  Scenario: Student sees own grades with ECTS letters
    Given "Ivan Petrenko" is logged in
    When he opens his dashboard
    Then he sees "Software Testing" with 92 points and grade "A"
    And he sees "Databases" with 58 points and grade "FX"

  Scenario: Student cannot view another student's grades
    Given "Ivan Petrenko" is logged in
    And student "Olena Kovalenko" from the same group exists
    When he sends GET /api/students/{Olena's id}/grades
    Then the system responds with status 403
    And the response contains no grades of "Olena Kovalenko"

  Scenario: Anonymous user is redirected to the login page
    Given nobody is logged in
    When the user opens the dashboard page
    Then the user is redirected to the login page

  Scenario: Account is locked after three failed login attempts
    Given "Ivan Petrenko" entered a wrong password 3 times within 15 minutes
    When he enters the correct password
    Then the system refuses to log him in with a message that the account is locked for 15 minutes
