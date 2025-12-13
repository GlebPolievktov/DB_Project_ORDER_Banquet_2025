SELECT manager_id,year,month,num_order,total_cost
FROM rk6_sheme.new_Report WHERE month = (%s)
AND year = (%s);