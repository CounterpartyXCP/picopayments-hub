SELECT (id, payer_handle, payee_handle, amount, token) FROM Payment
WHERE processed AND NOT(payee_notified) AND payee_handle = :payee_handle;
