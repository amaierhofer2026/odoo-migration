# Odoo 18 Diagnostics v2: Fixed for Odoo 18 schema
# Removed: ir_translation (doesn't exist as ORM table in Odoo 18)
# Fixed: language from res_partner via JOIN, not res_users.lang

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Odoo 18: Database Diagnostics v2" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ============================================================
# 1. Key table row counts
# ============================================================
Write-Host ""
Write-Host "[1] Key table row counts..." -ForegroundColor Yellow

$counts = docker exec odoo18-db psql -U odoo -d odoo18_test -c "
SELECT 'res_partner' as tbl, COUNT(*) FROM res_partner
UNION ALL SELECT 'res_users', COUNT(*) FROM res_users
UNION ALL SELECT 'res_groups', COUNT(*) FROM res_groups
UNION ALL SELECT 'res_company', COUNT(*) FROM res_company
UNION ALL SELECT 'res_country', COUNT(*) FROM res_country
UNION ALL SELECT 'res_country_state', COUNT(*) FROM res_country_state
UNION ALL SELECT 'sale_order', COUNT(*) FROM sale_order
UNION ALL SELECT 'sale_subscription', COUNT(*) FROM sale_subscription
UNION ALL SELECT 'helpdesk_ticket', COUNT(*) FROM helpdesk_ticket
UNION ALL SELECT 'helpdesk_ticket_team', COUNT(*) FROM helpdesk_ticket_team
UNION ALL SELECT 'helpdesk_ticket_stage', COUNT(*) FROM helpdesk_ticket_stage
UNION ALL SELECT 'helpdesk_ticket_category', COUNT(*) FROM helpdesk_ticket_category
UNION ALL SELECT 'helpdesk_ticket_channel', COUNT(*) FROM helpdesk_ticket_channel
UNION ALL SELECT 'ir_attachment', COUNT(*) FROM ir_attachment
UNION ALL SELECT 'ir_model_data', COUNT(*) FROM ir_model_data
UNION ALL SELECT 'ir_module_module', COUNT(*) FROM ir_module_module
ORDER BY tbl;
" 2>&1
Write-Host $counts

# ============================================================
# 2. Active users with language (via res_partner)
# ============================================================
Write-Host ""
Write-Host "[2] Active users (with language from partner)..." -ForegroundColor Yellow

$users = docker exec odoo18-db psql -U odoo -d odoo18_test -c "
SELECT u.id, u.login, u.active,
       COALESCE(p.lang, 'en_US') as lang,
       p.name as display_name
FROM res_users u
LEFT JOIN res_partner p ON u.partner_id = p.id
ORDER BY u.id;
" 2>&1
Write-Host $users

# ============================================================
# 3. Installed ITK & key OCA modules
# ============================================================
Write-Host ""
Write-Host "[3] Installed ITK modules..." -ForegroundColor Yellow

$modules = docker exec odoo18-db psql -U odoo -d odoo18_test -c "
SELECT name, state, latest_version
FROM ir_module_module
WHERE (name LIKE 'itk_%' OR name LIKE 'sale_subscription%' OR name = 'helpdesk')
  AND state = 'installed'
ORDER BY name;
" 2>&1
Write-Host $modules

# ============================================================
# 4. Installed modules summary (count by state)
# ============================================================
Write-Host ""
Write-Host "[4] Module summary (by state)..." -ForegroundColor Yellow

$summary = docker exec odoo18-db psql -U odoo -d odoo18_test -c "
SELECT state, COUNT(*) as count
FROM ir_module_module
GROUP BY state
ORDER BY state;
" 2>&1
Write-Host $summary

# ============================================================
# 5. Constraint & index health
# ============================================================
Write-Host ""
Write-Host "[5] Constraint health (res_country_state)..." -ForegroundColor Yellow

$con = docker exec odoo18-db psql -U odoo -d odoo18_test -c "
SELECT conname, contype,
       CASE WHEN contype = 'u' THEN 'UNIQUE'
            WHEN contype = 'p' THEN 'PRIMARY KEY'
            WHEN contype = 'f' THEN 'FOREIGN KEY'
            WHEN contype = 'c' THEN 'CHECK'
            ELSE contype::text END as type_desc
FROM pg_constraint
WHERE conrelid = 'res_country_state'::regclass
ORDER BY contype, conname;
" 2>&1
Write-Host $con

# ============================================================
# 6. Invalid indexes (should be empty)
# ============================================================
Write-Host ""
Write-Host "[6] Invalid indexes..." -ForegroundColor Yellow

$invalid = docker exec odoo18-db psql -U odoo -d odoo18_test -c "
SELECT indexrelid::regclass as index_name, indisvalid, indisready
FROM pg_index
WHERE NOT indisvalid;
" 2>&1
if ($invalid -match "0 rows") {
    Write-Host "  All indexes valid." -ForegroundColor Green
} else {
    Write-Host $invalid
}

# ============================================================
# 7. Database encoding
# ============================================================
Write-Host ""
Write-Host "[7] Database encoding..." -ForegroundColor Yellow

$encoding = docker exec odoo18-db psql -U odoo -d odoo18_test -c "
SELECT datname, encoding, pg_encoding_to_char(encoding) as encoding_name,
       datcollate, datctype
FROM pg_database
WHERE datname = 'odoo18_test';
" 2>&1
Write-Host $encoding

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Diagnostics Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
