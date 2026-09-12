-- Run as a MySQL administrator and replace the sample password first.
CREATE USER IF NOT EXISTS 'data_agent_ro'@'%' IDENTIFIED BY 'CHANGE_THIS_PASSWORD';
ALTER USER 'data_agent_ro'@'%' IDENTIFIED BY 'CHANGE_THIS_PASSWORD';
GRANT SELECT ON dw.* TO 'data_agent_ro'@'%';
FLUSH PRIVILEGES;
