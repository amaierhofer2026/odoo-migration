update public.member_city_alliance
set communitycode
= (select communitycode from public.city_communitycode where city = public.member_city_alliance.city);