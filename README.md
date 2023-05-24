# gmailapi
happyfox_backend_assignment

Problem Statement:
Write a standalone Python script that integrates with GMail API and performs some rule based
operations on emails.
Task Details & Breakdown:
- This project is meant to be a standalone Python script, not a web server project. Use any
3rd party libraries you need for the assignment
- Authenticate to Google’s GMail API using OAuth (use Google’s official Python client) and
fetch a list of emails from your Inbox. Do NOT use IMAP.
- Come up a database table representation and store these emails there. Use any
relational database for this (Postgres / MySQL / SQLite3).
- Now that you can fetch emails, write another script that can process emails (in Python
code, not using Gmail’s Search) based on some rules and take some actions on them
using the REST API.
- These rules can be stored in a JSON file. The file should have a list of rules. Each rule
has a set of conditions with an overall predicate and a set of actions.
Example: Taken from Apple Mail app.

Requirements for Rules:
Each rule has 3 properties:
- Field name (From / To / Subject / Date Received / etc)
- Predicate ( contains / not equals / less than )
- Value
A collection of Rules has one of 2 predicates - “All” or “Any”
- “All” indicates that all the given conditions must match in order to run the actions.
- “Any” indicates that at least one of the conditions must match in order to run the
conditions.
Implement the following set: (Similar to the screenshot)
Fields: From, Subject, Message, Received Date/Time
Predicate:
- For string type fields - Contains, Does not Contain, Equals, Does not equal
- For date type field (Received) - Less than / Greater than for days / months.
Actions:
- Mark as read / mark as unread
- Move Message
