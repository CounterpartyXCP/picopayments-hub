SELECT sum(amount) AS 'sum' FROM Payment 
WHERE payee_handle = :handle GROUP BY payee_handle;
