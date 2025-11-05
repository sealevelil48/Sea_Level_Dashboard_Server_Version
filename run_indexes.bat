@echo off
echo Running database performance indexes...
psql -U SeaLevel -d T -f backend\migrations\add_performance_indexes.sql
echo Indexes created successfully!
pause