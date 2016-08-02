SELECT sum(amount) AS 'sum' FROM Payment 
WHERE payer_handle = :handle GROUP BY payer_handle;
