INSERT INTO `Order`
    (order_id, m_id, hall_id, data, time, avance, plan_num_people, real_num_people, real_cost, plan_cost)
VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);