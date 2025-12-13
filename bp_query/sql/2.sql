SELECT m.surname,o.data,o.real_num_people,o.real_cost FROM rk6_sheme.Order o JOIn rk6_sheme.Managers m ON m.m_id = o.m_id
WHERE o.real_cost BETWEEN %s AND %s
ORDER BY o.real_cost