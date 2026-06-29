select * from sale_subscription_line where product_id::text = name

update sale_subscription_line set name = (select name from public.product_template where id = sale_subscription_line.product_id) where name = product_id::text
